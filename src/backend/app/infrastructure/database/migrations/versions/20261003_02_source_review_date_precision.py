"""Preserve catalog review dates without inventing timestamps.

Revision ID: 20261003_02
Revises: 20261003_01
"""
from datetime import date

from alembic import op
import sqlalchemy as sa


revision = "20261003_02"
down_revision = "20261003_01"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    source_columns = {column["name"] for column in inspector.get_columns("official_sources")}
    service_columns = {column["name"] for column in inspector.get_columns("government_services")}
    if "reviewed_on" not in source_columns:
        op.add_column("official_sources", sa.Column("reviewed_on", sa.Date(), nullable=True))
    if "verified_on" not in source_columns:
        op.add_column("official_sources", sa.Column("verified_on", sa.Date(), nullable=True))
    if "last_verified_on" not in service_columns:
        op.add_column("government_services", sa.Column("last_verified_on", sa.Date(), nullable=True))

    with op.batch_alter_table("official_sources") as batch:
        batch.alter_column("retrieved_at", existing_type=sa.DateTime(), nullable=True)

    bind = op.get_bind()
    review_date = date(2026, 10, 2)
    update_sources = sa.text(
        """
        UPDATE official_sources
           SET retrieved_at = NULL,
               verified_at = NULL,
               reviewed_on = :review_date,
               verified_on = CASE WHEN verification_status = 'VERIFIED' THEN :review_date ELSE NULL END
         WHERE parser_version = 'official-catalog-v1'
        """
    ).bindparams(sa.bindparam("review_date", type_=sa.Date()))
    bind.execute(update_sources, {"review_date": review_date})

    update_services = sa.text(
        """
        UPDATE government_services
           SET last_verified = NULL,
               last_verified_on = CASE
                   WHEN NOT EXISTS (
                       SELECT 1
                         FROM government_service_sources AS links
                         JOIN official_sources AS sources ON sources.id = links.source_id
                        WHERE links.service_version_id = government_services.id
                          AND (
                              sources.parser_version <> 'official-catalog-v1'
                              OR sources.verification_status <> 'VERIFIED'
                          )
                   )
                   AND EXISTS (
                       SELECT 1 FROM government_service_sources AS links
                        WHERE links.service_version_id = government_services.id
                   )
                   THEN :review_date
                   ELSE NULL
               END
         WHERE id IN (
             SELECT service_version_id
               FROM government_service_sources AS links
               JOIN official_sources AS sources ON sources.id = links.source_id
              WHERE sources.parser_version = 'official-catalog-v1'
         )
        """
    ).bindparams(sa.bindparam("review_date", type_=sa.Date()))
    bind.execute(update_services, {"review_date": review_date})


def downgrade():
    bind = op.get_bind()
    has_date_only_evidence = bind.execute(sa.text(
        "SELECT 1 FROM official_sources WHERE reviewed_on IS NOT NULL OR verified_on IS NOT NULL LIMIT 1"
    )).first()
    has_service_review_date = bind.execute(sa.text(
        "SELECT 1 FROM government_services WHERE last_verified_on IS NOT NULL LIMIT 1"
    )).first()
    has_null_retrieval_timestamp = bind.execute(sa.text(
        "SELECT 1 FROM official_sources WHERE retrieved_at IS NULL LIMIT 1"
    )).first()
    if has_date_only_evidence or has_service_review_date or has_null_retrieval_timestamp:
        raise RuntimeError(
            "Downgrade blocked: date-only or unknown source-review evidence "
            "cannot be represented as precise timestamps without inventing data."
        )

    op.drop_column("government_services", "last_verified_on")
    op.drop_column("official_sources", "verified_on")
    op.drop_column("official_sources", "reviewed_on")
    with op.batch_alter_table("official_sources") as batch:
        batch.alter_column("retrieved_at", existing_type=sa.DateTime(), nullable=False)
