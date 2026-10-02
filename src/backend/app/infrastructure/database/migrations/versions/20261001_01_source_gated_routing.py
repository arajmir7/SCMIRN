"""Create source-gated routing and metadata audit tables.

Revision ID: 20261001_01
Revises: None
Create Date: 2026-10-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20261001_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "official_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_key", sa.String(120), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("authority", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("jurisdiction", sa.String(120), nullable=False),
        sa.Column("canonical_url", sa.String(2048), nullable=False),
        sa.Column("document_hash", sa.String(64)),
        sa.Column("effective_from", sa.DateTime()),
        sa.Column("effective_until", sa.DateTime()),
        sa.Column("retrieved_at", sa.DateTime(), nullable=False),
        sa.Column("verified_at", sa.DateTime()),
        sa.Column("verification_status", sa.String(32), nullable=False),
        sa.Column("supersedes_id", sa.String(36), sa.ForeignKey("official_sources.id")),
        sa.Column("superseded_by_id", sa.String(36), sa.ForeignKey("official_sources.id")),
        sa.Column("reviewer", sa.String(255)),
        sa.Column("parser_version", sa.String(80)),
        sa.UniqueConstraint("source_key", "version", name="uq_official_source_version"),
        sa.CheckConstraint("version > 0", name="ck_official_source_positive_version"),
        sa.CheckConstraint("verification_status IN ('UNVERIFIED', 'VERIFIED', 'SUPERSEDED', 'UNAVAILABLE')", name="ck_official_source_status"),
        sa.CheckConstraint("canonical_url LIKE 'https://%'", name="ck_official_source_https"),
    )
    op.create_index("ix_official_sources_source_key", "official_sources", ["source_key"])

    op.create_table(
        "authorities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("authority_key", sa.String(120), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("canonical_name", sa.String(500), nullable=False),
        sa.Column("authority_level", sa.String(32), nullable=False),
        sa.Column("jurisdiction", sa.JSON(), nullable=False),
        sa.Column("official_source_id", sa.String(36), sa.ForeignKey("official_sources.id")),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("effective_from", sa.DateTime()),
        sa.Column("effective_until", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("authority_key", "version", name="uq_authority_version"),
        sa.CheckConstraint("version > 0", name="ck_authority_positive_version"),
        sa.CheckConstraint("authority_level IN ('CENTRAL', 'STATE', 'DISTRICT', 'LOCAL', 'REGULATOR', 'OTHER')", name="ck_authority_level"),
    )
    op.create_index("ix_authorities_authority_key", "authorities", ["authority_key"])

    op.create_table(
        "government_services",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("service_key", sa.String(120), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("canonical_name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("authority_id", sa.String(36), sa.ForeignKey("authorities.id"), nullable=False),
        sa.Column("department", sa.String(255)),
        sa.Column("authority_level", sa.String(32), nullable=False),
        sa.Column("jurisdiction", sa.JSON(), nullable=False),
        sa.Column("geography", sa.JSON(), nullable=False),
        sa.Column("eligibility", sa.Text()),
        sa.Column("exclusions", sa.JSON(), nullable=False),
        sa.Column("issue_types", sa.JSON(), nullable=False),
        sa.Column("required_evidence", sa.JSON(), nullable=False),
        sa.Column("recommended_evidence", sa.JSON(), nullable=False),
        sa.Column("optional_evidence", sa.JSON(), nullable=False),
        sa.Column("application_channel", sa.String(2048)),
        sa.Column("grievance_channel", sa.String(2048)),
        sa.Column("appeal_channel", sa.String(2048)),
        sa.Column("escalation_channel", sa.String(2048)),
        sa.Column("official_url", sa.String(2048), nullable=False),
        sa.Column("integration_mode", sa.String(48), nullable=False),
        sa.Column("connector_id", sa.String(120)),
        sa.Column("identity_assurance_required", sa.String(8), nullable=False),
        sa.Column("official_sla", sa.JSON()),
        sa.Column("effective_from", sa.DateTime()),
        sa.Column("effective_until", sa.DateTime()),
        sa.Column("last_verified", sa.DateTime()),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("service_key", "version", name="uq_government_service_version"),
        sa.CheckConstraint("version > 0", name="ck_government_service_positive_version"),
        sa.CheckConstraint("status IN ('ACTIVE', 'DEPRECATED', 'SUPERSEDED', 'TEMPORARILY_UNAVAILABLE', 'UNVERIFIED')", name="ck_government_service_status"),
        sa.CheckConstraint("integration_mode IN ('CONNECTED', 'SANDBOX_CONNECTED', 'CONNECTOR_IMPLEMENTED_NOT_AUTHORISED', 'OFFICIAL_HANDOFF_ONLY', 'PLANNED', 'UNAVAILABLE')", name="ck_government_service_integration_mode"),
    )
    op.create_index("ix_government_services_service_key", "government_services", ["service_key"])

    op.create_table(
        "government_service_sources",
        sa.Column("service_version_id", sa.String(36), sa.ForeignKey("government_services.id"), primary_key=True),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("official_sources.id"), primary_key=True),
    )

    op.create_table(
        "route_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rule_key", sa.String(120), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("issue_type", sa.String(120), nullable=False),
        sa.Column("match_terms", sa.JSON(), nullable=False),
        sa.Column("exclusion_terms", sa.JSON(), nullable=False),
        sa.Column("authority_id", sa.String(36), sa.ForeignKey("authorities.id"), nullable=False),
        sa.Column("service_version_id", sa.String(36), sa.ForeignKey("government_services.id"), nullable=False),
        sa.Column("source_ids", sa.JSON(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("effective_from", sa.DateTime()),
        sa.Column("effective_until", sa.DateTime()),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("rule_key", "version", name="uq_route_rule_version"),
        sa.CheckConstraint("version > 0", name="ck_route_rule_positive_version"),
        sa.CheckConstraint("status IN ('ACTIVE', 'DEPRECATED', 'SUPERSEDED', 'UNVERIFIED')", name="ck_route_rule_status"),
    )
    op.create_index("ix_route_rules_rule_key", "route_rules", ["rule_key"])

    op.create_table(
        "route_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idempotency_key", sa.String(128), unique=True),
        sa.Column("input_fingerprint", sa.String(64), nullable=False),
        sa.Column("input_facts", sa.JSON(), nullable=False),
        sa.Column("route_rule_id", sa.String(36), sa.ForeignKey("route_rules.id")),
        sa.Column("route_rule_version", sa.String(160), nullable=False),
        sa.Column("service_registry_version", sa.String(160), nullable=False),
        sa.Column("source_versions", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(80)),
        sa.Column("output_authority_id", sa.String(36), sa.ForeignKey("authorities.id")),
        sa.Column("outcome", sa.String(48), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("retention_until", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_route_decisions_input_fingerprint", "route_decisions", ["input_fingerprint"])
    op.create_index("ix_route_decisions_created_at", "route_decisions", ["created_at"])

    op.create_table(
        "audit_events",
        sa.Column("sequence", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(36), nullable=False, unique=True),
        sa.Column("tenant_id", sa.String(120), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=False),
        sa.Column("actor_role", sa.String(40), nullable=False),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("object_type", sa.String(80), nullable=False),
        sa.Column("object_id", sa.String(120), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("previous_hash", sa.String(64), nullable=False),
        sa.Column("event_hash", sa.String(64), nullable=False, unique=True),
    )
    op.create_index("ix_audit_events_tenant_id", "audit_events", ["tenant_id"])
    op.create_index("ix_audit_events_occurred_at", "audit_events", ["occurred_at"])

    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
            CREATE FUNCTION scmirn_reject_audit_mutation() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'audit_events is append-only';
            END;
            $$ LANGUAGE plpgsql;
        """)
        op.execute("""
            CREATE TRIGGER scmirn_audit_events_append_only
            BEFORE UPDATE OR DELETE ON audit_events
            FOR EACH ROW EXECUTE FUNCTION scmirn_reject_audit_mutation();
        """)


def downgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS scmirn_audit_events_append_only ON audit_events")
        op.execute("DROP FUNCTION IF EXISTS scmirn_reject_audit_mutation()")
    op.drop_table("audit_events")
    op.drop_index("ix_route_decisions_created_at", table_name="route_decisions")
    op.drop_index("ix_route_decisions_input_fingerprint", table_name="route_decisions")
    op.drop_table("route_decisions")
    op.drop_index("ix_route_rules_rule_key", table_name="route_rules")
    op.drop_table("route_rules")
    op.drop_table("government_service_sources")
    op.drop_index("ix_government_services_service_key", table_name="government_services")
    op.drop_table("government_services")
    op.drop_index("ix_authorities_authority_key", table_name="authorities")
    op.drop_table("authorities")
    op.drop_index("ix_official_sources_source_key", table_name="official_sources")
    op.drop_table("official_sources")
