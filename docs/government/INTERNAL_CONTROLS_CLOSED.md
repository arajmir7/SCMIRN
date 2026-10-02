# Phase 2 internal control status

**Assessment date:** 2026-10-02. **Overall state:** `PARTIAL`. This evidence is local and bounded; it is not agency acceptance, security certification, or production deployment.

## Implemented with local evidence

| Control | Evidence | Limits |
|---|---|---|
| Canonical database baseline | Alembic head `20261002_03` creates all 34 ORM tables from zero and safely adopts an exact pre-existing schema. Unknown tables, drift, and partial staff schemas fail closed. | Six SQLite migration tests and the full migration chain on disposable PostgreSQL 16 passed. No production database was used. |
| Production table-creation policy | Production uses `AUTO_CREATE_DB=False`; schema preparation remains an explicit Alembic operation. | No production database or operator migration was run. |
| Source status constraints | Source review states are `DRAFT`, `VERIFIED`, `SUPERSEDED`, and `REVOKED`; the migration translates legacy `UNVERIFIED` and `UNAVAILABLE` to `DRAFT`. | No authenticated source publication or dual-review workflow exists yet. |
| Staff password and TOTP flow | Operator CLI provisioning; scrypt password hashes; password login followed by a signed short-lived, one-use MFA challenge; AES-GCM encrypted TOTP secret; replay prevention; failed-login lockout; 14-character minimum password policy; change/reset and account-disable operations revoke sessions. | Six unit tests and the login/MFA path against a disposable PostgreSQL database using a non-owner, non-BYPASSRLS role passed. No SSO/federation, independent account recovery, or security review. |
| Staff sessions and role checks | Opaque cookie token with only SHA-256 stored, HttpOnly/SameSite cookie, double-submit CSRF check, idle/absolute expiration, logout, password-change and disable revocation. Case APIs enforce tenant-admin/case-officer/auditor roles. | No frontend staff console, identity-provider integration, multi-instance production exercise, or privileged-route penetration test. |
| Metadata-only case workflow | Tenant-bound case create/list/read/status API, fixed case types, server-selected titles, constrained transitions, tenant-consistent foreign keys, and append-only metadata event/audit history. The API accepts no free text or attachments. | API and database tests passed on SQLite and disposable PostgreSQL 16. No staff UI, assignments, evidence vault, appeals, service-level queues, citizen linkage, or official agency status. |
| PostgreSQL RLS definitions | Revision `20261002_03` enables and forces RLS on tenant/staff tables, scopes staff sessions by exact token hash with a same-tenant session-management policy, and installs append-only history triggers. | Full chain and policies passed against disposable PostgreSQL 16 using a non-owner, non-BYPASSRLS runtime role, including cross-tenant read/write denial and append-only checks. Production DB/role configuration remains unverified. Other legacy tables still lack a complete tenant model. |
| Official source catalog and handoffs | Ten source records, five service candidates and nine standard-TLS page hashes are recorded. Four services pass runtime checks and appear only as `OFFICIAL_HANDOFF_ONLY`; route responses remain `NOT_SUBMITTED`. | Hashes identify fetched bytes, not agency approval or ongoing freshness. No connector, form submission, official reference, or publication console exists. |
| Cybercrime source remains gated | Normal TLS validation for `https://www.cybercrime.gov.in/` failed on 2026-10-02, so the source stays `DRAFT` and the service candidate is hidden. | Re-review depends on a valid certificate chain at the external portal. |
| Dependency audit and inventory | `pip-audit` reports no known vulnerabilities for the hash-locked Python dependencies; `npm audit` reports zero findings for the frontend lockfile. Python and frontend CycloneDX dependency inventories are checked in. | No SAST, secret, DAST, container/OS scan, image SBOM, or signed provenance. See [dependency evidence](../security/DEPENDENCY_SCAN_2026-10-02.md). |
| Backend suite and route contract | `python -m pytest -q` in the hash-locked Python 3.11 environment with the opt-in PostgreSQL test enabled: 65 passed, two existing SQLAlchemy `Query.get()` deprecation warnings. OpenAPI route parity passes for 17 allowlisted paths; 91 other API operations return 503 in synthetic production mode. | PostgreSQL used a disposable local instance and temporary non-owner role. There is no production ingress, load, penetration, or deployment evidence. |

## Still open inside this repository

- Repeat the disposable PostgreSQL/RLS integration test in CI and validate the approved deployment database role/configuration before staff access is enabled. Never use a table-owner or `BYPASSRLS` application role.
- Decide and implement tenant ownership for legacy citizen, issue, document, chat, route-decision and audit records before any shared-tenant data is enabled.
- Add the staff console, staff administration/reviewer separation, assignment and appeal queues, source publication workflow, and accessible/multilingual staff operations.
- Implement private encrypted evidence storage, malware quarantine/scanning, signed download authorization, purpose-bound retention, and verifiable deletion.
- Complete password/account lifecycle policy, MFA reset/recovery, SSO/federation and centralized identity integration if required by the selected deployment; perform an independent auth/session review.
- Add route-wide authz tests, accessibility evaluation, multilingual/adversarial replay corpus, stable explanation codes, and privacy-safe telemetry.
- Add staffed alert ownership, performance/capacity evidence, backup/restore, disaster-recovery and rollback rehearsals.
- Run source, secret, DAST, container and OS-image scans; generate image SBOMs and signed build provenance; review findings.
- Add source recapture scheduling, expiry alerts, dual review and service-owner runbooks.

## Blocked by external inputs

- The cybercrime portal operator must restore a certificate chain that passes normal TLS verification before its public link can be re-reviewed.
- Any API filing or status integration requires written agency authorization, current contract/specification, an approved sandbox and credentials, a permitted data-sharing purpose, and a named operational owner.
- Qualified legal/privacy reviewers must approve legal scope, notices, data purposes/retention, and any cross-organization sharing before production casework.
- Production rollout requires an accountable hosting/operator owner and approved identity, secrets/KMS, TLS ingress, PostgreSQL/Redis/object storage, backup/DR, incident response and monitoring arrangements.
- Independent assessment or government certification, where required, must be performed by the designated assessor against an approved scope.

## Release decision

`NOT PRODUCTION READY`. Staff identity, roles, a metadata-only case API, and PostgreSQL RLS have local disposable-database evidence. Production database/role validation, legacy-record tenant isolation, the staff console, evidence handling, operational controls, external approvals and independent evidence remain release blockers. See [execution state](../scmirn/EXECUTION_STATE.md), [source provenance](SOURCE_PROVENANCE.md), and [database inventory](DATABASE_SCHEMA.md).
