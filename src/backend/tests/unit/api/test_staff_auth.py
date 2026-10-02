from __future__ import annotations

import base64
import hashlib
import hmac
import struct
import time
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from app import create_app
from app.extensions import db
from app.staff_auth.models import (
    StaffCase, StaffMfaFactor, StaffRoleGrant, StaffSession, StaffUser, Tenant,
)
from app.staff_auth.security import (
    CSRF_COOKIE, SESSION_COOKIE, digest, encrypt_totp_secret, hash_password,
)


_TEST_PASSWORD = f"Test-{secrets.token_urlsafe(18)}-A9!"
_NEW_TEST_PASSWORD = f"Changed-{secrets.token_urlsafe(18)}-B7!"


def _totp(secret: str, at: int | None = None) -> str:
    counter = int((time.time() if at is None else at) // 30)
    key = base64.b32decode(secret + "=" * (-len(secret) % 8))
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{value:06d}"


def _new_app():
    app = create_app("testing")
    app.config.update(RATELIMIT_ENABLED=False)
    return app


def _seed_user(app, *, tenant_slug="district-a", email="officer@example.gov", role="CASE_OFFICER", secret="JBSWY3DPEHPK3PXP"):
    with app.app_context():
        tenant = Tenant(id=str(uuid.uuid4()), slug=tenant_slug, display_name=tenant_slug.title())
        db.session.add(tenant)
        db.session.flush()
        user = StaffUser(
            tenant_id=tenant.id,
            email=email,
            display_name="Test Officer",
            password_hash=hash_password(_TEST_PASSWORD),
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(StaffRoleGrant(tenant_id=tenant.id, user_id=user.id, role=role))
        db.session.add(StaffMfaFactor(
            tenant_id=tenant.id, user_id=user.id,
            secret_ciphertext=encrypt_totp_secret(secret), active=True,
        ))
        db.session.commit()
        return tenant.id, user.id


def _login(client, slug="district-a", email="officer@example.gov", password=_TEST_PASSWORD):
    response = client.post("/api/v1/staff/auth/login", json={
        "tenant_slug": slug, "email": email, "password": password,
    })
    assert response.status_code == 200
    assert response.json["mfa_required"] is True
    return response.json["challenge"]


def _complete_mfa(client, challenge, secret="JBSWY3DPEHPK3PXP", at=None):
    return client.post("/api/v1/staff/auth/mfa", json={"challenge": challenge, "code": _totp(secret, at)})


def test_mfa_enrollment_confirm_and_one_time_login_challenge():
    app = _new_app()
    tenant_id, user_id = _seed_user(app)
    client = app.test_client()

    challenge = _login(client)
    accepted = _complete_mfa(client, challenge)
    assert accepted.status_code == 200
    assert accepted.json["mfa_verified"] is True
    assert client.get_cookie(SESSION_COOKIE) is not None
    csrf = client.get_cookie(CSRF_COOKIE).value

    assert client.get("/api/v1/staff/auth/me").status_code == 200
    denied = client.post("/api/v1/staff/cases", json={"case_type": "WATER"})
    assert denied.status_code == 403
    created = client.post(
        "/api/v1/staff/cases",
        json={"case_type": "WATER", "priority": "HIGH", "description": "ignored"},
        headers={"X-CSRF-Token": csrf},
    )
    assert created.status_code == 201
    assert created.json["case"]["title"] == "Water service case"
    case_id = created.json["case"]["id"]
    changed = client.post(
        f"/api/v1/staff/cases/{case_id}/status",
        json={"status": "UNDER_REVIEW"},
        headers={"X-CSRF-Token": csrf},
    )
    assert changed.status_code == 200
    assert changed.json["case"]["status"] == "UNDER_REVIEW"

    replayed = _complete_mfa(client, challenge)
    assert replayed.status_code == 401
    with app.app_context():
        assert StaffCase.query.filter_by(tenant_id=tenant_id).count() == 1
        assert StaffSession.query.count() == 1
        assert StaffUser.query.filter_by(id=user_id).one().active is True


def test_mfa_replay_csrf_and_tenant_isolation():
    app = _new_app()
    first_tenant, _ = _seed_user(app)
    second_tenant, second_user = _seed_user(
        app, tenant_slug="district-b", email="other@example.gov", role="CASE_OFFICER",
        secret="KRSXG5DSNFXGOIDB",
    )
    with app.app_context():
        other_case = StaffCase(
            tenant_id=second_tenant, case_ref="C-OTHER", case_type="WATER",
            title="Water service case", status="OPEN", priority="NORMAL",
            created_by=second_user,
        )
        db.session.add(other_case)
        db.session.commit()
        other_case_id = other_case.id

    client = app.test_client()
    challenge = _login(client)
    fixed = int(time.time())
    accepted = _complete_mfa(client, challenge, at=fixed)
    assert accepted.status_code == 200
    no_csrf = client.post("/api/v1/staff/cases", json={"case_type": "WATER"})
    assert no_csrf.status_code == 403
    csrf = client.get_cookie(CSRF_COOKIE).value
    cross_tenant = client.get(f"/api/v1/staff/cases/{other_case_id}")
    assert cross_tenant.status_code == 404
    listed = client.get("/api/v1/staff/cases")
    assert listed.status_code == 200
    assert listed.json["cases"] == []
    assert first_tenant != second_tenant

    next_challenge = _login(client)
    reused_code = client.post("/api/v1/staff/auth/mfa", json={"challenge": next_challenge, "code": _totp("JBSWY3DPEHPK3PXP", fixed)})
    assert reused_code.status_code == 401


def test_invalid_role_and_login_lockout():
    app = _new_app()
    _seed_user(app, role="AUDITOR")
    client = app.test_client()
    for _ in range(5):
        response = client.post("/api/v1/staff/auth/login", json={
            "tenant_slug": "district-a", "email": "officer@example.gov", "new_password": _TEST_PASSWORD,
        })
        assert response.status_code == 401
    locked = client.post("/api/v1/staff/auth/login", json={
        "tenant_slug": "district-a", "email": "officer@example.gov", "new_password": _TEST_PASSWORD,
    })
    assert locked.status_code == 401
    with app.app_context():
        user = StaffUser.query.filter_by(email="officer@example.gov").one()
        user.failed_login_count = 0
        user.locked_until = None
        db.session.commit()
    challenge = _login(client)
    assert _complete_mfa(client, challenge).status_code == 200
    denied = client.post(
        "/api/v1/staff/cases",
        json={"case_type": "WATER"},
        headers={"X-CSRF-Token": client.get_cookie(CSRF_COOKIE).value},
    )
    assert denied.status_code == 403


def test_mfa_enrollment_is_token_bound_and_session_expires():
    app = _new_app()
    tenant_id, user_id = _seed_user(app)
    enrollment_token = "operator-delivered-once-token"
    with app.app_context():
        factor = StaffMfaFactor.query.filter_by(tenant_id=tenant_id, user_id=user_id).one()
        factor.active = False
        factor.enrollment_token_hash = digest(enrollment_token)
        factor.enrollment_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.commit()
    client = app.test_client()
    confirmed = client.post("/api/v1/staff/auth/mfa/enroll/confirm", json={
        "tenant_slug": "district-a", "enrollment_token": enrollment_token,
        "code": _totp("JBSWY3DPEHPK3PXP"),
    })
    assert confirmed.status_code == 200
    reused = client.post("/api/v1/staff/auth/mfa/enroll/confirm", json={
        "tenant_slug": "district-a", "enrollment_token": enrollment_token,
        "code": _totp("JBSWY3DPEHPK3PXP"),
    })
    assert reused.status_code == 401

    challenge = _login(client)
    next_totp_step = int(time.time() // 30 * 30 + 30)
    assert _complete_mfa(client, challenge, at=next_totp_step).status_code == 200
    raw_cookie = client.get_cookie(SESSION_COOKIE).value
    with app.app_context():
        session_row = StaffSession.query.filter_by(session_hash=digest(raw_cookie)).one()
        session_row.idle_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.session.commit()
    assert client.get("/api/v1/staff/auth/me").status_code == 401


def test_staff_password_change_revokes_all_sessions():
    app = _new_app()
    _, user_id = _seed_user(app)
    client = app.test_client()
    challenge = _login(client)
    assert _complete_mfa(client, challenge).status_code == 200
    response = client.post("/api/v1/staff/auth/password/change", json={
        "current_password": _TEST_PASSWORD,
        "new_password": _NEW_TEST_PASSWORD,
    }, headers={"X-CSRF-Token": client.get_cookie(CSRF_COOKIE).value})
    assert response.status_code == 200
    assert response.json["login_required"] is True
    assert client.get("/api/v1/staff/auth/me").status_code == 401
    with app.app_context():
        user = StaffUser.query.filter_by(id=user_id).one()
        assert user.password_changed_at is not None
        assert StaffSession.query.filter_by(user_id=user_id, revoked_at=None).count() == 0


def test_totp_failures_lock_the_factor_even_with_new_challenges():
    app = _new_app()
    _seed_user(app)
    client = app.test_client()
    correct_code = _totp("JBSWY3DPEHPK3PXP")
    wrong_code = "999999" if correct_code != "999999" else "000000"
    for _ in range(5):
        challenge = _login(client)
        response = client.post("/api/v1/staff/auth/mfa", json={"challenge": challenge, "code": wrong_code})
        assert response.status_code == 401
    locked_challenge = _login(client)
    locked = client.post("/api/v1/staff/auth/mfa", json={"challenge": locked_challenge, "code": _totp("JBSWY3DPEHPK3PXP")})
    assert locked.status_code == 401
