"""Security primitives for staff authentication and tenant-scoped requests."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import struct
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Iterable

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import current_app, g, jsonify, request
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.staff_auth.models import StaffAuditEvent, StaffMfaFactor, StaffSession, StaffUser


ROLES = frozenset({"TENANT_ADMIN", "CASE_OFFICER", "SOURCE_REVIEWER", "AUDITOR"})
SESSION_COOKIE = "scmirn_staff_session"
CSRF_COOKIE = "scmirn_staff_csrf"
DUMMY_PASSWORD_HASH = generate_password_hash("timing-only-invalid-password", method="scrypt:32768:8:1")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def normalize_db_time(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _encryption_key() -> bytes:
    encoded = current_app.config.get("STAFF_MFA_ENCRYPTION_KEY", "")
    if not isinstance(encoded, str) or not encoded:
        raise RuntimeError("STAFF_MFA_ENCRYPTION_KEY is required for staff MFA")
    try:
        key = base64.b64decode(
            encoded + "=" * (-len(encoded) % 4), altchars=b"-_", validate=True
        )
    except Exception as exc:
        raise RuntimeError("STAFF_MFA_ENCRYPTION_KEY must be URL-safe base64") from exc
    if len(key) != 32:
        raise RuntimeError("STAFF_MFA_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return key


def encrypt_totp_secret(secret: str) -> str:
    nonce = os.urandom(12)
    ciphertext = AESGCM(_encryption_key()).encrypt(nonce, secret.encode("ascii"), b"scmirn-staff-totp-v1")
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")


def decrypt_totp_secret(ciphertext: str) -> str:
    raw = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
    secret = AESGCM(_encryption_key()).decrypt(raw[:12], raw[12:], b"scmirn-staff-totp-v1")
    return secret.decode("ascii")


def new_totp_secret() -> str:
    import base64 as b64
    return b64.b32encode(os.urandom(20)).decode("ascii").rstrip("=")


def totp_counter(secret: str, code: str, at: int | None = None) -> int | None:
    if not isinstance(code, str) or len(code) != 6 or not code.isascii() or not code.isdigit():
        return None
    current = int((time.time() if at is None else at) // 30)
    secret_bytes = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    for counter in (current - 1, current, current + 1):
        if counter < 0:
            continue
        digest_bytes = hmac.new(secret_bytes, struct.pack(">Q", counter), hashlib.sha1).digest()
        offset = digest_bytes[-1] & 0x0F
        number = (struct.unpack(">I", digest_bytes[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
        expected = f"{number:06d}"
        if hmac.compare_digest(expected, code):
            return counter
    return None


def provisioning_uri(secret: str, email: str, tenant_slug: str) -> str:
    from urllib.parse import quote
    label = quote(f"SCMIRN:{tenant_slug}:{email}", safe="")
    issuer = quote("SCMIRN", safe="")
    return f"otpauth://totp/{label}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"


def set_tenant_scope(tenant_id: str) -> None:
    """Set PostgreSQL transaction-local scope; application queries also filter explicitly."""
    if db.engine.dialect.name == "postgresql":
        db.session.execute(text("SELECT set_config('scmirn.tenant_id', :tenant_id, true)"), {"tenant_id": tenant_id})


def set_session_scope(session_hash: str) -> None:
    if db.engine.dialect.name == "postgresql":
        db.session.execute(text("SELECT set_config('scmirn.staff_session_hash', :session_hash, true)"), {"session_hash": session_hash})


def set_session_management_scope(user_id: str) -> None:
    """Allow this transaction to manage sessions belonging to this one user."""
    if db.engine.dialect.name == "postgresql":
        db.session.execute(text("SELECT set_config('scmirn.staff_manage_user_id', :user_id, true)"), {"user_id": user_id})


def record_audit(action: str, object_type: str, object_id: str, actor_id: str | None) -> None:
    if not getattr(g, "staff_tenant_id", None):
        return
    db.session.add(StaffAuditEvent(
        tenant_id=g.staff_tenant_id,
        actor_id=actor_id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        request_id=request.environ.get("scmirn.request_id", "unavailable"),
    ))


def _auth_error(status: int = 401, code: str = "AUTHENTICATION_REQUIRED"):
    return jsonify({"success": False, "error": "Authentication is required.", "code": code}), status


def staff_required(*required_roles: str):
    unknown = set(required_roles) - ROLES
    if unknown:
        raise ValueError(f"Unknown staff roles: {', '.join(sorted(unknown))}")

    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_app.config.get("STAFF_AUTH_ENABLED"):
                return jsonify({"success": False, "error": "Staff authentication is disabled.", "code": "STAFF_AUTH_DISABLED"}), 503
            raw_token = request.cookies.get(SESSION_COOKIE)
            if not raw_token or len(raw_token) > 128:
                return _auth_error()
            session_hash = digest(raw_token)
            set_session_scope(session_hash)
            session_row = StaffSession.query.filter_by(session_hash=session_hash).first()
            now = now_utc()
            if not session_row or session_row.revoked_at:
                return _auth_error()
            idle_deadline = normalize_db_time(session_row.idle_expires_at)
            absolute_deadline = normalize_db_time(session_row.absolute_expires_at)
            if now >= idle_deadline or now >= absolute_deadline:
                session_row.revoked_at = now
                db.session.commit()
                return _auth_error()
            set_tenant_scope(session_row.tenant_id)
            user = StaffUser.query.filter_by(id=session_row.user_id, tenant_id=session_row.tenant_id, active=True).first()
            if not user:
                return _auth_error()
            csrf_cookie = request.cookies.get(CSRF_COOKIE, "")
            csrf_header = request.headers.get("X-CSRF-Token", "")
            safe_method = request.method in {"GET", "HEAD", "OPTIONS"}
            if not safe_method and (
                not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header)
                or not hmac.compare_digest(digest(csrf_header), session_row.csrf_hash)
            ):
                return jsonify({"success": False, "error": "CSRF token is invalid.", "code": "CSRF_REJECTED"}), 403
            from app.staff_auth.models import StaffRoleGrant
            roles = frozenset(grant.role for grant in StaffRoleGrant.query.filter_by(
                tenant_id=session_row.tenant_id, user_id=user.id
            ).all())
            if required_roles and not roles.intersection(required_roles):
                return jsonify({"success": False, "error": "Staff role is not authorized.", "code": "ROLE_FORBIDDEN"}), 403
            session_row.last_seen_at = now
            session_row.idle_expires_at = min(now + timedelta(minutes=int(current_app.config.get("STAFF_SESSION_IDLE_MINUTES", 30))), absolute_deadline)
            g.staff_session = session_row
            g.staff_user = user
            g.staff_roles = roles
            g.staff_tenant_id = session_row.tenant_id
            response = view(*args, **kwargs)
            db.session.commit()
            return response
        return wrapped
    return decorate


def verify_password(encoded: str, password: str) -> bool:
    try:
        return check_password_hash(encoded, password)
    except (ValueError, TypeError):
        return False


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="scrypt:32768:8:1")


def password_meets_policy(password: str) -> bool:
    return (
        isinstance(password, str)
        and 14 <= len(password) <= 128
        and any(character.isalpha() for character in password)
        and any(character.isdigit() for character in password)
    )
