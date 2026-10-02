"""Provide a narrow audit-chain head function for the application role.

Revision ID: 20261002_04
Revises: 20261002_03
"""
from alembic import op


revision = "20261002_04"
down_revision = "20261002_03"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute("""
        CREATE OR REPLACE FUNCTION public.scmirn_audit_head()
        RETURNS text
        LANGUAGE sql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
            SELECT event_hash FROM public.audit_events
             ORDER BY sequence DESC LIMIT 1
        $$
    """)
    op.execute("REVOKE ALL ON FUNCTION public.scmirn_audit_head() FROM PUBLIC")


def downgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP FUNCTION IF EXISTS public.scmirn_audit_head()")
