"""Hash-chain append and verification helpers for audit events."""
import hashlib
import json
import re
import uuid
from datetime import timezone

from sqlalchemy import text

from app.extensions import db
from app.source_routing.audit_models import AuditEvent
from app.source_routing.models import utcnow_naive


GENESIS_HASH = "0" * 64
_POSTGRES_LOCK_KEY = 0x53434D49524E
_FORBIDDEN_DETAIL_KEYS = re.compile(
    r"(description|free.?text|password|secret|token|authorization|email|phone|address|document|evidence.?content|file.?content)",
    re.IGNORECASE,
)


class AuditInputError(ValueError):
    pass


def _canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _event_payload(*, event_id, tenant_id, actor_id, actor_role, action, object_type, object_id, details, occurred_at, previous_hash):
    return {
        "event_id": event_id,
        "tenant_id": tenant_id,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "action": action,
        "object_type": object_type,
        "object_id": object_id,
        "details": details,
        "occurred_at": occurred_at.replace(tzinfo=timezone.utc).isoformat(timespec="microseconds"),
        "previous_hash": previous_hash,
    }


def _digest(payload):
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _reject_sensitive_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str) or _FORBIDDEN_DETAIL_KEYS.search(key):
                raise AuditInputError("Audit details contain a prohibited sensitive field name.")
            _reject_sensitive_keys(child)
    elif isinstance(value, list):
        for child in value:
            _reject_sensitive_keys(child)


def append_event(*, tenant_id, actor_id, actor_role, action, object_type, object_id, details=None):
    """Append an event in the caller's current transaction and return its row."""
    values = {
        "tenant_id": tenant_id,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "action": action,
        "object_type": object_type,
        "object_id": object_id,
    }
    field_limits = {
        "tenant_id": 120,
        "actor_id": 255,
        "actor_role": 40,
        "action": 120,
        "object_type": 80,
        "object_id": 120,
    }
    for name, value in values.items():
        maximum = field_limits[name]
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            raise AuditInputError(f"{name} must be a non-empty string of at most {maximum} characters.")
    details = {} if details is None else details
    if not isinstance(details, dict):
        raise AuditInputError("Audit details must be a JSON object.")
    _reject_sensitive_keys(details)
    encoded = _canonical_json(details)
    if len(encoded.encode("utf-8")) > 16 * 1024:
        raise AuditInputError("Audit details exceed the 16 KiB limit.")

    connection = db.session.connection()
    if connection.dialect.name == "postgresql":
        # Serialize writers until the surrounding transaction commits. This
        # prevents concurrent requests from selecting the same chain head.
        db.session.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": _POSTGRES_LOCK_KEY})

    previous = AuditEvent.query.order_by(AuditEvent.sequence.desc()).first()
    previous_hash = previous.event_hash if previous else GENESIS_HASH
    event_id = str(uuid.uuid4())
    occurred_at = utcnow_naive()
    payload = _event_payload(
        event_id=event_id,
        tenant_id=tenant_id,
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        object_type=object_type,
        object_id=object_id,
        details=details,
        occurred_at=occurred_at,
        previous_hash=previous_hash,
    )
    row = AuditEvent(
        event_id=event_id,
        **values,
        details=details,
        occurred_at=occurred_at,
        previous_hash=previous_hash,
        event_hash=_digest(payload),
    )
    db.session.add(row)
    db.session.flush()
    return row


def verify_chain():
    """Return a verifiable summary; no event content is returned."""
    previous_hash = GENESIS_HASH
    count = 0
    last_sequence = None
    for row in AuditEvent.query.order_by(AuditEvent.sequence.asc()).yield_per(500):
        if row.previous_hash != previous_hash:
            return {"valid": False, "count": count, "failed_sequence": row.sequence, "reason": "previous_hash_mismatch"}
        expected = _digest(_event_payload(
            event_id=row.event_id,
            tenant_id=row.tenant_id,
            actor_id=row.actor_id,
            actor_role=row.actor_role,
            action=row.action,
            object_type=row.object_type,
            object_id=row.object_id,
            details=row.details,
            occurred_at=row.occurred_at,
            previous_hash=row.previous_hash,
        ))
        if row.event_hash != expected:
            return {"valid": False, "count": count, "failed_sequence": row.sequence, "reason": "event_hash_mismatch"}
        previous_hash = row.event_hash
        last_sequence = row.sequence
        count += 1
    return {"valid": True, "count": count, "head_sequence": last_sequence, "head_hash": previous_hash}
