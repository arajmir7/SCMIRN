"""Create private evidence metadata with tenant and case boundaries.

Revision ID: 20261003_01
Revises: 20261002_04
"""
from alembic import op
import sqlalchemy as sa


revision = "20261003_01"
down_revision = "20261002_04"
branch_labels = None
depends_on = None


def upgrade():
    if not sa.inspect(op.get_bind()).has_table("evidence_objects"):
        op.create_table(
            "evidence_objects",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("case_id", sa.String(length=36), nullable=False),
            sa.Column("created_by", sa.String(length=36), nullable=False),
            sa.Column("object_key", sa.String(length=64), nullable=False),
            sa.Column("content_type", sa.String(length=64), nullable=False),
            sa.Column("size_bytes", sa.BigInteger(), nullable=False),
            sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
            sa.Column("scan_status", sa.String(length=16), nullable=False),
            sa.Column("scanner_version", sa.String(length=120), nullable=False),
            sa.Column("retention_policy_id", sa.String(length=120), nullable=False),
            sa.Column("retention_until", sa.DateTime(timezone=True), nullable=False),
            sa.Column("legal_hold", sa.Boolean(), nullable=False),
            sa.Column("lifecycle_status", sa.String(length=24), nullable=False),
            sa.Column("deletion_attempts", sa.Integer(), nullable=False),
            sa.Column("deletion_last_error", sa.String(length=64), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deletion_verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("size_bytes > 0", name="ck_evidence_size_positive"),
            sa.CheckConstraint("length(object_key) = 64", name="ck_evidence_object_key_length"),
            sa.CheckConstraint("length(checksum_sha256) = 64", name="ck_evidence_checksum_length"),
            sa.CheckConstraint("length(trim(retention_policy_id)) > 0", name="ck_evidence_retention_policy_id"),
            sa.CheckConstraint("content_type IN ('application/pdf', 'image/png', 'image/jpeg')", name="ck_evidence_content_type"),
            sa.CheckConstraint("scan_status = 'CLEAN'", name="ck_evidence_only_clean_rows"),
            sa.CheckConstraint("lifecycle_status IN ('ACTIVE', 'DELETE_FAILED', 'DELETED')", name="ck_evidence_lifecycle_status"),
            sa.CheckConstraint("deletion_attempts >= 0", name="ck_evidence_deletion_attempts"),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_evidence_tenant", ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["tenant_id", "case_id"], ["staff_cases.tenant_id", "staff_cases.id"], name="fk_evidence_tenant_case", ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["tenant_id", "created_by"], ["staff_users.tenant_id", "staff_users.id"], name="fk_evidence_tenant_creator", ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("object_key", name="uq_evidence_object_key"),
        )
    inspector = sa.inspect(op.get_bind())
    for name, columns in (
        ("ix_evidence_objects_tenant_id", ["tenant_id"]),
        ("ix_evidence_objects_case_id", ["case_id"]),
        ("ix_evidence_tenant_case_created", ["tenant_id", "case_id", "created_at"]),
        ("ix_evidence_retention", ["retention_until", "legal_hold", "lifecycle_status"]),
    ):
        if not inspector.has_index("evidence_objects", name):
            op.create_index(name, "evidence_objects", columns)
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE evidence_objects ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE evidence_objects FORCE ROW LEVEL SECURITY")
        op.execute("DROP POLICY IF EXISTS evidence_tenant_scope ON evidence_objects")
        op.execute("""
            CREATE POLICY evidence_tenant_scope ON evidence_objects
            USING (tenant_id = NULLIF(current_setting('scmirn.tenant_id', true), ''))
            WITH CHECK (tenant_id = NULLIF(current_setting('scmirn.tenant_id', true), ''))
        """)


def downgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP POLICY IF EXISTS evidence_tenant_scope ON evidence_objects")
        op.execute("ALTER TABLE evidence_objects NO FORCE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE evidence_objects DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_evidence_retention", table_name="evidence_objects")
    op.drop_index("ix_evidence_tenant_case_created", table_name="evidence_objects")
    op.drop_index("ix_evidence_objects_case_id", table_name="evidence_objects")
    op.drop_index("ix_evidence_objects_tenant_id", table_name="evidence_objects")
    op.drop_table("evidence_objects")
