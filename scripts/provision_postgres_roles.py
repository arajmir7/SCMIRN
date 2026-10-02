#!/usr/bin/env python3
"""Idempotently provision SCMIRN PostgreSQL identities and narrow grants.

Run only against the dedicated SCMIRN database with a database provisioner
credential. Run once before migrations and again after migrations; the migration
process must connect as ``scmirn_migrator`` and the web process as
``scmirn_app``. Credentials are read from the environment and never printed.
"""
from __future__ import annotations

import os
import re
import sys

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url


ROLE_ENV = {
    "migrator": ("SCMIRN_MIGRATOR_DB_ROLE", "SCMIRN_MIGRATOR_DB_PASSWORD", "scmirn_migrator", 3),
    "app": ("SCMIRN_APP_DB_ROLE", "SCMIRN_APP_DB_PASSWORD", "scmirn_app", 30),
    "worker": ("SCMIRN_WORKER_DB_ROLE", "SCMIRN_WORKER_DB_PASSWORD", "scmirn_worker", 5),
    "auditor": ("SCMIRN_AUDITOR_DB_ROLE", "SCMIRN_AUDITOR_DB_PASSWORD", "scmirn_auditor", 3),
}

GLOBAL_REFERENCE_TABLES = (
    "authorities",
    "government_service_sources",
    "government_services",
    "official_sources",
    "route_rules",
)
APP_TENANT_TABLE_GRANTS = {
    "audit_events": "INSERT",
    "tenants": "SELECT, INSERT",
    "staff_users": "SELECT, INSERT, UPDATE",
    "staff_mfa_factors": "SELECT, INSERT, UPDATE",
    "staff_mfa_challenges": "SELECT, INSERT, UPDATE, DELETE",
    "staff_role_grants": "SELECT, INSERT",
    "staff_sessions": "SELECT, INSERT, UPDATE, DELETE",
    "staff_cases": "SELECT, INSERT, UPDATE",
    "staff_case_events": "SELECT, INSERT",
    # Application writes metadata audit rows; reads go through the protected
    # verification/head paths and are granted to the separate auditor role.
    "staff_audit_events": "INSERT",
}
AUDIT_TABLES = ("audit_events", "staff_audit_events", "srs_audit_logs")


def _settings():
    provisioner_url = os.environ.get("SCMIRN_ROLE_PROVISIONER_DATABASE_URL", "")
    if not provisioner_url:
        raise ValueError("SCMIRN_ROLE_PROVISIONER_DATABASE_URL is required")
    roles = {}
    for purpose, (role_env, password_env, fallback, limit) in ROLE_ENV.items():
        name = os.environ.get(role_env, fallback)
        password = os.environ.get(password_env, "")
        if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]{0,62}", name):
            raise ValueError(f"{role_env} must be a PostgreSQL identifier")
        if len(password) < 32 or "\x00" in password:
            raise ValueError(f"{password_env} must contain at least 32 characters")
        roles[purpose] = (name, password, limit)
    if len({entry[0] for entry in roles.values()}) != len(roles):
        raise ValueError("The four PostgreSQL role names must be distinct")
    if len({entry[1] for entry in roles.values()}) != len(roles):
        raise ValueError("The four PostgreSQL role passwords must be different")
    return provisioner_url, roles


def _existing_public_owners(connection):
    return connection.execute("""
        SELECT c.relname, pg_get_userbyid(c.relowner) AS owner
          FROM pg_class AS c
          JOIN pg_namespace AS n ON n.oid = c.relnamespace
         WHERE n.nspname = 'public'
           AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
         ORDER BY c.relname
    """).fetchall()


def _psycopg_conninfo(value):
    url = make_url(value)
    if url.drivername not in {"postgresql+psycopg", "postgresql"}:
        raise ValueError("role provisioner URL must use PostgreSQL with psycopg")
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


def provision():
    provisioner_url, roles = _settings()
    with psycopg.connect(_psycopg_conninfo(provisioner_url), autocommit=True) as connection:
        app_name = roles["app"][0]
        migrator_name = roles["migrator"][0]
        existing = _existing_public_owners(connection)
        mismatched = [name for name, owner in existing if owner != migrator_name]
        if mismatched:
            raise RuntimeError(
                "Public schema objects are not owned by the migration role; "
                "review ownership adoption before provisioning grants."
            )

        for purpose, (name, password, connection_limit) in roles.items():
            attrs = sql.SQL(
                "LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE "
                "NOREPLICATION NOBYPASSRLS CONNECTION LIMIT {} PASSWORD {}"
            ).format(sql.Literal(connection_limit), sql.Literal(password))
            found = connection.execute(
                "SELECT 1 FROM pg_roles WHERE rolname = %s", (name,)
            ).fetchone()
            if found:
                connection.execute(sql.SQL("ALTER ROLE {} ").format(sql.Identifier(name)) + attrs)
            else:
                connection.execute(sql.SQL("CREATE ROLE {} ").format(sql.Identifier(name)) + attrs)

        # Remove inherited roles and stale grants before applying the narrow
        # role contract again. This also repairs accidental broad grants from
        # an earlier provisioning run.
        for purpose in ("migrator", "app", "worker", "auditor"):
            member = roles[purpose][0]
            inherited = connection.execute(
                "SELECT granted.rolname FROM pg_auth_members AS m "
                "JOIN pg_roles AS granted ON granted.oid = m.roleid "
                "JOIN pg_roles AS member_role ON member_role.oid = m.member "
                "WHERE member_role.rolname = %s",
                (member,),
            ).fetchall()
            for (granted_role,) in inherited:
                connection.execute(sql.SQL("REVOKE {} FROM {}").format(
                    sql.Identifier(granted_role), sql.Identifier(member),
                ))

        # Public access is removed only from this dedicated database/schema.
        database = connection.execute("SELECT current_database()").fetchone()[0]
        connection.execute(sql.SQL("REVOKE CONNECT, TEMPORARY ON DATABASE {} FROM PUBLIC").format(sql.Identifier(database)))
        connection.execute(sql.SQL("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
        connection.execute(sql.SQL("REVOKE ALL ON DATABASE {} FROM {}, {}, {}, {}").format(
            sql.Identifier(database), *[
                sql.Identifier(roles[purpose][0])
                for purpose in ("migrator", "app", "worker", "auditor")
            ]
        ))
        connection.execute(sql.SQL("REVOKE CREATE ON SCHEMA public FROM {}, {}, {}").format(*[
            sql.Identifier(roles[purpose][0]) for purpose in ("app", "worker", "auditor")
        ]))
        connection.execute(sql.SQL("ALTER SCHEMA public OWNER TO {}").format(sql.Identifier(migrator_name)))
        connection.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
            sql.Identifier(database), sql.Identifier(migrator_name),
        ))
        for purpose in ("app", "worker", "auditor"):
            connection.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(database), sql.Identifier(roles[purpose][0]),
            ))
        connection.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}, {}, {}").format(*[
            sql.Identifier(roles[purpose][0]) for purpose in ("app", "worker", "auditor")
        ]))
        connection.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC")
        connection.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC")
        runtime_roles = [sql.Identifier(roles[purpose][0]) for purpose in ("app", "worker", "auditor")]
        connection.execute(sql.SQL("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {}, {}, {}").format(*runtime_roles))
        connection.execute(sql.SQL("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM {}, {}, {}").format(*runtime_roles))
        connection.execute(sql.SQL(
            "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA public REVOKE ALL ON TABLES FROM PUBLIC"
        ).format(sql.Identifier(migrator_name)))
        connection.execute(sql.SQL(
            "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA public REVOKE ALL ON SEQUENCES FROM PUBLIC"
        ).format(sql.Identifier(migrator_name)))

        present = {
            row[0] for row in connection.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ).fetchall()
        }
        for table in GLOBAL_REFERENCE_TABLES:
            if table in present:
                connection.execute(sql.SQL("GRANT SELECT ON TABLE public.{} TO {}").format(
                    sql.Identifier(table), sql.Identifier(app_name),
                ))
        for table, privileges in APP_TENANT_TABLE_GRANTS.items():
            if table in present:
                connection.execute(sql.SQL("GRANT {} ON TABLE public.{} TO {}").format(
                    sql.SQL(privileges), sql.Identifier(table), sql.Identifier(app_name),
                ))
        if "audit_events" in present:
            # SQLAlchemy's INSERT ... RETURNING sequence needs visibility of
            # this one generated key column, not SELECT access to event data.
            connection.execute(sql.SQL(
                "GRANT SELECT (sequence) ON TABLE public.audit_events TO {}"
            ).format(sql.Identifier(app_name)))
        for table in (*AUDIT_TABLES, "staff_case_events"):
            if table in present:
                connection.execute(sql.SQL("GRANT SELECT ON TABLE public.{} TO {}").format(
                    sql.Identifier(table), sql.Identifier(roles["auditor"][0]),
                ))
        for table, policy_name in (
            ("staff_audit_events", "scmirn_auditor_read_staff_audit"),
            ("staff_case_events", "scmirn_auditor_read_case_events"),
        ):
            if table in present:
                connection.execute(sql.SQL("DROP POLICY IF EXISTS {} ON public.{}").format(
                    sql.Identifier(policy_name), sql.Identifier(table),
                ))
                connection.execute(sql.SQL(
                    "CREATE POLICY {} ON public.{} FOR SELECT TO {} USING (true)"
                ).format(
                    sql.Identifier(policy_name), sql.Identifier(table),
                    sql.Identifier(roles["auditor"][0]),
                ))
        if "audit_events" in present:
            audit_sequence = connection.execute(
                "SELECT pg_get_serial_sequence('public.audit_events', 'sequence')"
            ).fetchone()[0]
            if audit_sequence:
                sequence_schema, sequence_name = audit_sequence.split(".", 1)
                sequence_name = sequence_name.strip('"')
                connection.execute(sql.SQL(
                    "GRANT USAGE ON SEQUENCE {}.{} TO {}"
                ).format(
                    sql.Identifier(sequence_schema), sql.Identifier(sequence_name),
                    sql.Identifier(app_name),
                ))

        if "audit_events" in present:
            connection.execute("""
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
            connection.execute(sql.SQL(
                "ALTER FUNCTION public.scmirn_audit_head() OWNER TO {}"
            ).format(sql.Identifier(migrator_name)))
            connection.execute("REVOKE ALL ON FUNCTION public.scmirn_audit_head() FROM PUBLIC")
            connection.execute(sql.SQL(
                "GRANT EXECUTE ON FUNCTION public.scmirn_audit_head() TO {}"
            ).format(sql.Identifier(app_name)))

    return {purpose: name for purpose, (name, _password, _limit) in roles.items()}


if __name__ == "__main__":
    try:
        roles = provision()
    except Exception as exc:
        # Driver exceptions may include connection details; only the type is
        # surfaced so credentials and private hostnames stay out of logs.
        print(f"PostgreSQL role provisioning failed ({type(exc).__name__}).", file=sys.stderr)
        raise SystemExit(1)
    print("PostgreSQL roles and explicit grants provisioned: " + ", ".join(sorted(roles)))
