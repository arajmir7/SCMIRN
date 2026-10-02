"""Append-only, hash-chained audit events.

Events intentionally accept only bounded identifiers and metadata. Callers
must not put report text, credentials, or evidence content in ``details``.
"""
import uuid

from sqlalchemy import event

from app.extensions import db
from app.source_routing.models import utcnow_naive


class AuditEvent(db.Model):
    __tablename__ = "audit_events"

    sequence = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(120), nullable=False, index=True)
    actor_id = db.Column(db.String(255), nullable=False)
    actor_role = db.Column(db.String(40), nullable=False)
    action = db.Column(db.String(120), nullable=False)
    object_type = db.Column(db.String(80), nullable=False)
    object_id = db.Column(db.String(120), nullable=False)
    details = db.Column(db.JSON, nullable=False, default=dict)
    occurred_at = db.Column(db.DateTime, nullable=False, default=utcnow_naive, index=True)
    previous_hash = db.Column(db.String(64), nullable=False)
    event_hash = db.Column(db.String(64), nullable=False, unique=True)


def _reject_audit_mutation(mapper, connection, target):
    raise ValueError("Audit events are append-only; record a corrective event instead.")


event.listen(AuditEvent, "before_update", _reject_audit_mutation)
event.listen(AuditEvent, "before_delete", _reject_audit_mutation)
