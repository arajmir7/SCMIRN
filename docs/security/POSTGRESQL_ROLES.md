# PostgreSQL role provisioning

The web service and migration job must use different PostgreSQL credentials.
The production Compose migration service uses
`SCMIRN_MIGRATION_DATABASE_URL`; the web service uses `DATABASE_URL` and must
connect as `scmirn_app`. The app validates its role at startup and exits if it
has create privileges, owns public-schema objects, inherits another role, can
read protected audit tables, or if staff RLS is not both enabled and forced.

## Roles

| Role | Use | Privilege boundary |
| --- | --- | --- |
| `scmirn_migrator` | One-shot Alembic migration | Owns `public`; no superuser, role creation, database creation, replication or RLS bypass. |
| `scmirn_app` | Flask web process | SELECT on five global registry tables; narrowly enumerated staff workflow grants; no DDL, temporary tables, audit content reads, or access to quarantined legacy tables. |
| `scmirn_worker` | Future background worker | No table grants until a specific worker job and data boundary are implemented. |
| `scmirn_auditor` | Separate audit verifier | SELECT only on audit/history tables. |

The provisioner itself is an operator credential. Do not put its URL or
passwords in the application container, source tree, or `DATABASE_URL`.
Provide these environment values from a secret manager or protected operator
shell: `SCMIRN_ROLE_PROVISIONER_DATABASE_URL`, `SCMIRN_MIGRATOR_DB_PASSWORD`,
`SCMIRN_APP_DB_PASSWORD`, `SCMIRN_WORKER_DB_PASSWORD`, and
`SCMIRN_AUDITOR_DB_PASSWORD`. Passwords must be at least 32 characters. Role
names can be overridden with `SCMIRN_MIGRATOR_DB_ROLE`,
`SCMIRN_APP_DB_ROLE`, `SCMIRN_WORKER_DB_ROLE`, and
`SCMIRN_AUDITOR_DB_ROLE`; if changed, update the database URLs and app role
setting to match.

## Bootstrap sequence for a new dedicated database

1. Run `python scripts/provision_postgres_roles.py` against the empty SCMIRN
   database. It creates the four bounded login roles and gives the migrator
   ownership of the `public` schema.
2. Configure `SCMIRN_MIGRATION_DATABASE_URL` with the migrator credential and
   run the one-shot migration job. It runs with application traffic disabled.
3. Run the role provisioner again. This applies table-level grants and creates
   the `scmirn_audit_head()` security-definer function owned by the migrator.
   The web role gets only the chain-head hash and cannot select audit content;
   it can see the generated sequence number returned by its own audit insert.
4. Configure `DATABASE_URL` with the app credential. Keep
   `STAFF_API_ENABLED=false` until the staff deployment, MFA key, authorization
   policy and tenant ownership are separately reviewed.
5. Start the application. It checks `current_user`, role flags/memberships,
   ownership, audit-table read access, and all nine forced staff RLS tables.
6. Run audit verification as a separate operator command with
   `SCMIRN_AUDITOR_DATABASE_URL` pointing to the read-only auditor role. Never
   pass that credential to the web process; the CLI prints only the chain
   verification summary.

The provisioner is idempotent for roles, grants and the function. It refuses
to grant access if public-schema objects already belong to another role; do
not bypass that check with a blanket ownership transfer. Existing databases
need a separately reviewed ownership-adoption plan. This repository has no
production database credentials and no production database was changed.

## Limits

`scmirn_app` receives no grants for legacy subject records, route decisions,
infrastructure operations, or legacy audit data. Production triage is
therefore disabled until its stored decision and audit model has enforceable
subject/tenant isolation. `scmirn_worker` has no scheduled purge access yet.
The tenant RLS policies use transaction-local PostgreSQL settings set by the
application; they constrain ordinary app queries but do not protect against a
fully compromised application process that can issue arbitrary SQL. A future
hostile-threat boundary needs a database-verifiable identity context, not a
caller-controlled tenant setting alone.
