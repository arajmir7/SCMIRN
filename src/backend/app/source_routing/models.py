"""Versioned service, authority, source, and routing records.

Registry versions are append-only. A correction creates a new version instead of
silently changing the basis on which an earlier route was made.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import event

from app.extensions import db


def utcnow_naive():
    """Return UTC wall time for legacy timezone-naive database columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


government_service_sources = db.Table(
    "government_service_sources",
    db.Column("service_version_id", db.String(36), db.ForeignKey("government_services.id"), primary_key=True),
    db.Column("source_id", db.String(36), db.ForeignKey("official_sources.id"), primary_key=True),
)


class OfficialSource(db.Model):
    __tablename__ = "official_sources"
    __table_args__ = (
        db.UniqueConstraint("source_key", "version", name="uq_official_source_version"),
        db.CheckConstraint("version > 0", name="ck_official_source_positive_version"),
        db.CheckConstraint("verification_status IN ('DRAFT', 'VERIFIED', 'SUPERSEDED', 'REVOKED')", name="ck_official_source_status"),
        db.CheckConstraint("canonical_url LIKE 'https://%'", name="ck_official_source_https"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_key = db.Column(db.String(120), nullable=False, index=True)
    version = db.Column(db.Integer, nullable=False)
    authority = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    source_type = db.Column(db.String(40), nullable=False)
    jurisdiction = db.Column(db.String(120), nullable=False, default="INDIA")
    canonical_url = db.Column(db.String(2048), nullable=False)
    document_hash = db.Column(db.String(64))
    effective_from = db.Column(db.DateTime)
    effective_until = db.Column(db.DateTime)
    retrieved_at = db.Column(db.DateTime, nullable=False, default=utcnow_naive)
    verified_at = db.Column(db.DateTime)
    verification_status = db.Column(db.String(32), nullable=False, default="DRAFT")
    supersedes_id = db.Column(db.String(36), db.ForeignKey("official_sources.id"))
    superseded_by_id = db.Column(db.String(36), db.ForeignKey("official_sources.id"))
    reviewer = db.Column(db.String(255))
    parser_version = db.Column(db.String(80))


class Authority(db.Model):
    __tablename__ = "authorities"
    __table_args__ = (
        db.UniqueConstraint("authority_key", "version", name="uq_authority_version"),
        db.CheckConstraint("version > 0", name="ck_authority_positive_version"),
        db.CheckConstraint("authority_level IN ('CENTRAL', 'STATE', 'DISTRICT', 'LOCAL', 'REGULATOR', 'OTHER')", name="ck_authority_level"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    authority_key = db.Column(db.String(120), nullable=False, index=True)
    version = db.Column(db.Integer, nullable=False)
    canonical_name = db.Column(db.String(500), nullable=False)
    authority_level = db.Column(db.String(32), nullable=False)
    jurisdiction = db.Column(db.JSON, nullable=False, default=dict)
    official_source_id = db.Column(db.String(36), db.ForeignKey("official_sources.id"))
    status = db.Column(db.String(32), nullable=False, default="UNVERIFIED")
    effective_from = db.Column(db.DateTime)
    effective_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow_naive)


class GovernmentService(db.Model):
    __tablename__ = "government_services"
    __table_args__ = (
        db.UniqueConstraint("service_key", "version", name="uq_government_service_version"),
        db.CheckConstraint("version > 0", name="ck_government_service_positive_version"),
        db.CheckConstraint("status IN ('ACTIVE', 'DEPRECATED', 'SUPERSEDED', 'TEMPORARILY_UNAVAILABLE', 'UNVERIFIED')", name="ck_government_service_status"),
        db.CheckConstraint("integration_mode IN ('CONNECTED', 'SANDBOX_CONNECTED', 'CONNECTOR_IMPLEMENTED_NOT_AUTHORISED', 'OFFICIAL_HANDOFF_ONLY', 'PLANNED', 'UNAVAILABLE')", name="ck_government_service_integration_mode"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_key = db.Column(db.String(120), nullable=False, index=True)
    version = db.Column(db.Integer, nullable=False)
    canonical_name = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    authority_id = db.Column(db.String(36), db.ForeignKey("authorities.id"), nullable=False)
    department = db.Column(db.String(255))
    authority_level = db.Column(db.String(32), nullable=False)
    jurisdiction = db.Column(db.JSON, nullable=False, default=dict)
    geography = db.Column(db.JSON, nullable=False, default=dict)
    eligibility = db.Column(db.Text)
    exclusions = db.Column(db.JSON, nullable=False, default=list)
    issue_types = db.Column(db.JSON, nullable=False, default=list)
    required_evidence = db.Column(db.JSON, nullable=False, default=list)
    recommended_evidence = db.Column(db.JSON, nullable=False, default=list)
    optional_evidence = db.Column(db.JSON, nullable=False, default=list)
    application_channel = db.Column(db.String(2048))
    grievance_channel = db.Column(db.String(2048))
    appeal_channel = db.Column(db.String(2048))
    escalation_channel = db.Column(db.String(2048))
    official_url = db.Column(db.String(2048), nullable=False)
    integration_mode = db.Column(db.String(48), nullable=False)
    connector_id = db.Column(db.String(120))
    identity_assurance_required = db.Column(db.String(8), nullable=False, default="A0")
    official_sla = db.Column(db.JSON)
    effective_from = db.Column(db.DateTime)
    effective_until = db.Column(db.DateTime)
    last_verified = db.Column(db.DateTime)
    status = db.Column(db.String(40), nullable=False, default="UNVERIFIED")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow_naive)

    authority = db.relationship("Authority")
    sources = db.relationship("OfficialSource", secondary=government_service_sources, lazy="joined")


class RouteRule(db.Model):
    __tablename__ = "route_rules"
    __table_args__ = (
        db.UniqueConstraint("rule_key", "version", name="uq_route_rule_version"),
        db.CheckConstraint("version > 0", name="ck_route_rule_positive_version"),
        db.CheckConstraint("status IN ('ACTIVE', 'DEPRECATED', 'SUPERSEDED', 'UNVERIFIED')", name="ck_route_rule_status"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_key = db.Column(db.String(120), nullable=False, index=True)
    version = db.Column(db.Integer, nullable=False)
    issue_type = db.Column(db.String(120), nullable=False)
    match_terms = db.Column(db.JSON, nullable=False, default=list)
    exclusion_terms = db.Column(db.JSON, nullable=False, default=list)
    authority_id = db.Column(db.String(36), db.ForeignKey("authorities.id"), nullable=False)
    service_version_id = db.Column(db.String(36), db.ForeignKey("government_services.id"), nullable=False)
    source_ids = db.Column(db.JSON, nullable=False, default=list)
    priority = db.Column(db.Integer, nullable=False, default=100)
    effective_from = db.Column(db.DateTime)
    effective_until = db.Column(db.DateTime)
    status = db.Column(db.String(32), nullable=False, default="UNVERIFIED")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow_naive)

    authority = db.relationship("Authority")
    service = db.relationship("GovernmentService")


class RouteDecision(db.Model):
    __tablename__ = "route_decisions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    idempotency_key = db.Column(db.String(128), unique=True)
    input_fingerprint = db.Column(db.String(64), nullable=False, index=True)
    input_facts = db.Column(db.JSON, nullable=False)
    route_rule_id = db.Column(db.String(36), db.ForeignKey("route_rules.id"))
    route_rule_version = db.Column(db.String(160), nullable=False)
    service_registry_version = db.Column(db.String(160), nullable=False)
    source_versions = db.Column(db.JSON, nullable=False, default=list)
    model_version = db.Column(db.String(80))
    output_authority_id = db.Column(db.String(36), db.ForeignKey("authorities.id"))
    outcome = db.Column(db.String(48), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    output = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow_naive, index=True)
    retention_until = db.Column(db.DateTime, nullable=False)


def _reject_registry_version_update(mapper, connection, target):
    raise ValueError("Registry versions are immutable. Create a new version instead.")


for _versioned_model in (OfficialSource, Authority, GovernmentService, RouteRule):
    event.listen(_versioned_model, "before_update", _reject_registry_version_update)
