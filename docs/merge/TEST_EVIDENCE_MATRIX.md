# Test evidence matrix

All test statements are dated **2026-10-01** (workspace date). Baseline results were run before application changes in this task.

| System / gate | Command or evidence | Result | Limits |
|---|---|---|---|
| Canonical frontend TypeScript | `npm run typecheck` in `src/frontend` | Passed | Static typecheck only. |
| Canonical production frontend build | `npm run build` in `src/frontend` | Passed with Vite 6.4.3 | Build output is local; no served production smoke at baseline. |
| Canonical browser suite | `npm run test:e2e -- --workers=1` | 8 passed | Existing suite; does not cover all security/accessibility routes. |
| Canonical backend | `python -m pytest tests -q` in `src/backend` | 19 passed, 115 warnings | Warnings include deprecated UTC-naive datetime and `Query.get`; tests do not prove production isolation. |
| Canonical visual capture | Playwright CLI, Chromium desktop, 1440×1000 | Captured `/tmp/scmirn-canonical-baseline.png` | One desktop viewport, no full-page/mobile visual diff. |
| Source jurisdiction API | `python -m pytest tests/test_jurisdiction_v1.py -q` in curated source backend | 10 passed | SQLite/in-process tests; no authorized verified source route exists. |
| Source audit | `python -m pytest tests/test_audit_chain.py -q` | 5 passed | SQLite; no independent storage anchor. |
| Source retention | `python -m pytest tests/test_retention.py -q` | 3 passed | Does not prove worker scheduling or deletion observability. |
| Source Alembic SQLite migrations | Fresh isolated SQLite upgrade to head | 3 migrations applied | PostgreSQL-specific SQL/RLS was not executed. |
| Source SQLite audit DB triggers | `SCMIRN_SQLITE_TEST_DATABASE_URL=... pytest tests/test_audit_migration_sqlite.py -q` | 1 passed | SQLite only. |
| Source frontend | `npm run build` in curated source frontend | Not run: `tsc` missing because dependencies were excluded | Installing ZIP dependencies was intentionally not part of baseline. Five frontend Vitest cases exist but were not run. |
| Source PostgreSQL tests | `test_audit_postgres.py` | Not run | No isolated PostgreSQL test URL/service. |
| Accessibility / axe all routes | none | Not tested | Release blocking. |
| DAST / SAST / SCA / secret scan | stale ZIP artifacts only | Not verified | 33 HIGH/CRITICAL Redis/Postgres SARIF findings require fresh scan. |
| Performance, backup/restore, DR, Docker production boot | none | Not tested | Release blocking for production. |

Later merge tests must append fresh results; do not overwrite this baseline record. The final release verdict is `NOT PRODUCTION READY` until all external and production gates are satisfied.

## Post-merge implementation evidence

These checks were run on **2026-10-01** in the local workspace after the frontend/backend merge. They establish local build and test results only.

| System / gate | Command or evidence | Result | Limits |
|---|---|---|---|
| Canonical frontend TypeScript | `npm run typecheck` in `src/frontend` | Passed | Static typecheck only. |
| Canonical production frontend build | `npm run build` in `src/frontend` | Passed | Local Vite build; no production deployment smoke. |
| Canonical browser suite | `npm run test:e2e` in `src/frontend` | 8 passed | Includes consented triage, draft disclosure, donation absence, demo labels, and external location lookup consent; not a full accessibility/security suite. |
| Canonical backend | `python -m pytest tests -q` in `src/backend` | 30 passed, 116 warnings | Local test configuration; warnings include existing deprecations; no PostgreSQL service. |
| Routing schema migration | Fresh isolated temporary SQLite database; Alembic upgrade to head and downgrade | Passed; 7 source-routing tables created on upgrade | PostgreSQL execution, concurrency, and deployment rollback were not tested. |
| Production API boundary | Backend unit tests in `tests/unit/api/test_source_routing.py` | Passed | Configuration and request-gate behavior only; no production ingress/deployment smoke. |
| Source feature parity | `python scripts/check_feature_parity.py` | 9 source-real features, 9 integrated, 0 unexplained | Evidence completeness gate; does not certify correctness or production operation. |
| Enterprise OpenAPI | YAML parse and required source-route presence check | Passed | Contract syntax/presence only; no generated-client or live-server conformance test. |
| PostgreSQL, row-level security, DAST/SAST/SCA, accessibility/axe, backup/restore, DR, performance, production smoke | No production environment available | Not tested / not verified | Required before any production or government deployment claim. |

The source routing registry currently has no verified official service source configured, so safe behavior is abstention. No government filing, payment, or official case tracking is enabled. The migration creates the routing schema; it does not establish a complete baseline for legacy tables or implement PostgreSQL row-level security.

## Production-hardening overlay evidence

These checks were run on **2026-10-01** against the hardened workspace. They establish local automated and image-build evidence only.

| System / gate | Command or evidence | Result | Limits |
|---|---|---|---|
| Backend tests in pinned Python 3.11 dependency environment | Disposable `python:3.11-slim` container; hash-verified install from `requirements-dev.lock`; `pytest -q tests` | 39 passed, 2 existing SQLAlchemy `Query.get()` deprecation warnings | Unit/policy tests only; no PostgreSQL service in this run. |
| Frontend typecheck and build | `npm --prefix src/frontend run typecheck`; `npm --prefix src/frontend run build` | Passed | Local production build, not deployed. |
| Frontend browser flows | `npm --prefix src/frontend run test:e2e` | 8 passed | Does not provide a route-wide accessibility or security audit. |
| Source feature parity | `python scripts/check_feature_parity.py` | 9 source-real features; 9 integrated; 0 unexplained | Evidence completeness only. |
| OpenAPI and production route gate | `python scripts/validate_openapi_contract.py` | OpenAPI 3.1 syntax/path/method checks passed for 8 allowlisted production paths; synthetic production requests confirmed 91 other registered API operations return 503 | No remote ingress, WAF, identity provider, or deployment verification. |
| Production config and image build | `scripts/release_gate.sh` with a disposable synthetic env and placeholder CA files; images tagged `local-hardening-20261001-d49f12a` | Config/Compose policy and both Docker image builds passed | Placeholder CA files prove file-policy and Compose wiring only, not certificate trust or service connectivity. This did not deploy or contact PostgreSQL/Redis. |
| Release tag reuse guard | `scripts/deploy.sh build` with an existing local tag and synthetic config | Reuse rejected before build | Confirms local Docker tag uniqueness only; no registry immutability policy is configured. |
| Backend and frontend image IDs | `docker image inspect` for the local build tag | Backend `sha256:603bcf46e8817314c6bfe00c4e536e78d6a0bfea2c85f6946360f36f88d2655f`; frontend `sha256:9297bd75148c984bd9073888d443598f17237b997cf30397c948f02f02dcba7e` | Local image IDs; no signed provenance, registry push, or container scan. |
| Dependency lock hashes | SHA-256 for backend runtime/dev and frontend package lock | Recorded in `RELEASE_EVIDENCE.json` | Hash pins do not replace SCA or artifact provenance. |
| Rollback, authz/tenant isolation, backups/restore/DR, performance, monitoring, accessibility, security scans, agency/legal review | No applicable verified evidence | Not tested / not verified | Release blocking. |

The release-gate command exits nonzero intentionally while unresolved production blockers remain. The image build is not a release approval, and the earlier disposable PostgreSQL/Redis Compose rehearsal predates the latest configuration and route-gate changes.

## Government transformation follow-up evidence

These checks were run on **2026-10-02** after the route-severity, verified-host, geography, and problem-first frontend changes. They establish local repository evidence only.

| System / gate | Command or evidence | Result | Limits |
|---|---|---|---|
| Backend suite, locked Python 3.11 | Temporary `python:3.11-slim` container; `pip install --require-hashes -r requirements-dev.lock`; `pytest -q -p no:cacheprovider tests` | **46 passed, 2 existing SQLAlchemy deprecation warnings, 1.71s** | Unit/policy tests with synthetic registry fixtures; no production database or government source. |
| OpenAPI / production route parity | `python /workspace/scripts/validate_openapi_contract.py` in the same locked container | **Passed:** 8 allowlisted paths; 91 other registered API operations return 503 in synthetic production mode. | No remote ingress, identity provider, agency service, or deployment. |
| Local geography guard | Backend parameterized regression test | Six combinations verify missing/mismatched state or district abstain and matching synthetic geography permits only an explicit handoff. | Synthetic records only; no authoritative boundary dataset or real jurisdiction accuracy evidence. |
| Release gate | `bash scripts/release_gate.sh` with temporary hash-locked Python 3.11 venv and temporary synthetic env/placeholder CA files | **7/7 executable checks passed:** 46 backend tests, frontend typecheck, frontend build, 8 browser tests (6.6s), parity 9/9, OpenAPI 8/91, production config and both local image builds. | Script exit is intentionally 1 because production blockers remain. No deployment was started and PostgreSQL/Redis were not contacted. Placeholder CA files establish only config wiring. |
| Local image identifiers | `docker image inspect` for the unique local verification tag | Backend `sha256:55a4f655625ea767314dbdd641faf89d982900171a847bae61b28e7f66f565f4`; frontend `sha256:5b36ec6f35cbf210d03323e25066f7ea1ad6fcc5b2bfdb584388fb96744f6f15` | No registry push, SBOM, signed provenance, or fresh container scan. |
| Feature parity | `python scripts/check_feature_parity.py` | **9 integrated, 0 unexplained** | Evidence completeness only. |
| Government documentation links | Relative Markdown link check over `docs/government/*.md` | All relative links resolve. | Does not validate external authority or regulatory interpretation. |

The matching synthetic route test demonstrates only deterministic code behavior: it does not prove that a configured source is authoritative, current, legally applicable, or safe for citizens.

## Earlier Phase 2 migration and source-catalog evidence

Snapshot run on **2026-10-02** after the database baseline and official source catalog changes, before staff identity/RLS integration was added. These results are preserved as historical local evidence; the later staff identity and tenant-case section below records the current migration head and PostgreSQL test results.

| System / gate | Command or evidence | Result | Limits |
|---|---|---|---|
| Canonical backend suite | Temporary hash-locked Python 3.11 environment; `python -m pytest -q src/backend/tests` | **58 passed, 2 existing SQLAlchemy `Query.get()` deprecation warnings, 2.78s** | SQLite and in-process tests. No PostgreSQL instance was run for these new revisions. |
| Database zero-to-head | `tests/integration/test_migration_baseline.py` | **6 passed:** empty DB, exact schema, legacy-only schema, drift refusal, and legacy source-state conversion/constraint checks. All 25 ORM tables plus `alembic_version` reached `20261002_02`; existing user rows were preserved. | Isolated SQLite databases only; no backup/restore, concurrency or PostgreSQL RLS evidence. |
| Existing schema safety | Migration preflight integration tests | Unknown structure/drift was refused before creating new migration tables; exact/legacy schemas reached head without losing fixture rows. | No real application database was inspected or changed. |
| Official source fetch | Standard TLS, host allowlist and 2 MB response cap; SHA-256 stored in `official_source_catalog.json` | **9 official pages fetched and hashed; 1 cybercrime portal source remains `DRAFT`.** | Hashes are over exact response bytes; source bodies were not archived. Hashes do not prove legal approval or ongoing freshness. |
| Verified handoffs | `tests/unit/api/test_source_routing.py` | **28 passed.** Four official handoff candidates are exposed; NCH/CPGRAMS/central RTI/NALSA-Tele-Law outcomes explicitly remain `NOT_SUBMITTED`. | Synthetic request text and offline test DB; no agency filing, credentials, or receipt was used. |
| Cybercrime source TLS | Read-only fetch of `https://www.cybercrime.gov.in/` using normal certificate validation | Fetch blocked with `CERTIFICATE_VERIFY_FAILED` (certificate expired); route remains `DRAFT` and is omitted from active service listing. | External endpoint state; no TLS bypass was attempted. |
| PostgreSQL / RLS | No PostgreSQL service run after `20261002_02` | **Not verified.** | Required before production database approval. |
| Python dependency SCA and SBOM | `pip-audit 2.10.1` against `requirements-dev.lock`; CycloneDX output generated | **No known vulnerabilities; 40 components.** | Advisory snapshot only; not source-code or image analysis. |
| Frontend dependency SCA and SBOM | `npm audit` against `package-lock.json`; `npm sbom --package-lock-only` | **0 known findings; 152 components.** | Dependency-lock scope only; not source-code or image analysis. |
| Frontend tests, accessibility, SAST/DAST/secret/container scans, backup/restore, DR, performance, production boot | No new runs in this phase | **Not tested in this phase.** | Dependency SBOMs are generated separately; earlier frontend/build evidence does not cover this backend change or external operations. |

Release verdict remains `NOT PRODUCTION READY`; see [Phase 2 blocker closure](../government/INTERNAL_CONTROLS_CLOSED.md).

## Staff identity and tenant-case evidence

Checks run on **2026-10-02** after implementing staff password+TOTP, session management, RBAC, metadata-only cases and the `20261002_03` RLS migration. These results establish local behavior only.

| System / gate | Command or evidence | Result | Limits |
|---|---|---|---|
| Full backend suite, hash-locked Python 3.11 | `python -m pytest -q` with `SCMIRN_POSTGRES_RLS_TEST_URL` set to a disposable PostgreSQL 16 instance | **65 passed, two existing SQLAlchemy `Query.get()` deprecation warnings, 5.22s.** | Local disposable database and in-process tests; no production deployment. |
| Staff identity and sessions | `tests/unit/api/test_staff_auth.py` and PostgreSQL integration test | **6 unit tests passed:** operator MFA enrollment; login/MFA replay; lockout; password change and session revocation; idle expiry; CSRF denial; role checks. Login/MFA was also exercised with PostgreSQL persistence. | No identity provider, deployed browser, or independent penetration test. |
| Tenant case API | Staff suite and PostgreSQL integration test | Tenant A receives 404 for tenant B case; the database role is denied cross-tenant reads/writes; role-denied and bounded case transitions create metadata-only events. | No citizen text, uploads, assignments or agency case linkage; legacy tables remain outside staff RLS. |
| Database migration head | `tests/integration/test_migration_baseline.py` and PostgreSQL integration test | **6 SQLite migration tests passed:** empty, exact full schema, legacy-only schema, drift refusal, legacy source-state conversion and status constraint. **34 ORM tables** reach `20261002_03`; PostgreSQL full chain also reached head; seeded legacy user row preserved. | Disposable test databases only. No production migration, backup/restore, or rollback rehearsal. |
| OpenAPI and production route gate | `python scripts/validate_openapi_contract.py` | **Passed:** 17 allowlisted paths are documented; synthetic production mode returns 503 for 91 other API operations. | Staff APIs remain opt-in; no production deployment or ingress test. |
| PostgreSQL RLS/runtime role | Opt-in `tests/integration/test_postgres_staff_rls.py` against disposable PostgreSQL 16 | **Passed:** non-owner/non-BYPASSRLS role; forced policies; tenant reads/writes; session-hash scope; login/MFA/case API; append-only history checks. | Local integration evidence only; deployment DB role/configuration must be validated. Legacy records remain outside RLS scope. |
| Dependency SCA and SBOM | Updated hash-locked `requirements-dev.lock`, `pip-audit`, `npm audit`, CycloneDX exports | Python audit: no known findings; frontend audit: 0 findings. Updated evidence and digests are in [dependency scan report](../security/DEPENDENCY_SCAN_2026-10-02.md). | Lockfile scope only; no source, image or OS scan. |

Production staff authentication remains disabled until the approved deployment database role/configuration and operating controls are validated. The overall release remains `NOT PRODUCTION READY`.

## Phase 3 database privilege and boundary evidence

Checks run on **2026-10-02** against a disposable PostgreSQL 16 instance after
adding separate app, migrator, worker and auditor identities. This section is
the current test snapshot; previous sections are historical records.

| System / gate | Command or evidence | Result | Limits |
|---|---|---|---|
| Backend suite with PostgreSQL integration | Hash-locked Python 3.11 runner; `SCMIRN_POSTGRES_RLS_TEST_URL` pointed only to disposable PostgreSQL | **67 passed, two existing SQLAlchemy `Query.get()` deprecation warnings.** | No production database, deployment, or external service. |
| PostgreSQL roles and grants | Role provisioner plus integration test; provisioner was run twice to check repeatability | Four distinct logins; app cannot create DB/roles/schema objects, own relations, bypass RLS, or read audit/legacy content. Auditor is read-only; worker has no table grants. | Synthetic role passwords/database only. Deployment role provisioning remains unverified. |
| Migration and mapped-table inventory | Alembic zero-to-head plus `test_database_security_contract.py` | Head `20261002_04`; 34 of 34 mapped tables classified. Nine legacy tables are quarantined without app/worker grants. | Does not complete ownership keys/RLS for legacy data. |
| RLS and audit separation | `tests/integration/test_postgres_staff_rls.py` | Forced tenant RLS and cross-tenant denial; audit append-only web access; auditor read; app audit read, DDL, and an overprivileged role rejected. | Disposable PostgreSQL 16 only. |
| Production API contract | OpenAPI validator and production gate | 15 allowlisted paths; 93 other registered API operations returned deterministic HTTP 503, including triage/jurisdiction. | Synthetic Flask production mode only; no external ingress/WAF. |
| Production readiness | `scripts/release_gate.sh` | Release verdict remains **`NOT PRODUCTION READY`**; PostgreSQL integration is required by the gate when run. | Production auth/recovery, legacy isolation, scheduled purge, observability, scans/provenance, accessibility, and DR controls remain open. |

Detailed implementation status and remaining controls are in
[`../security/PHASE3_IMPLEMENTATION_STATUS.md`](../security/PHASE3_IMPLEMENTATION_STATUS.md).
