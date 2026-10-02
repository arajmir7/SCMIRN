"""Retention job for privacy-minimized route decision records."""
from app.extensions import db
from app.source_routing.models import RouteDecision, utcnow_naive
from app.source_routing.audit_chain import append_event


def purge_expired_route_decisions(*, dry_run=False, now=None):
    """Delete expired route decisions and append a metadata-only audit event."""
    now = now or utcnow_naive()
    query = RouteDecision.query.filter(RouteDecision.retention_until <= now)
    expired_count = query.count()
    if dry_run:
        db.session.rollback()
        return {"dry_run": True, "would_delete": expired_count, "deleted": 0}

    deleted = query.delete(synchronize_session=False)
    if deleted:
        append_event(
            tenant_id="system:retention",
            actor_id="system:retention-worker",
            actor_role="system",
            action="retention.route_decisions.purged",
            object_type="route_decision_retention",
            object_id=now.isoformat(timespec="microseconds"),
            details={"count": deleted, "retention_days": 30},
        )
    db.session.commit()
    pending = RouteDecision.query.filter(RouteDecision.retention_until <= now).count()
    return {"dry_run": False, "would_delete": expired_count, "deleted": deleted, "pending": pending}
