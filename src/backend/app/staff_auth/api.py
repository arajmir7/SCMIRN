"""Staff login, MFA enrollment, tenant case workflow, and role-protected APIs."""
from __future__ import annotations

import secrets
import uuid
from datetime import timedelta

from flask import Blueprint, current_app, g, jsonify, make_response, request
from flask_limiter.util import get_remote_address
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import or_, update

from app.extensions import db, limiter
from app.staff_auth.authorization import PolicyAttributes, StaffPrincipal, authorize
from app.staff_auth.models import (
    StaffCase, StaffCaseEvent, StaffMfaChallenge, StaffMfaFactor,
    StaffRoleGrant, StaffSession, StaffUser, Tenant,
)
from app.staff_auth.security import (
    CSRF_COOKIE, DUMMY_PASSWORD_HASH, SESSION_COOKIE, decrypt_totp_secret, digest,
    hash_password, new_totp_secret, normalize_db_time, now_utc,
    password_meets_policy, provisioning_uri, record_audit, set_session_management_scope,
    set_session_scope, set_tenant_scope, staff_required,
    totp_counter, verify_password,
)


bp = Blueprint("staff_auth", __name__)
ROLES = {"TENANT_ADMIN", "CASE_OFFICER", "SOURCE_REVIEWER", "AUDITOR"}
CASE_TITLES = {
    "ROADS": "Road infrastructure case",
    "WATER": "Water service case",
    "WASTE": "Waste management case",
    "ELECTRICITY": "Electricity service case",
    "PUBLIC_SERVICE": "Public service case",
}
CASE_STATUSES = {"OPEN", "UNDER_REVIEW", "ACTION_REQUIRED", "RESOLVED", "CLOSED"}
CASE_TRANSITIONS = {
    "OPEN": {"UNDER_REVIEW", "CLOSED"},
    "UNDER_REVIEW": {"ACTION_REQUIRED", "RESOLVED", "CLOSED"},
    "ACTION_REQUIRED": {"UNDER_REVIEW", "RESOLVED", "CLOSED"},
    "RESOLVED": {"CLOSED", "UNDER_REVIEW"},
    "CLOSED": set(),
}


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="scmirn-staff-mfa-challenge-v1")


def _staff_disabled():
    return not current_app.config.get("STAFF_AUTH_ENABLED")


def _generic_login_failure():
    return jsonify({"success": False, "error": "Credentials or second factor were not accepted.", "code": "LOGIN_FAILED"}), 401


def _json_body():
    return request.get_json(silent=True) if isinstance(request.get_json(silent=True), dict) else {}


def _as_utc(value):
    return normalize_db_time(value)


def _policy_principal():
    return StaffPrincipal(
        user_id=g.staff_user.id,
        tenant_id=g.staff_tenant_id,
        roles=frozenset(g.staff_roles),
        active=bool(g.staff_user.active),
        mfa_verified=bool(g.staff_session.mfa_verified_at),
    )


def _case_policy_attributes(case=None):
    return PolicyAttributes(
        tenant_id=case.tenant_id if case is not None else g.staff_tenant_id,
        purpose="CASE_OPERATIONS",
        sensitivity="INTERNAL",
        created_by_id=case.created_by if case is not None else g.staff_user.id,
        owner_id=case.created_by if case is not None else g.staff_user.id,
        assigned_user_id=case.assigned_user_id if case is not None else None,
    )


@bp.post("/auth/login")
@limiter.limit("10 per minute", key_func=get_remote_address)
def staff_login():
    if _staff_disabled():
        return jsonify({"success": False, "error": "Staff authentication is disabled.", "code": "STAFF_AUTH_DISABLED"}), 503
    data = _json_body()
    tenant_slug = data.get("tenant_slug")
    email = data.get("email")
    password = data.get("password")
    if not all(isinstance(value, str) for value in (tenant_slug, email, password)):
        return _generic_login_failure()
    tenant_slug = tenant_slug.strip().lower()
    email = email.strip().lower()
    if len(tenant_slug) > 80 or len(email) > 254 or len(password) > 256:
        return _generic_login_failure()
    tenant = Tenant.query.filter_by(slug=tenant_slug, active=True).first()
    if not tenant:
        # Keep the no-tenant path close to the known-user password path.
        verify_password(DUMMY_PASSWORD_HASH, password)
        return _generic_login_failure()
    set_tenant_scope(tenant.id)
    user = StaffUser.query.filter_by(tenant_id=tenant.id, email=email).with_for_update().first()
    if not user:
        verify_password(DUMMY_PASSWORD_HASH, password)
        return _generic_login_failure()
    password_ok = verify_password(user.password_hash, password)
    now = now_utc()
    locked = bool(user.locked_until and _as_utc(user.locked_until) > now)
    if not user.active or locked or not password_ok:
        if user.active and not locked:
            user.failed_login_count += 1
            if user.failed_login_count >= 5:
                user.locked_until = now + timedelta(minutes=15)
            db.session.commit()
        return _generic_login_failure()
    factor = StaffMfaFactor.query.filter_by(tenant_id=tenant.id, user_id=user.id, active=True).with_for_update().first()
    if not factor:
        return _generic_login_failure()
    user.failed_login_count = 0
    user.locked_until = None
    challenge_id = secrets.token_urlsafe(32)
    challenge = _serializer().dumps({"nonce": challenge_id, "tenant_id": tenant.id, "user_id": user.id})
    db.session.add(StaffMfaChallenge(
        token_hash=digest(challenge_id), tenant_id=tenant.id, user_id=user.id,
        expires_at=now + timedelta(minutes=5),
    ))
    db.session.commit()
    return jsonify({"success": True, "mfa_required": True, "challenge": challenge, "expires_in": 300}), 200


@bp.post("/auth/mfa")
@limiter.limit("8 per minute", key_func=get_remote_address)
def staff_mfa():
    if _staff_disabled():
        return jsonify({"success": False, "error": "Staff authentication is disabled.", "code": "STAFF_AUTH_DISABLED"}), 503
    data = _json_body()
    challenge_token = data.get("challenge")
    code = data.get("code")
    if not isinstance(challenge_token, str) or len(challenge_token) > 1024 or not isinstance(code, str):
        return _generic_login_failure()
    try:
        payload = _serializer().loads(challenge_token, max_age=300)
        tenant_id, user_id, challenge_id = payload["tenant_id"], payload["user_id"], payload["nonce"]
        uuid.UUID(tenant_id)
        uuid.UUID(user_id)
    except (BadSignature, SignatureExpired, KeyError, TypeError, ValueError):
        return _generic_login_failure()
    tenant = Tenant.query.filter_by(id=tenant_id, active=True).first()
    if not tenant:
        return _generic_login_failure()
    set_tenant_scope(tenant_id)
    challenge = StaffMfaChallenge.query.filter_by(token_hash=digest(challenge_id), tenant_id=tenant_id, user_id=user_id).first()
    user = StaffUser.query.filter_by(id=user_id, tenant_id=tenant_id, active=True).first()
    factor = StaffMfaFactor.query.filter_by(tenant_id=tenant_id, user_id=user_id, active=True).with_for_update().first()
    now = now_utc()
    if not challenge or not user or not factor or challenge.consumed_at or _as_utc(challenge.expires_at) <= now:
        return _generic_login_failure()
    if factor.locked_until and _as_utc(factor.locked_until) > now:
        return _generic_login_failure()
    try:
        counter = totp_counter(decrypt_totp_secret(factor.secret_ciphertext), code)
    except Exception:
        current_app.logger.error("Staff MFA secret could not be decrypted; request_id=%s", request.environ.get("scmirn.request_id"))
        return _generic_login_failure()
    if counter is None:
        factor.failed_attempts += 1
        if factor.failed_attempts >= 5:
            factor.locked_until = now + timedelta(minutes=15)
        db.session.commit()
        return _generic_login_failure()
    claimed = db.session.execute(update(StaffMfaFactor).where(
        StaffMfaFactor.id == factor.id,
        StaffMfaFactor.tenant_id == tenant_id,
        StaffMfaFactor.last_totp_step < counter,
    ).values(last_totp_step=counter).execution_options(synchronize_session=False))
    consumed = db.session.execute(update(StaffMfaChallenge).where(
        StaffMfaChallenge.token_hash == challenge.token_hash,
        StaffMfaChallenge.tenant_id == tenant_id,
        StaffMfaChallenge.consumed_at.is_(None),
        StaffMfaChallenge.expires_at > now,
    ).values(consumed_at=now).execution_options(synchronize_session=False))
    if claimed.rowcount != 1 or consumed.rowcount != 1:
        db.session.rollback()
        return _generic_login_failure()
    factor.failed_attempts = 0
    factor.locked_until = None
    raw_session = secrets.token_urlsafe(32)
    raw_csrf = secrets.token_urlsafe(32)
    set_session_scope(digest(raw_session))
    absolute_hours = int(current_app.config.get("STAFF_SESSION_ABSOLUTE_HOURS", 12))
    idle_minutes = int(current_app.config.get("STAFF_SESSION_IDLE_MINUTES", 30))
    absolute_expiry = now + timedelta(hours=absolute_hours)
    db.session.add(StaffSession(
        session_hash=digest(raw_session), tenant_id=tenant_id, user_id=user_id,
        csrf_hash=digest(raw_csrf), mfa_verified_at=now,
        created_at=now, last_seen_at=now,
        idle_expires_at=min(now + timedelta(minutes=idle_minutes), absolute_expiry),
        absolute_expires_at=absolute_expiry,
    ))
    roles = [row.role for row in StaffRoleGrant.query.filter_by(tenant_id=tenant_id, user_id=user_id).all()]
    user_response = {"id": user.id, "email": user.email, "display_name": user.display_name}
    record_audit("STAFF_LOGIN", "staff_user", user_id, user_id)
    db.session.commit()
    response = make_response(jsonify({
        "success": True,
        "user": user_response,
        "roles": sorted(roles),
        "mfa_verified": True,
        "session_expires_at": absolute_expiry.isoformat(),
    }))
    secure = current_app.config.get("SCMIRN_ENVIRONMENT") == "production"
    response.set_cookie(SESSION_COOKIE, raw_session, max_age=absolute_hours * 3600, secure=secure, httponly=True, samesite="Strict", path="/")
    response.set_cookie(CSRF_COOKIE, raw_csrf, max_age=absolute_hours * 3600, secure=secure, httponly=False, samesite="Strict", path="/")
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.post("/auth/mfa/enroll/confirm")
@limiter.limit("8 per minute", key_func=get_remote_address)
def confirm_mfa_enrollment():
    if _staff_disabled():
        return jsonify({"success": False, "error": "Staff authentication is disabled.", "code": "STAFF_AUTH_DISABLED"}), 503
    data = _json_body()
    slug, token, code = data.get("tenant_slug"), data.get("enrollment_token"), data.get("code")
    if not all(isinstance(value, str) for value in (slug, token, code)) or len(token) > 256:
        return _generic_login_failure()
    tenant = Tenant.query.filter_by(slug=slug.strip().lower(), active=True).first()
    if not tenant:
        return _generic_login_failure()
    set_tenant_scope(tenant.id)
    token_hash = digest(token)
    factor = StaffMfaFactor.query.filter_by(tenant_id=tenant.id, enrollment_token_hash=token_hash, active=False).with_for_update().first()
    now = now_utc()
    if not factor or not factor.enrollment_expires_at or _as_utc(factor.enrollment_expires_at) <= now:
        return _generic_login_failure()
    if factor.locked_until and _as_utc(factor.locked_until) > now:
        return _generic_login_failure()
    try:
        counter = totp_counter(decrypt_totp_secret(factor.secret_ciphertext), code)
    except Exception:
        return _generic_login_failure()
    if counter is None:
        factor.failed_attempts += 1
        if factor.failed_attempts >= 5:
            factor.locked_until = now + timedelta(minutes=15)
        db.session.commit()
        return _generic_login_failure()
    factor.active = True
    factor.last_totp_step = counter
    factor.failed_attempts = 0
    factor.locked_until = None
    factor.enrollment_token_hash = None
    factor.enrollment_expires_at = None
    factor.activated_at = now
    record_audit("STAFF_MFA_ENROLLED", "staff_user", factor.user_id, factor.user_id)
    db.session.commit()
    return jsonify({"success": True, "mfa_enrolled": True}), 200


@bp.get("/auth/me")
@staff_required()
def staff_me():
    return jsonify({
        "success": True,
        "user": {"id": g.staff_user.id, "email": g.staff_user.email, "display_name": g.staff_user.display_name},
        "tenant": {"id": g.staff_tenant_id},
        "roles": sorted(g.staff_roles),
        "mfa_verified_at": _as_utc(g.staff_session.mfa_verified_at).isoformat(),
    })


@bp.post("/auth/logout")
@staff_required()
def staff_logout():
    g.staff_session.revoked_at = now_utc()
    record_audit("STAFF_LOGOUT", "staff_user", g.staff_user.id, g.staff_user.id)
    db.session.commit()
    response = make_response(jsonify({"success": True, "logged_out": True}))
    response.delete_cookie(SESSION_COOKIE, path="/", secure=current_app.config.get("SCMIRN_ENVIRONMENT") == "production", httponly=True, samesite="Strict")
    response.delete_cookie(CSRF_COOKIE, path="/", secure=current_app.config.get("SCMIRN_ENVIRONMENT") == "production", httponly=False, samesite="Strict")
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.post("/auth/password/change")
@staff_required()
def change_staff_password():
    data = _json_body()
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    if not isinstance(current_password, str) or not isinstance(new_password, str):
        return jsonify({"success": False, "error": "Current and new passwords are required.", "code": "INVALID_PASSWORD_CHANGE"}), 400
    if not verify_password(g.staff_user.password_hash, current_password):
        return jsonify({"success": False, "error": "Current password was not accepted.", "code": "INVALID_PASSWORD_CHANGE"}), 400
    if not password_meets_policy(new_password) or verify_password(g.staff_user.password_hash, new_password):
        return jsonify({"success": False, "error": "New password does not meet the password policy.", "code": "INVALID_PASSWORD_CHANGE"}), 400
    now = now_utc()
    g.staff_user.password_hash = hash_password(new_password)
    g.staff_user.password_changed_at = now
    set_session_management_scope(g.staff_user.id)
    for session_row in StaffSession.query.filter_by(tenant_id=g.staff_tenant_id, user_id=g.staff_user.id, revoked_at=None).all():
        session_row.revoked_at = now
    record_audit("STAFF_PASSWORD_CHANGED", "staff_user", g.staff_user.id, g.staff_user.id)
    db.session.commit()
    response = make_response(jsonify({"success": True, "sessions_revoked": True, "login_required": True}))
    secure = current_app.config.get("SCMIRN_ENVIRONMENT") == "production"
    response.delete_cookie(SESSION_COOKIE, path="/", secure=secure, httponly=True, samesite="Strict")
    response.delete_cookie(CSRF_COOKIE, path="/", secure=secure, httponly=False, samesite="Strict")
    response.headers["Cache-Control"] = "no-store"
    return response


def _case_json(case):
    return {
        "id": case.id, "case_ref": case.case_ref, "case_type": case.case_type,
        "title": case.title, "status": case.status, "priority": case.priority,
        "assigned_user_id": case.assigned_user_id,
        "created_at": _as_utc(case.created_at).isoformat(),
        "updated_at": _as_utc(case.updated_at).isoformat(),
    }


@bp.get("/cases")
@staff_required("TENANT_ADMIN", "CASE_OFFICER", "AUDITOR")
def list_cases():
    query = StaffCase.query.filter_by(tenant_id=g.staff_tenant_id)
    if not g.staff_roles.intersection({"TENANT_ADMIN", "AUDITOR"}):
        query = query.filter(or_(
            StaffCase.created_by == g.staff_user.id,
            StaffCase.assigned_user_id == g.staff_user.id,
        ))
    cases = query.order_by(StaffCase.created_at.desc()).limit(100).all()
    visible = [
        _case_json(case) for case in cases
        if authorize(_policy_principal(), "case:list", _case_policy_attributes(case))
    ]
    return jsonify({"success": True, "cases": visible})


@bp.post("/cases")
@staff_required("TENANT_ADMIN", "CASE_OFFICER")
def create_case():
    if not authorize(_policy_principal(), "case:create", _case_policy_attributes()):
        return jsonify({"success": False, "error": "Staff attributes do not authorize this action.", "code": "ATTRIBUTE_FORBIDDEN"}), 403
    data = _json_body()
    case_type = data.get("case_type")
    priority = data.get("priority", "NORMAL")
    if case_type not in CASE_TITLES or priority not in {"LOW", "NORMAL", "HIGH", "URGENT"}:
        return jsonify({"success": False, "error": "Case type or priority is invalid.", "code": "INVALID_CASE"}), 400
    now = now_utc()
    case = StaffCase(
        tenant_id=g.staff_tenant_id,
        case_ref=f"C-{now.strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}",
        case_type=case_type,
        title=CASE_TITLES[case_type],
        status="OPEN", priority=priority, created_by=g.staff_user.id,
        created_at=now, updated_at=now,
    )
    db.session.add(case)
    db.session.flush()
    db.session.add(StaffCaseEvent(
        tenant_id=g.staff_tenant_id, case_id=case.id, actor_id=g.staff_user.id,
        event_type="CASE_CREATED", from_status=None, to_status="OPEN", metadata_json={},
    ))
    record_audit("CASE_CREATED", "staff_case", case.id, g.staff_user.id)
    case_response = _case_json(case)
    db.session.commit()
    return jsonify({"success": True, "case": case_response}), 201


@bp.get("/cases/<case_id>")
@staff_required("TENANT_ADMIN", "CASE_OFFICER", "AUDITOR")
def get_case(case_id):
    case = StaffCase.query.filter_by(id=case_id, tenant_id=g.staff_tenant_id).with_for_update().first()
    if not case:
        return jsonify({"success": False, "error": "Case not found.", "code": "NOT_FOUND"}), 404
    if not authorize(_policy_principal(), "case:read", _case_policy_attributes(case)):
        return jsonify({"success": False, "error": "Case not found.", "code": "NOT_FOUND"}), 404
    events = StaffCaseEvent.query.filter_by(case_id=case.id, tenant_id=g.staff_tenant_id).order_by(StaffCaseEvent.created_at.asc()).all()
    return jsonify({"success": True, "case": _case_json(case), "events": [
        {"event_type": event.event_type, "from_status": event.from_status, "to_status": event.to_status, "created_at": _as_utc(event.created_at).isoformat()}
        for event in events
    ]})


@bp.post("/cases/<case_id>/status")
@staff_required("TENANT_ADMIN", "CASE_OFFICER")
def change_case_status(case_id):
    data = _json_body()
    next_status = data.get("status")
    if next_status not in CASE_STATUSES:
        return jsonify({"success": False, "error": "Case status is invalid.", "code": "INVALID_STATUS"}), 400
    case = StaffCase.query.filter_by(id=case_id, tenant_id=g.staff_tenant_id).first()
    if not case:
        return jsonify({"success": False, "error": "Case not found.", "code": "NOT_FOUND"}), 404
    if not authorize(_policy_principal(), "case:update_status", _case_policy_attributes(case)):
        return jsonify({"success": False, "error": "Case not found.", "code": "NOT_FOUND"}), 404
    if next_status == case.status:
        return jsonify({"success": True, "case": _case_json(case)}), 200
    if next_status not in CASE_TRANSITIONS[case.status]:
        return jsonify({"success": False, "error": "Case status transition is not allowed.", "code": "INVALID_TRANSITION"}), 409
    previous = case.status
    case.status = next_status
    case.updated_at = now_utc()
    db.session.add(StaffCaseEvent(
        tenant_id=g.staff_tenant_id, case_id=case.id, actor_id=g.staff_user.id,
        event_type="STATUS_CHANGED", from_status=previous, to_status=next_status, metadata_json={},
    ))
    record_audit("CASE_STATUS_CHANGED", "staff_case", case.id, g.staff_user.id)
    case_response = _case_json(case)
    db.session.commit()
    return jsonify({"success": True, "case": case_response}), 200
