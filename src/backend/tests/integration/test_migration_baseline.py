from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy.exc import IntegrityError

import app as app_package
from app import create_app
from app.config import TestingConfig, config_by_name
from app.extensions import db
from app.infrastructure.database.models import UserORM
from app.source_routing.audit_models import AuditEvent  # noqa: F401 - register metadata
from app.source_routing.models import (  # noqa: F401 - register metadata
    Authority,
    GovernmentService,
    OfficialSource,
    RouteDecision,
    RouteRule,
)


MIGRATIONS = Path(__file__).resolve().parents[2] / "app/infrastructure/database/migrations"
ROUTING_TABLES = {
    "official_sources",
    "authorities",
    "government_services",
    "government_service_sources",
    "route_rules",
    "route_decisions",
    "audit_events",
}


@pytest.fixture
def migration_app(tmp_path, monkeypatch):
    class MigrationTestConfig(TestingConfig):
        AUTO_CREATE_DB = False
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'migration.db'}"
        UPLOAD_FOLDER = str(tmp_path / "uploads")

    monkeypatch.setitem(config_by_name, "migration_test", MigrationTestConfig)
    monkeypatch.setattr(app_package, "init_database", lambda app: None)
    monkeypatch.setattr(app_package.app_config, "DATA_DIR", str(tmp_path / "data"))
    app = create_app("migration_test")
    with app.app_context():
        yield app
        db.session.remove()
        db.engine.dispose()


def _upgrade_to(revision):
    config = Config(str(MIGRATIONS / "alembic.ini"))
    config.set_main_option("script_location", str(MIGRATIONS))
    command.upgrade(config, revision)


def _upgrade_to_head():
    _upgrade_to("head")


def _assert_at_head():
    table_names = set(db.inspect(db.engine).get_table_names())
    assert table_names - {"alembic_version"} == set(db.metadata.tables)
    with db.engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version"
        ).scalar_one() == "20261002_04"
        staff_tables = {"tenants", "staff_users", "staff_mfa_factors", "staff_mfa_challenges", "staff_role_grants", "staff_sessions", "staff_cases", "staff_case_events", "staff_audit_events"}

        def include_object(obj, name, object_type, reflected, compare_to):
            if object_type == "table":
                return name in staff_tables
            table = getattr(obj, "table", None)
            return table is None or table.name in staff_tables

        migration_context = MigrationContext.configure(connection, opts={
            "target_metadata": db.metadata,
            "compare_type": True,
            "compare_server_default": True,
            "include_object": include_object,
        })
        assert compare_metadata(migration_context, db.metadata) == []


@pytest.mark.integration
@pytest.mark.parametrize("starting_schema", ["empty", "complete", "legacy_only"])
def test_migration_builds_head_and_preserves_existing_rows(
    migration_app, starting_schema
):
    if starting_schema != "empty":
        if starting_schema == "complete":
            db.metadata.create_all(db.engine)
        else:
            db.metadata.create_all(
                db.engine,
                tables=[
                    table
                    for table in db.metadata.sorted_tables
                    if table.name not in ROUTING_TABLES
                ]
            )
        db.session.add(
            UserORM(
                public_id="preserved-user",
                phone="+10000000001",
                email="migration@example.test",
                password_hash="test-only",
            )
        )
        db.session.commit()

    _upgrade_to_head()

    _assert_at_head()
    assert db.session.query(UserORM).count() == (0 if starting_schema == "empty" else 1)


@pytest.mark.integration
def test_migration_refuses_schema_drift_before_creating_tables(migration_app):
    with db.engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, phone VARCHAR(20))"
        )

    with pytest.raises(RuntimeError, match="differs from ORM metadata"):
        _upgrade_to_head()

    table_names = set(db.inspect(db.engine).get_table_names())
    assert table_names == {"users"}


@pytest.mark.integration
@pytest.mark.parametrize("legacy_status", ["UNVERIFIED", "UNAVAILABLE"])
def test_source_lifecycle_migration_translates_legacy_statuses(migration_app, legacy_status):
    _upgrade_to("20261002_01")
    with db.engine.begin() as connection:
        connection.exec_driver_sql(
            """
            INSERT INTO official_sources (
                id, source_key, version, authority, title, source_type,
                jurisdiction, canonical_url, retrieved_at, verification_status
            ) VALUES (
                'legacy-source', 'legacy-source', 1, 'Test authority',
                'Legacy source fixture', 'TEST', 'TEST',
                'https://example.test/source', '2026-10-01 00:00:00', ?
            )
            """,
            (legacy_status,),
        )

    _upgrade_to_head()

    with db.engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT verification_status FROM official_sources WHERE id = 'legacy-source'"
        ).scalar_one() == "DRAFT"
    with pytest.raises(IntegrityError):
        with db.engine.begin() as connection:
            connection.exec_driver_sql(
                """
                INSERT INTO official_sources (
                    id, source_key, version, authority, title, source_type,
                    jurisdiction, canonical_url, retrieved_at, verification_status
                ) VALUES (
                    'invalid-source', 'invalid-source', 1, 'Test authority',
                    'Invalid lifecycle fixture', 'TEST', 'TEST',
                    'https://example.test/source', '2026-10-02 00:00:00', 'UNAVAILABLE'
                )
                """
            )
