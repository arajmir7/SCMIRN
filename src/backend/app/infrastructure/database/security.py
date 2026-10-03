"""Fail-closed checks for the production PostgreSQL runtime identity."""

from sqlalchemy import text


TENANT_RLS_TABLES = (
    "tenants",
    "staff_users",
    "staff_mfa_factors",
    "staff_mfa_challenges",
    "staff_role_grants",
    "staff_sessions",
    "staff_cases",
    "staff_case_events",
    "staff_audit_events",
    "evidence_objects",
)

AUDIT_TABLES_HIDDEN_FROM_APP = (
    "audit_events",
    "staff_audit_events",
    "srs_audit_logs",
)


def validate_production_runtime_role(
    connection, expected_role="scmirn_app", staff_api_enabled=False
):
    """Require a non-owner, non-privileged role with forced staff RLS.

    This check intentionally applies to the database identity used by the web
    process. Migrations must run in a separate one-shot process as the
    ``scmirn_migrator`` role.
    """
    identity = connection.execute(text("""
        SELECT current_user AS role_name,
               r.rolcanlogin, r.rolsuper, r.rolcreatedb, r.rolcreaterole,
               r.rolbypassrls, r.rolreplication,
               has_database_privilege(current_user, current_database(), 'CREATE') AS can_create_database_objects,
               has_database_privilege(current_user, current_database(), 'TEMPORARY') AS can_create_temporary_objects,
               has_schema_privilege(current_user, 'public', 'CREATE') AS can_create_schema_objects
          FROM pg_roles AS r
         WHERE r.rolname = current_user
    """)).mappings().one_or_none()
    if identity is None:
        raise RuntimeError("Production database role validation failed: current role was not found.")

    if identity["role_name"] != expected_role:
        raise RuntimeError("Production database role validation failed: DATABASE_URL must use the configured application role.")
    if not identity["rolcanlogin"] or any(identity[name] for name in (
        "rolsuper", "rolcreatedb", "rolcreaterole", "rolbypassrls", "rolreplication",
        "can_create_database_objects", "can_create_temporary_objects", "can_create_schema_objects",
    )):
        raise RuntimeError("Production database role validation failed: application role has a privileged capability.")

    memberships = connection.execute(text("""
        SELECT r.rolname
          FROM pg_roles AS r
         WHERE r.rolname <> current_user
           AND pg_has_role(current_user, r.oid, 'MEMBER')
         ORDER BY r.rolname
    """)).scalars().all()
    if memberships:
        raise RuntimeError("Production database role validation failed: application role inherits another PostgreSQL role.")

    owned_objects = connection.execute(text("""
        SELECT c.relname
          FROM pg_class AS c
          JOIN pg_namespace AS n ON n.oid = c.relnamespace
         WHERE n.nspname = 'public'
           AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
           AND pg_get_userbyid(c.relowner) = current_user
        UNION ALL
        SELECT n.nspname
          FROM pg_namespace AS n
         WHERE n.nspname = 'public'
           AND pg_get_userbyid(n.nspowner) = current_user
    """)).scalars().all()
    if owned_objects:
        raise RuntimeError("Production database role validation failed: application role owns schema objects.")

    missing_rls = connection.execute(text("""
        SELECT required.table_name
          FROM unnest(CAST(:table_names AS text[])) AS required(table_name)
          LEFT JOIN pg_class AS c ON c.relname = required.table_name
                                AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
         WHERE c.oid IS NULL OR NOT c.relrowsecurity OR NOT c.relforcerowsecurity
            OR NOT EXISTS (
                SELECT 1 FROM pg_policies AS p
                 WHERE p.schemaname = 'public' AND p.tablename = required.table_name
            )
         ORDER BY required.table_name
    """), {"table_names": list(TENANT_RLS_TABLES)}).scalars().all()
    if missing_rls:
        raise RuntimeError("Production database role validation failed: tenant RLS is missing or not forced.")

    audit_reads = connection.execute(text("""
        SELECT table_name
          FROM unnest(CAST(:table_names AS text[])) AS required(table_name)
         WHERE has_table_privilege(current_user, 'public.' || table_name, 'SELECT')
         ORDER BY table_name
    """), {"table_names": list(AUDIT_TABLES_HIDDEN_FROM_APP)}).scalars().all()
    if audit_reads:
        raise RuntimeError("Production database role validation failed: application role can read a protected audit table.")

    audit_capabilities = connection.execute(text("""
        SELECT has_table_privilege(current_user, 'public.audit_events', 'INSERT') AS can_append_audit,
               has_function_privilege(current_user, 'public.scmirn_audit_head()', 'EXECUTE') AS can_read_audit_head
    """)).mappings().one()
    if not audit_capabilities["can_append_audit"] or not audit_capabilities["can_read_audit_head"]:
        raise RuntimeError(
            "Production database role validation failed: protected audit append "
            f"capabilities are incomplete (insert={audit_capabilities['can_append_audit']}, "
            f"head={audit_capabilities['can_read_audit_head']})."
        )

    if staff_api_enabled:
        required_privileges = {
            "tenants": ("SELECT", "INSERT"),
            "staff_users": ("SELECT", "INSERT", "UPDATE"),
            "staff_mfa_factors": ("SELECT", "INSERT", "UPDATE"),
            "staff_mfa_challenges": ("SELECT", "INSERT", "UPDATE", "DELETE"),
            "staff_role_grants": ("SELECT", "INSERT"),
            "staff_sessions": ("SELECT", "INSERT", "UPDATE", "DELETE"),
            "staff_cases": ("SELECT", "INSERT", "UPDATE"),
            "staff_case_events": ("SELECT", "INSERT"),
            "staff_audit_events": ("INSERT",),
            "evidence_objects": ("SELECT", "INSERT", "UPDATE", "DELETE"),
        }
        missing_privileges = []
        for table, privileges in required_privileges.items():
            for privilege in privileges:
                allowed = connection.execute(text(
                    "SELECT has_table_privilege(current_user, :table_name, :privilege)"
                ), {"table_name": f"public.{table}", "privilege": privilege}).scalar_one()
                if not allowed:
                    missing_privileges.append(table)
                    break
        if missing_privileges:
            raise RuntimeError("Production database role validation failed: enabled staff APIs lack required workflow grants.")

    return identity["role_name"]
