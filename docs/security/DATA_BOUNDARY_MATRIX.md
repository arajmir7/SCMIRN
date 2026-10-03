# PostgreSQL data boundary matrix

Current implementation/test status: see
[`PHASE3_IMPLEMENTATION_STATUS.md`](PHASE3_IMPLEMENTATION_STATUS.md).

Inventory date: 2026-10-03. The inventory is generated from the 35 mapped
SQLAlchemy tables at Alembic head `20261003_02`. The source-review precision
revision adds three date fields; every mapped table appears
below. `LEGACY_UNCLASSIFIED` is an explicit quarantine classification: the
table is known, its data sensitivity is recorded, and production app/worker
grants are withheld until a usable subject, tenant, or jurisdiction boundary
has been migrated and tested.

## Classification totals

| Classification | Tables | Runtime treatment |
| --- | ---: | --- |
| `GLOBAL_REFERENCE` | 5 | App can read; only migration role can modify. |
| `TENANT_SCOPED` | 4 | Forced PostgreSQL RLS; app workflow grants only. |
| `SUBJECT_SCOPED` | 0 | No legacy table currently has a complete, enforced subject boundary. |
| `SECURITY_SCOPED` | 14 | Staff secrets use forced RLS; other tables have no app/worker grants. |
| `AUDIT_SCOPED` | 3 | App cannot read audit rows; auditor is read-only; scoped staff audit writes remain tenant-filtered. |
| `LEGACY_UNCLASSIFIED` | 9 | Quarantined; no application or worker table grants. |
| **Total** | **35** | No mapped table is omitted. |

## Table inventory

| Table | Classification | Data and purpose | Enforced boundary and application access |
| --- | --- | --- | --- |
| `authorities` | `GLOBAL_REFERENCE` | Public-authority names, levels, and jurisdictions | App `SELECT`; writes reserved to migrations/review tooling. |
| `government_service_sources` | `GLOBAL_REFERENCE` | Join from service versions to official source versions | App `SELECT`; writes reserved to migrations/review tooling. |
| `government_services` | `GLOBAL_REFERENCE` | Published service descriptions, eligibility, channels, and scope | App `SELECT`; writes reserved to migrations/review tooling. |
| `official_sources` | `GLOBAL_REFERENCE` | Official URLs, source hashes, verification and version history | App `SELECT`; writes reserved to migrations/review tooling. |
| `route_rules` | `GLOBAL_REFERENCE` | Versioned deterministic routing rules | App `SELECT`; writes reserved to migrations/review tooling. |
| `tenants` | `TENANT_SCOPED` | Staff organization directory | Forced RLS; tenant lookup policy deliberately exposes only tenant IDs/slugs/display names for login. App may select and create through the operator path. |
| `staff_cases` | `TENANT_SCOPED` | Bounded metadata-only staff cases | Forced tenant RLS, composite tenant/user references; app `SELECT/INSERT/UPDATE`. |
| `staff_case_events` | `TENANT_SCOPED` | Case status history | Forced tenant RLS and append-only trigger; app `SELECT/INSERT`, auditor `SELECT`. |
| `evidence_objects` | `TENANT_SCOPED` | Checksummed metadata for restricted evidence; bytes live in a private object store | Forced tenant RLS; composite tenant/case and tenant/creator foreign keys; only clean scanned records can be inserted. Evidence routes remain outside the production API allowlist. |
| `staff_users` | `SECURITY_SCOPED` | Staff identities and password hashes | Forced tenant RLS; app `SELECT/INSERT/UPDATE`; no app delete. |
| `staff_mfa_factors` | `SECURITY_SCOPED` | Encrypted TOTP factors and enrollment state | Forced tenant RLS; app `SELECT/INSERT/UPDATE`. |
| `staff_mfa_challenges` | `SECURITY_SCOPED` | Short-lived login challenges | Forced tenant RLS; app `SELECT/INSERT/UPDATE/DELETE`. |
| `staff_role_grants` | `SECURITY_SCOPED` | Staff role grants | Forced tenant RLS; app `SELECT/INSERT`; role administration remains constrained by API policy. |
| `staff_sessions` | `SECURITY_SCOPED` | Hashed sessions, CSRF hashes, expiry and revocation | Forced tenant RLS plus exact-session hash policy; app `SELECT/INSERT/UPDATE/DELETE`. |
| `audit_events` | `AUDIT_SCOPED` | Hash-chained routing and retention metadata | No RLS in this schema. App has `INSERT`, `SELECT` on the generated sequence number only (needed for `INSERT ... RETURNING`), and execute-only access to a function returning the chain head; it cannot read audit content. Auditor has read-only access. |
| `staff_audit_events` | `AUDIT_SCOPED` | Staff action metadata | Forced tenant RLS and append-only trigger; app `INSERT` only; auditor `SELECT`. |
| `srs_audit_logs` | `AUDIT_SCOPED` | Legacy asset/work-order audit records | No RLS; auditor read-only; app/worker have no grants. |
| `blockchain_tx` | `SECURITY_SCOPED` | Transaction/hash records, including simulated legacy records | No RLS; app/worker have no grants. |
| `iot_assets` | `SECURITY_SCOPED` | Infrastructure asset locations and operational health | No tenant/jurisdiction RLS; app/worker have no grants. |
| `iot_readings` | `SECURITY_SCOPED` | Sensor readings, anomalies, and maintenance predictions | No tenant/jurisdiction RLS; app/worker have no grants. |
| `resilience_hubs` | `SECURITY_SCOPED` | Facility location, occupancy, supplies, and operating status | No tenant/jurisdiction RLS; app/worker have no grants. |
| `srs_assets` | `SECURITY_SCOPED` | Infrastructure condition and maintenance attributes | No tenant/jurisdiction RLS; app/worker have no grants. |
| `srs_budget_events` | `SECURITY_SCOPED` | Planned and actual costs, variances, and flags | No tenant/jurisdiction RLS; app/worker have no grants. |
| `srs_contractors` | `SECURITY_SCOPED` | Contractor capacity, performance, and fraud flags | No tenant/jurisdiction RLS; app/worker have no grants. |
| `srs_utility_map` | `SECURITY_SCOPED` | Utility type, geometry, and depth | No tenant/jurisdiction RLS; app/worker have no grants. |
| `srs_work_orders` | `SECURITY_SCOPED` | Work assignment, costs, completion, and payment state | No tenant/jurisdiction RLS; app/worker have no grants. |
| `chat_logs` | `LEGACY_UNCLASSIFIED` | User/session identifiers and free-text conversation | No enforced subject/tenant boundary; app/worker have no grants. |
| `documents` | `LEGACY_UNCLASSIFIED` | User IDs, form data, file paths and generated documents | `user_id` is not protected by RLS; app/worker have no grants. |
| `issues` | `LEGACY_UNCLASSIFIED` | Civic reports, precise locations and optional reporter phone/user ID | No tenant/subject RLS; app/worker have no grants. |
| `offices` | `LEGACY_UNCLASSIFIED` | Office directory with staff names and phone numbers | Public-source status and personal contact fields are not normalized; app/worker have no grants. |
| `route_decisions` | `LEGACY_UNCLASSIFIED` | Derived request facts, idempotency and result metadata | No tenant/subject RLS; app/worker have no grants. Production triage stays disabled until migrated. |
| `srs_issue_events` | `LEGACY_UNCLASSIFIED` | Infrastructure issue status events and free-text notes | No tenant/subject RLS; app/worker have no grants. |
| `srs_issues` | `LEGACY_UNCLASSIFIED` | Issue descriptions, evidence URLs, reporter attributes and work assignment | No tenant/subject RLS; app/worker have no grants. |
| `user_gamification` | `LEGACY_UNCLASSIFIED` | Citizen-linked score, streak and badges | No enforced subject boundary; app/worker have no grants. |
| `users` | `LEGACY_UNCLASSIFIED` | Phone, email, name, location, password hash and login state | No tenant/subject RLS; app/worker have no grants. |

## Runtime role rules

- `scmirn_migrator` owns the application schema and runs only the one-shot
  Alembic migration container. It is not a superuser and cannot create roles
  or databases.
- `scmirn_app` is the web identity. It cannot create database/schema objects,
  own tables, inherit another role, bypass RLS, or read audit tables. Startup
  rejects the connection if these properties or forced staff RLS are absent.
- `scmirn_worker` currently receives no table grants because no production
  worker contract is implemented. This is least privilege, not evidence that
  retention is scheduled.
- `scmirn_auditor` is separate and read-only for audit tables. It is used for
  audit verification, never as the web connection.
- Provisioning is repeatable with
  [`scripts/provision_postgres_roles.py`](../../scripts/provision_postgres_roles.py).
  It refuses to adopt pre-existing public-schema objects owned by another
  role. For a new database, provision roles before migrations, run migrations
  as the migrator URL, then run provisioning again to apply explicit grants.

## Isolation blockers

The 9 `LEGACY_UNCLASSIFIED` tables, 14 security-scoped infrastructure tables,
and 3 audit tables do not all have tenant/jurisdiction RLS. Their runtime
grants are therefore withheld. A future migration must add stable ownership or
jurisdiction keys, backfill and validate them, install forced RLS, and prove
read/write/inference denial before any API or worker receives grants. The
current `tenants` login directory policy allows directory lookup across
tenants; it must be replaced by an independently reviewed identity discovery
design before treating tenant names as confidential.

Evidence isolation depends on both forced tenant RLS and request-level case
assignment ABAC. The tenant RLS policy trusts a transaction-local GUC set by
the application role; it is not an independent tenant credential and does not
withstand arbitrary SQL execution under the shared app role. Local and
S3-compatible storage adapters, ClamAV scanning, signed session-bound API
retrieval, and verified deletion handling are implemented. No approved
production bucket, ClamAV deployment, authority retention policy, or scheduled
worker has been configured or exercised. Evidence routes remain disabled in
production.
