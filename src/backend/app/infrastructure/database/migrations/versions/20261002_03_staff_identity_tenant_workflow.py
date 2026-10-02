"""Add staff identity, tenant workflow, audit, and PostgreSQL tenant RLS.

Revision ID: 20261002_03
Revises: 20261002_02
"""
from alembic import op
import sqlalchemy as sa


revision = "20261002_03"
down_revision = "20261002_02"
branch_labels = None
depends_on = None


TENANT_TABLES = (
    "staff_users", "staff_mfa_factors", "staff_mfa_challenges",
    "staff_role_grants", "staff_sessions", "staff_cases",
    "staff_case_events", "staff_audit_events",
)


def _create_table(name, *args, **kwargs):
    if not sa.inspect(op.get_bind()).has_table(name):
        op.create_table(name, *args, **kwargs)


def _create_index(name, table, columns):
    if not sa.inspect(op.get_bind()).has_index(table, name):
        op.create_index(name, table, columns)


def upgrade():
    present = set(sa.inspect(op.get_bind()).get_table_names()) & (set(TENANT_TABLES) | {"tenants"})
    if present and present != (set(TENANT_TABLES) | {"tenants"}):
        raise RuntimeError("Staff identity migration refused: partial staff schema already exists.")
    _create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    _create_table(
        "staff_users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("failed_login_count", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "email", name="uq_staff_user_tenant_email"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_staff_user_tenant_id"),
        sa.CheckConstraint("failed_login_count >= 0", name="ck_staff_failed_login_count"),
    )
    _create_table(
        "staff_mfa_factors",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False, unique=True),
        sa.Column("secret_ciphertext", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("enrollment_token_hash", sa.String(64)),
        sa.Column("enrollment_expires_at", sa.DateTime(timezone=True)),
        sa.Column("last_totp_step", sa.BigInteger(), nullable=False),
        sa.Column("failed_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["tenant_id", "user_id"], ["staff_users.tenant_id", "staff_users.id"], name="fk_staff_mfa_factor_tenant_user", ondelete="CASCADE"),
        sa.CheckConstraint("failed_attempts >= 0", name="ck_staff_mfa_failed_attempts"),
    )
    _create_table(
        "staff_mfa_challenges",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "user_id"], ["staff_users.tenant_id", "staff_users.id"], name="fk_staff_mfa_challenge_tenant_user", ondelete="CASCADE"),
    )
    _create_table(
        "staff_role_grants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("granted_by", sa.String(36), sa.ForeignKey("staff_users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", "role", name="uq_staff_role_grant"),
        sa.CheckConstraint("role IN ('TENANT_ADMIN', 'CASE_OFFICER', 'SOURCE_REVIEWER', 'AUDITOR')", name="ck_staff_role_name"),
        sa.ForeignKeyConstraint(["tenant_id", "user_id"], ["staff_users.tenant_id", "staff_users.id"], name="fk_staff_role_grant_tenant_user", ondelete="CASCADE"),
    )
    _create_table(
        "staff_sessions",
        sa.Column("session_hash", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("csrf_hash", sa.String(64), nullable=False),
        sa.Column("mfa_verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idle_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["tenant_id", "user_id"], ["staff_users.tenant_id", "staff_users.id"], name="fk_staff_session_tenant_user", ondelete="CASCADE"),
    )
    _create_table(
        "staff_cases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("case_ref", sa.String(24), nullable=False),
        sa.Column("case_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("assigned_user_id", sa.String(36), sa.ForeignKey("staff_users.id", ondelete="SET NULL")),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "case_ref", name="uq_staff_case_tenant_ref"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_staff_case_tenant_id"),
        sa.CheckConstraint("status IN ('OPEN', 'UNDER_REVIEW', 'ACTION_REQUIRED', 'RESOLVED', 'CLOSED')", name="ck_staff_case_status"),
        sa.CheckConstraint("priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')", name="ck_staff_case_priority"),
        sa.ForeignKeyConstraint(["tenant_id", "created_by"], ["staff_users.tenant_id", "staff_users.id"], name="fk_staff_case_creator_tenant_user", ondelete="RESTRICT"),
    )
    _create_table(
        "staff_case_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id", sa.String(36), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("from_status", sa.String(32)),
        sa.Column("to_status", sa.String(32)),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "case_id"], ["staff_cases.tenant_id", "staff_cases.id"], name="fk_staff_case_event_tenant_case", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "actor_id"], ["staff_users.tenant_id", "staff_users.id"], name="fk_staff_case_event_tenant_actor", ondelete="RESTRICT"),
    )
    _create_table(
        "staff_audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("staff_users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("object_type", sa.String(48), nullable=False),
        sa.Column("object_id", sa.String(64), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    for table in TENANT_TABLES:
        _create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])
    for table, column in (("staff_role_grants", "user_id"), ("staff_sessions", "user_id"), ("staff_cases", "assigned_user_id"), ("staff_cases", "created_by"), ("staff_case_events", "case_id")):
        _create_index(f"ix_{table}_{column}", table, [column])

    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE tenants FORCE ROW LEVEL SECURITY")
        op.execute("CREATE POLICY tenant_scope ON tenants USING (id = NULLIF(current_setting('scmirn.tenant_id', true), '')) WITH CHECK (id = NULLIF(current_setting('scmirn.tenant_id', true), ''))")
        # Tenant slug lookup is required before a tenant scope can be established
        # at login. The directory contains no user or case information.
        op.execute("CREATE POLICY tenant_directory_lookup ON tenants FOR SELECT USING (true)")
        for table in TENANT_TABLES:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
            if table == "staff_sessions":
                predicate = (
                    "session_hash = NULLIF(current_setting('scmirn.staff_session_hash', true), '') "
                    "OR (tenant_id = NULLIF(current_setting('scmirn.tenant_id', true), '') "
                    "AND user_id = NULLIF(current_setting('scmirn.staff_manage_user_id', true), ''))"
                )
            else:
                predicate = "tenant_id = NULLIF(current_setting('scmirn.tenant_id', true), '')"
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING ({predicate}) WITH CHECK ({predicate})")

        op.execute("""
            CREATE FUNCTION scmirn_reject_staff_history_mutation() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'staff history is append-only'; END;
            $$ LANGUAGE plpgsql;
        """)
        for table in ("staff_audit_events", "staff_case_events"):
            op.execute(f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION scmirn_reject_staff_history_mutation()")


def downgrade():
    if op.get_bind().dialect.name == "postgresql":
        for table in ("staff_audit_events", "staff_case_events"):
            op.execute(f"DROP TRIGGER IF EXISTS {table}_append_only ON {table}")
        op.execute("DROP FUNCTION IF EXISTS scmirn_reject_staff_history_mutation()")
        for table in reversed(TENANT_TABLES):
            op.execute(f"DROP POLICY IF EXISTS tenant_scope ON {table}")
            op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        op.execute("DROP POLICY IF EXISTS tenant_scope ON tenants")
        op.execute("DROP POLICY IF EXISTS tenant_directory_lookup ON tenants")
        op.execute("ALTER TABLE tenants NO FORCE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE tenants DISABLE ROW LEVEL SECURITY")
    for table in reversed(("staff_audit_events", "staff_case_events", "staff_cases", "staff_sessions", "staff_role_grants", "staff_mfa_challenges", "staff_mfa_factors", "staff_users", "tenants")):
        op.drop_table(table)
