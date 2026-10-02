"""Adopt the explicit DRAFT/VERIFIED/SUPERSEDED/REVOKED source lifecycle.

Revision ID: 20261002_02
Revises: 20261002_01
"""
from alembic import op
import sqlalchemy as sa


revision = "20261002_02"
down_revision = "20261002_01"
branch_labels = None
depends_on = None


TRANSITION_STATUS_CHECK = (
    "verification_status IN ('UNVERIFIED', 'VERIFIED', 'SUPERSEDED', "
    "'UNAVAILABLE', 'DRAFT', 'REVOKED')"
)
CURRENT_STATUS_CHECK = "verification_status IN ('DRAFT', 'VERIFIED', 'SUPERSEDED', 'REVOKED')"


def upgrade():
    # Widen first so the data migration can run under the existing constraint,
    # then narrow to the explicit lifecycle after legacy states are translated.
    with op.batch_alter_table("official_sources") as batch:
        batch.drop_constraint("ck_official_source_status", type_="check")
        batch.create_check_constraint("ck_official_source_status", TRANSITION_STATUS_CHECK)

    op.execute(sa.text(
        "UPDATE official_sources "
        "SET verification_status = 'DRAFT' "
        "WHERE verification_status IN ('UNVERIFIED', 'UNAVAILABLE')"
    ))

    with op.batch_alter_table("official_sources") as batch:
        batch.drop_constraint("ck_official_source_status", type_="check")
        batch.create_check_constraint("ck_official_source_status", CURRENT_STATUS_CHECK)


def downgrade():
    raise RuntimeError(
        "Source lifecycle downgrade is blocked: REVOKED and DRAFT states "
        "cannot be safely represented by the legacy status constraint."
    )
