from __future__ import annotations

import base64
import hashlib
import hmac
import struct
import time
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO
from urllib.parse import parse_qs, urlsplit

from app import create_app
from app.extensions import db
from app.staff_auth.models import (
    EvidenceObject, StaffAuditEvent, StaffCase, StaffMfaFactor, StaffRoleGrant,
    StaffSession, StaffUser, Tenant,
)
from app.staff_auth.security import (
    CSRF_COOKIE, SESSION_COOKIE, digest, encrypt_totp_secret, hash_password,
)
from app.evidence_vault.storage import LocalPrivateStore


_TEST_PASSWORD = f"Test-{secrets.token_urlsafe(18)}-A9!"
_NEW_TEST_PASSWORD = f"Changed-{secrets.token_urlsafe(18)}-B7!"
_EVIDENCE_PDF = b"%PDF-1.7\ncase evidence\n%%EOF"


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


class CleanEvidenceScanner:
    def scan(self, path):
        with open(path, "rb") as evidence_file:
            assert evidence_file.read().startswith(b"%PDF-")
        return "clamav-test/1"


def _enable_evidence_vault(app, root):
    app.config.update(
        EVIDENCE_VAULT_ENABLED=True,
        EVIDENCE_DEFAULT_RETENTION_DAYS=30,
        EVIDENCE_RETENTION_POLICY_ID="test-authority-policy-v1",
    )
    app.extensions["scmirn_evidence_store"] = LocalPrivateStore(root)
    app.extensions["scmirn_evidence_scanner"] = CleanEvidenceScanner()


def _case_for_staff(client):
    csrf = client.get_cookie(CSRF_COOKIE).value
    response = client.post(
        "/api/v1/staff/cases", json={"case_type": "WATER"},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 201
    return response.json["case"]["id"], csrf


def _authenticated_client(app, *, slug="district-a", email="officer@example.gov", secret="JBSWY3DPEHPK3PXP"):
    client = app.test_client()
    challenge = _login(client, slug=slug, email=email)
    response = _complete_mfa(client, challenge, secret=secret)
    assert response.status_code == 200
    return client


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


def test_case_officer_scope_is_limited_to_owned_or_assigned_cases():
    app = _new_app()
    tenant_id, actor_id = _seed_user(app)
    with app.app_context():
        other_user = StaffUser(
            tenant_id=tenant_id,
            email="colleague@example.gov",
            display_name="Other Officer",
            password_hash=hash_password(_TEST_PASSWORD),
        )
        db.session.add(other_user)
        db.session.flush()
        own_case = StaffCase(
            tenant_id=tenant_id, case_ref="C-OWN", case_type="WATER",
            title="Own case", status="OPEN", priority="NORMAL", created_by=actor_id,
        )
        assigned_case = StaffCase(
            tenant_id=tenant_id, case_ref="C-ASSIGNED", case_type="ROADS",
            title="Assigned case", status="OPEN", priority="NORMAL",
            created_by=other_user.id, assigned_user_id=actor_id,
        )
        unrelated_case = StaffCase(
            tenant_id=tenant_id, case_ref="C-OTHER", case_type="WASTE",
            title="Unrelated case", status="OPEN", priority="NORMAL", created_by=other_user.id,
            assigned_user_id=other_user.id,
        )
        db.session.add_all([own_case, assigned_case, unrelated_case])
        db.session.commit()
        unrelated_case_id = unrelated_case.id

    client = app.test_client()
    challenge = _login(client)
    assert _complete_mfa(client, challenge).status_code == 200
    listed = client.get("/api/v1/staff/cases")
    assert listed.status_code == 200
    listed_refs = {case["case_ref"] for case in listed.json["cases"]}
    assert listed_refs == {"C-OWN", "C-ASSIGNED"}

    hidden = client.get(f"/api/v1/staff/cases/{unrelated_case_id}")
    assert hidden.status_code == 404
    denied_mutation = client.post(
        f"/api/v1/staff/cases/{unrelated_case_id}/status",
        json={"status": "CLOSED"},
        headers={"X-CSRF-Token": client.get_cookie(CSRF_COOKIE).value},
    )
    assert denied_mutation.status_code == 404


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


def test_assigned_officer_uploads_scanned_evidence_and_retrieves_short_lived_url(tmp_path):
    from itsdangerous import URLSafeTimedSerializer

    app = _new_app()
    _enable_evidence_vault(app, tmp_path / "private")
    tenant_id, user_id = _seed_user(app)
    client = _authenticated_client(app)
    case_id, csrf = _case_for_staff(client)

    uploaded = client.post(
        f"/api/v1/staff/cases/{case_id}/evidence",
        data={"file": (BytesIO(_EVIDENCE_PDF), "citizen-evidence.pdf")},
        headers={"X-CSRF-Token": csrf}, content_type="multipart/form-data",
    )
    assert uploaded.status_code == 201
    metadata = uploaded.json["evidence"]
    assert metadata["scan_status"] == "CLEAN"
    assert metadata["checksum_sha256"] == hashlib.sha256(_EVIDENCE_PDF).hexdigest()
    assert "object_key" not in metadata
    assert "citizen-evidence.pdf" not in str(uploaded.json)

    with app.app_context():
        evidence = EvidenceObject.query.filter_by(tenant_id=tenant_id, case_id=case_id).one()
        evidence_id, object_key = evidence.id, evidence.object_key
        assert evidence.created_by == user_id
    assert client.get(f"/uploads/{object_key}").status_code == 404
    local_store = app.extensions["scmirn_evidence_store"]

    class RemotePrivateStore:
        def open(self, key):
            assert key == object_key
            return BytesIO(_EVIDENCE_PDF)

    # Remote-store downloads still pass through the signed, reauthorizing API.
    app.extensions["scmirn_evidence_store"] = RemotePrivateStore()
    retrieval = client.get(f"/api/v1/staff/evidence/{evidence_id}/retrieval")
    assert retrieval.status_code == 200
    parsed = urlsplit(retrieval.json["url"])
    assert parsed.path == f"/api/v1/staff/evidence/{evidence_id}/content"
    assert "ticket=" in parsed.query
    assert 1 <= retrieval.json["expires_in"] <= 300
    claims = URLSafeTimedSerializer(
        app.config["SECRET_KEY"], salt="scmirn-evidence-retrieval-v1",
    ).loads(parse_qs(parsed.query)["ticket"][0])
    assert claims["evidence_id"] == evidence_id
    assert claims["tenant_id"] == tenant_id
    assert claims["case_id"] == case_id
    assert claims["user_id"] == user_id
    assert claims["session_hash"] == digest(client.get_cookie(SESSION_COOKIE).value)
    assert client.get(retrieval.json["url"].replace("ticket=", "ticket=invalid", 1)).status_code == 404
    other_session = app.test_client()
    alternate_token, alternate_csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    with app.app_context():
        db.session.add(StaffSession(
            session_hash=digest(alternate_token),
            tenant_id=tenant_id,
            user_id=user_id,
            csrf_hash=digest(alternate_csrf),
            mfa_verified_at=now,
            created_at=now,
            last_seen_at=now,
            idle_expires_at=now + timedelta(minutes=30),
            absolute_expires_at=now + timedelta(hours=12),
        ))
        db.session.commit()
    other_session.set_cookie(SESSION_COOKIE, alternate_token)
    other_session.set_cookie(CSRF_COOKIE, alternate_csrf)
    assert other_session.get(retrieval.json["url"]).status_code == 404
    expired_ticket = URLSafeTimedSerializer(
        app.config["SECRET_KEY"], salt="scmirn-evidence-retrieval-v1",
    ).dumps({
        "key": object_key,
        "evidence_id": evidence_id,
        "tenant_id": tenant_id,
        "case_id": case_id,
        "user_id": user_id,
        "expires_at": 0,
    })
    expired_url = f"/api/v1/staff/evidence/{evidence_id}/content?ticket={expired_ticket}"
    assert client.get(expired_url).status_code == 404
    content = client.get(retrieval.json["url"])
    assert content.status_code == 200
    assert content.data == _EVIDENCE_PDF
    assert content.headers["Cache-Control"] == "no-store"
    with app.app_context():
        assert EvidenceObject.query.filter_by(id=evidence_id).one().scan_status == "CLEAN"
        assert local_store.object_path(object_key).exists()
        audit_events = StaffAuditEvent.query.filter_by(object_id=evidence_id).all()
        audit_actions = {event.action for event in audit_events}
        assert audit_actions == {
            "STAFF_EVIDENCE_UPLOADED",
            "STAFF_EVIDENCE_RETRIEVAL_ISSUED",
            "STAFF_EVIDENCE_ACCESSED",
        }
        assert all(event.object_type == "evidence_object" for event in audit_events)
        audit_metadata = repr([
            (event.action, event.object_type, event.object_id, event.request_id)
            for event in audit_events
        ])
        assert "citizen-evidence.pdf" not in audit_metadata
        assert object_key not in audit_metadata
        assert hashlib.sha256(_EVIDENCE_PDF).hexdigest() not in audit_metadata
        session_hash = digest(client.get_cookie(SESSION_COOKIE).value)
        StaffSession.query.filter_by(session_hash=session_hash).one().revoked_at = datetime.now(timezone.utc)
        db.session.commit()
    assert client.get(retrieval.json["url"]).status_code == 401


def test_unassigned_same_tenant_officer_cannot_access_another_cases_evidence(tmp_path):
    app = _new_app()
    _enable_evidence_vault(app, tmp_path / "private")
    tenant_id, first_user = _seed_user(app)
    first = _authenticated_client(app)
    case_id, csrf = _case_for_staff(first)
    uploaded = first.post(
        f"/api/v1/staff/cases/{case_id}/evidence",
        data={"file": (BytesIO(_EVIDENCE_PDF), "evidence.pdf")},
        headers={"X-CSRF-Token": csrf}, content_type="multipart/form-data",
    )
    assert uploaded.status_code == 201
    evidence_id = uploaded.json["evidence"]["id"]
    second_secret = "KRSXG5DSNFXGOIDB"
    with app.app_context():
        user = StaffUser(
            tenant_id=tenant_id, email="unassigned@example.gov", display_name="Unassigned",
            password_hash=hash_password(_TEST_PASSWORD),
        )
        db.session.add(user)
        db.session.flush()
        second_user_id = user.id
        db.session.add(StaffRoleGrant(tenant_id=tenant_id, user_id=user.id, role="CASE_OFFICER"))
        db.session.add(StaffMfaFactor(
            tenant_id=tenant_id, user_id=user.id,
            secret_ciphertext=encrypt_totp_secret(second_secret), active=True,
        ))
        db.session.commit()
    second = _authenticated_client(app, email="unassigned@example.gov", secret=second_secret)

    assert second.get(f"/api/v1/staff/cases/{case_id}/evidence").status_code == 404
    assert second.get(f"/api/v1/staff/evidence/{evidence_id}/retrieval").status_code == 404
    denied_upload = second.post(
        f"/api/v1/staff/cases/{case_id}/evidence",
        data={"file": (BytesIO(_EVIDENCE_PDF), "evidence.pdf")},
        headers={"X-CSRF-Token": second.get_cookie(CSRF_COOKIE).value},
        content_type="multipart/form-data",
    )
    assert denied_upload.status_code == 404
    assert first_user != second_user_id


def test_expired_evidence_deletion_honors_legal_hold_and_verifies_retry(tmp_path):
    app = _new_app()
    _enable_evidence_vault(app, tmp_path / "private")
    tenant_id, _user_id = _seed_user(app)
    client = _authenticated_client(app)
    case_id, csrf = _case_for_staff(client)
    uploaded = client.post(
        f"/api/v1/staff/cases/{case_id}/evidence",
        data={"file": (BytesIO(_EVIDENCE_PDF), "evidence.pdf")},
        headers={"X-CSRF-Token": csrf}, content_type="multipart/form-data",
    )
    assert uploaded.status_code == 201
    evidence_id = uploaded.json["evidence"]["id"]
    with app.app_context():
        evidence = EvidenceObject.query.filter_by(tenant_id=tenant_id, id=evidence_id).one()
        evidence.legal_hold = True
        evidence.retention_until = datetime.now(timezone.utc) - timedelta(days=1)
        object_key = evidence.object_key
        db.session.commit()
    held = client.delete(
        f"/api/v1/staff/evidence/{evidence_id}", headers={"X-CSRF-Token": csrf}
    )
    assert held.status_code == 409
    with app.app_context():
        evidence = EvidenceObject.query.filter_by(id=evidence_id).one()
        assert evidence.lifecycle_status == "ACTIVE"
        assert app.extensions["scmirn_evidence_store"].object_path(object_key).exists()
        evidence.legal_hold = False
        db.session.commit()
        store = app.extensions["scmirn_evidence_store"]
        original_delete = store.delete
        store.delete = lambda key: False
    failed = client.delete(
        f"/api/v1/staff/evidence/{evidence_id}", headers={"X-CSRF-Token": csrf}
    )
    assert failed.status_code == 503
    with app.app_context():
        evidence = EvidenceObject.query.filter_by(id=evidence_id).one()
        assert evidence.lifecycle_status == "DELETE_FAILED"
        assert evidence.deletion_attempts == 1
        assert evidence.deletion_last_error == "OBJECT_STORE_UNVERIFIED"
        store.delete = original_delete
    deleted = client.delete(
        f"/api/v1/staff/evidence/{evidence_id}", headers={"X-CSRF-Token": csrf}
    )
    assert deleted.status_code == 200
    with app.app_context():
        evidence = EvidenceObject.query.filter_by(id=evidence_id).one()
        assert evidence.lifecycle_status == "DELETED"
        assert evidence.deleted_at is not None
        assert evidence.deletion_verified_at is not None


def test_evidence_upload_fails_closed_when_feature_or_scanner_is_unavailable(tmp_path):
    app = _new_app()
    tenant_id, _user_id = _seed_user(app)
    client = _authenticated_client(app)
    case_id, csrf = _case_for_staff(client)
    app.config.update(
        EVIDENCE_VAULT_ENABLED=True,
        EVIDENCE_DEFAULT_RETENTION_DAYS=30,
        EVIDENCE_RETENTION_POLICY_ID="test-authority-policy-v1",
    )
    app.extensions["scmirn_evidence_store"] = LocalPrivateStore(
        tmp_path / "private"
    )
    unavailable = client.post(
        f"/api/v1/staff/cases/{case_id}/evidence",
        data={"file": (BytesIO(_EVIDENCE_PDF), "evidence.pdf")},
        headers={"X-CSRF-Token": csrf}, content_type="multipart/form-data",
    )
    assert unavailable.status_code == 503
    assert unavailable.json["code"] == "EVIDENCE_DEPENDENCY_UNAVAILABLE"
    with app.app_context():
        assert EvidenceObject.query.filter_by(tenant_id=tenant_id).count() == 0
    app.config["EVIDENCE_VAULT_ENABLED"] = False
    disabled = client.post(
        f"/api/v1/staff/cases/{case_id}/evidence",
        data={"file": (BytesIO(_EVIDENCE_PDF), "evidence.pdf")},
        headers={"X-CSRF-Token": csrf}, content_type="multipart/form-data",
    )
    assert disabled.status_code == 503
    assert disabled.json["code"] == "EVIDENCE_VAULT_DISABLED"


def test_evidence_routes_are_disabled_in_the_default_test_profile():
    app = _new_app()
    _seed_user(app)
    client = _authenticated_client(app)
    case_id, csrf = _case_for_staff(client)

    response = client.post(
        f"/api/v1/staff/cases/{case_id}/evidence",
        data={"file": (BytesIO(_EVIDENCE_PDF), "evidence.pdf")},
        headers={"X-CSRF-Token": csrf}, content_type="multipart/form-data",
    )

    assert response.status_code == 503
    assert response.json["code"] == "EVIDENCE_VAULT_DISABLED"
