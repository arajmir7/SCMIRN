from logging.config import fileConfig

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic import context
from flask import current_app
import sqlalchemy as sa


config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

migrate_ext = current_app.extensions["migrate"]
db = migrate_ext.db
target_metadata = db.metadata

ROUTING_TABLES = {
    "official_sources",
    "authorities",
    "government_services",
    "government_service_sources",
    "route_rules",
    "route_decisions",
    "audit_events",
}
ROUTING_REVISION = "20261001_01"


def _existing_schema_differences(connection, existing_tables):
    """Return structural differences for existing ORM tables only."""
    def include_object(obj, name, object_type, reflected, compare_to):
        if object_type == "table":
            return name in existing_tables
        if (
            object_type.endswith("constraint")
            and name == "ck_official_source_status"
            and getattr(getattr(obj, "table", None), "name", None) == "official_sources"
        ):
            # This one check has a forward-only data migration for prior
            # UNVERIFIED/UNAVAILABLE rows; all other structure remains strict.
            return False
        table = getattr(obj, "table", None)
        return table is None or table.name in existing_tables

    migration_context = MigrationContext.configure(
        connection,
        opts={
            "target_metadata": target_metadata,
            "compare_type": True,
            "compare_server_default": True,
            "include_object": include_object,
        },
    )
    return compare_metadata(migration_context, target_metadata)


def _prepare_existing_schema(connection):
    """Safely adopt exact legacy schemas without replaying CREATE TABLE DDL.

    Unversioned schemas created by the former development ``create_all`` path
    are accepted only when every existing table matches current ORM metadata.
    A schema with all routing tables is stamped at the routing revision.
    Partial routing migrations and drift
    fail closed before any application migration runs.
    """
    inspector = sa.inspect(connection)
    all_tables = set(inspector.get_table_names())
    has_version_table = "alembic_version" in all_tables
    existing_tables = all_tables - {"alembic_version"}
    migration_context = MigrationContext.configure(connection)
    current_revision = migration_context.get_current_revision() if has_version_table else None

    if not existing_tables:
        return

    known_tables = set(target_metadata.tables)
    unknown_tables = existing_tables - known_tables
    if unknown_tables:
        raise RuntimeError(
            "Database migration refused: existing tables are not represented "
            "in ORM metadata: " + ", ".join(sorted(unknown_tables))
        )

    needs_compatibility_check = current_revision is None
    if not needs_compatibility_check:
        return

    differences = _existing_schema_differences(connection, existing_tables)
    if differences:
        preview = "; ".join(repr(item) for item in differences[:5])
        raise RuntimeError(
            "Database migration refused before applying DDL: existing table "
            "structure differs from ORM metadata. Resolve the schema drift "
            "with a reviewed migration first. Differences: " + preview
        )

    if current_revision is not None:
        return

    present_routing_tables = existing_tables & ROUTING_TABLES
    if present_routing_tables and present_routing_tables != ROUTING_TABLES:
        raise RuntimeError(
            "Database migration refused: partial source-routing schema found "
            "without a migration revision. Restore a consistent backup or "
            "apply a reviewed repair migration."
        )

    if present_routing_tables == ROUTING_TABLES:
        script = ScriptDirectory.from_config(config)
        # Keep post-routing revisions runnable for exact schemas created by
        # the previous ORM auto-create path (including current ORM metadata).
        stamp_revision = ROUTING_REVISION
        if connection.in_transaction():
            connection.commit()
        with connection.begin():
            MigrationContext.configure(connection).stamp(script, stamp_revision)
        connection.commit()


def run_migrations_offline():
    url = current_app.config["SQLALCHEMY_DATABASE_URI"]
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,
        transactional_ddl=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with db.engine.connect() as connection:
        _prepare_existing_schema(connection)
        # Inspector reads start an implicit SQLAlchemy transaction. Close the
        # read-only preflight transaction before Alembic opens its DDL scope;
        # otherwise SQLite can roll back revision bookkeeping on connection
        # close even though the migration steps appeared to run successfully.
        if connection.in_transaction():
            connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,
            transactional_ddl=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
