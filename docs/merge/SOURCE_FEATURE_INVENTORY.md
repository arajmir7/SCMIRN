# SCMIRN(3) source feature inventory

**Review copy:** `/tmp/scmirn3-source-review-efec6db4` (301 curated files, about 2.4 MB). The ZIP’s dependency trees, virtual environment, `.env` files, database, build output, and caches were not extracted into the repository or executed. The source project identifies top-level `frontend/` + Flask `backend/` as its active application. `backend/src/` is a dormant Fastify/TypeScript implementation; `scmirn/frontend/` is an unreferenced duplicate scaffold.

**Evidence basis:** source code and active wiring, plus the 18 Python source tests and one isolated SQLite migration-trigger test executed during this review. `VERIFIED_WORKING` means the bounded behavior was exercised locally; it does not mean production readiness. A candidate cybercrime source was unavailable during the source project’s own review, has no content hash, and is intentionally excluded from active routing.

## Usable source features

The machine-readable set and final disposition are in [`feature-parity.json`](feature-parity.json). Each item below records the source and target boundary.

### SRC-01 — Consent-gated civic intake — `PARTIAL`

- **Source paths:** `frontend/src/components/CivicResolutionIntake.tsx`, `frontend/src/pages/LandingPage.tsx`; Flask `backend/app/api/v1_resolution.py`, `backend/app/services/jurisdiction.py`.
- **Entry/API:** public landing intake; `POST /api/v1/triage` and alias `POST /api/v1/jurisdiction/resolve`.
- **Contract:** JSON `{description: string (1–8000), state?: string|null (<=120), district?: string|null (<=120), consent_to_process: true}`. Optional `Idempotency-Key` header (<=128). Returns a route outcome, versions, provenance, `submission_status=NOT_SUBMITTED`, and no official reference.
- **Data/dependencies/access:** `route_decisions`, source/service/rule registry; Flask-SQLAlchemy; no external service, queue, login, or resource authorization. User consent is required.
- **Test/readiness/security:** consent, length, abstention, and response bounds covered by `test_jurisdiction_v1.py` (10 tests). Frontend build/e2e was not run because the ZIP excludes frontend dependencies. Route decisions omit raw free text; residual risks include public unauthenticated access, lack of configured rate limiting on these endpoints, and retention operating only when the worker/job runs.
- **Canonical target/strategy:** Problem Solver assistant surface; adapt semantics and controls to the canonical Bootstrap design, preserve the consent and privacy notice, never imply a government filing.

### SRC-02 — Deterministic classification and emergency abstention — `PARTIAL`

- **Source paths:** `backend/app/services/jurisdiction.py::classify_issue`, `resolve`; `backend/tests/test_jurisdiction_v1.py`.
- **Entry/API:** both triage POST routes above. Recognizes a small fixed set of immediate-danger phrases and registry rule terms; no LLM is invoked.
- **Contract/data/dependencies/access:** uses bounded description and optional geography; persists only extracted facts and a keyed fingerprint. Rule/service/source records are versioned. No external API or queue; public endpoint.
- **Test/readiness/security:** emergency test confirms no authority is inferred. Classifier coverage is deliberately narrow; state/district are recorded only as “provided” flags and do not constrain matching. Do not represent as complete issue classification, legal advice, or emergency service.
- **Canonical target/strategy:** integrate the safe deterministic/abstention behavior; keep unknown and ambiguous cases explicit.

### SRC-03 — Immutable, versioned service/authority/rule registry — `PARTIAL`

- **Source paths:** `backend/app/models/service_registry.py`, `backend/app/services/registry_seed.py`, initial Alembic revision.
- **Entry/API:** seed command `seed-routing-registry`; consumed by triage, service listing and evidence check.
- **Contract/data/dependencies/access:** models `OfficialSource`, `Authority`, `GovernmentService`, `RouteRule`; version uniqueness, constrained statuses, effective dates, source associations; append-only enforced by ORM update hooks. No external API; seed is operator-controlled but no authenticated registry-management API exists.
- **Test/readiness/security:** migration chain applied to temporary SQLite; PostgreSQL-specific policies were not exercised. Seeded source is `UNAVAILABLE` with no content hash, so the candidate service is not routable or listable.
- **Canonical target/strategy:** integrate versioned records and an unavailable seed; never promote a service without current source verification.

### SRC-04 — Official-source provenance and handoff gating — `PARTIAL`

- **Source paths:** `service_registry.py`, `jurisdiction.py::_live_verified_sources`, `api/v1_resolution.py`, `frontend/src/utils/officialHandoff.ts`.
- **Entry/API:** `GET /api/v1/sources/{source_key}`; source snapshots are embedded in route results. UI displays a handoff only when outcome is handoff-only and every source is `VERIFIED` with a 64-character lowercase SHA-256 hash.
- **Contract/data/dependencies/access:** source key/version/title/authority/type/canonical HTTPS URL/hash/review status/effective dates/reviewer/parser version. No crawling or TLS verification runs in the request path. Public read API.
- **Test/readiness/security:** backend tests verify missing hash remains `UNAVAILABLE` and no handoff is returned. Frontend gate has five Vitest cases in source but was not executed in this environment. A URL prefix check does not itself prove domain ownership or safe redirect behavior.
- **Canonical target/strategy:** integrate strict source gate and human-visible provenance; retain the no-route state until independent source capture/review.

### SRC-05 — Verified service catalog and evidence checklist — `PARTIAL`

- **Source paths:** `backend/app/services/jurisdiction.py::list_services`, `check_evidence`; `backend/app/api/v1_resolution.py`.
- **Entry/API:** `GET /api/v1/services`, `GET /api/v1/services/{service_id}`, `POST /api/v1/evidence/check`.
- **Contract/data/dependencies/access:** catalog returns active/effective services only if every linked source passes live verification; evidence check accepts at most 100 string IDs and returns `READY`, `INCOMPLETE`, `UNCONFIGURED`, `SOURCE_UNVERIFIED`, or `SERVICE_UNAVAILABLE`. No evidence content upload/storage; no login.
- **Test/readiness/security:** endpoint tests prove the current unverified service yields an empty catalog and `SOURCE_UNVERIFIED`; no requirements are invented. The check is a checklist only, not legal eligibility or filing readiness.
- **Canonical target/strategy:** integrate API and present an honest empty/unavailable catalog in the existing Rights Engine surface.

### SRC-06 — Request idempotency and privacy-minimized decision record — `VERIFIED_WORKING` within tested contract

- **Source paths:** `backend/app/services/jurisdiction.py::resolve`, `RouteDecision`; `backend/tests/test_jurisdiction_v1.py`.
- **Entry/API:** `Idempotency-Key` on triage. Same key and same HMAC fingerprint returns the prior decision; reuse for different input yields HTTP 409.
- **Contract/data/dependencies/access:** stores keyed input fingerprint, structured facts, route/version/source references, bounded output, creation and 30-day expiry. Raw description is not stored. HMAC depends on configured `SECRET_KEY`; unique database key serializes duplicate inserts.
- **Test/readiness/security:** replay, conflict, and “raw description absent” tests passed. No per-user identity, tenant boundary, request rate limit, or cross-process PostgreSQL concurrency test was run.
- **Canonical target/strategy:** integrate with per-request browser key, persisted decision, conflict handling and the same privacy boundary.

### SRC-07 — 30-day decision purge and retention worker — `PARTIAL`

- **Source paths:** `backend/app/services/retention.py`, `backend/retention_worker.py`, Flask CLI in `backend/app/__init__.py`, Compose worker service.
- **Entry/API:** `flask purge-route-decisions [--dry-run]`; worker polls and purges expired route decisions.
- **Contract/data/dependencies/access:** deletes only expired `RouteDecision` rows; emits count-only audit metadata. Uses database and a long-lived worker; no external service. CLI/operator access only.
- **Test/readiness/security:** dry-run, deletion, audit event and repeat-purge tests passed. Compose/service startup and scheduling were not executed; container configuration gives the backend the migration database URL, which violates least privilege.
- **Canonical target/strategy:** integrate a purge command and clearly document operational scheduling; do not claim TTL enforcement until schedule/monitoring is deployed.

### SRC-08 — Metadata-only append-only audit hash chain — `PARTIAL`

- **Source paths:** `backend/app/models/audit.py`, `backend/app/services/audit_chain.py`, audit migration, audit tests.
- **Entry/API:** internal `append_event` / `verify_chain`; CLI `verify-audit-chain`; used by retention purge, not by every route or privileged operation.
- **Contract/data/dependencies/access:** bounded actor/action/object fields and JSON metadata; rejects sensitive detail keys, maximum 16 KiB, SHA-256 chain, append-only ORM hooks and PostgreSQL/SQLite triggers. Postgres writes serialize with advisory lock. No SIEM anchor or external immutability.
- **Test/readiness/security:** 5 Python tests and isolated SQLite trigger test passed. PostgreSQL parallel writers, trigger/RLS behavior and independent chain anchoring were not run. A database owner can still alter the database or disable controls.
- **Canonical target/strategy:** integrate metadata-only event mechanics for triage and purge; make no “immutable” claim beyond tested database constraints.

### SRC-09 — Citizen-facing route result, emergency warning and handoff status — `PARTIAL`

- **Source paths:** `frontend/src/components/CivicResolutionIntake.tsx`, `frontend/src/utils/officialHandoff.ts`.
- **Entry/API:** landing component consumes triage result, explains abstentions, distinguishes `NOT_SUBMITTED`, shows rule/service versions and retention date, and conditionally renders official handoff.
- **Contract/data/dependencies/access:** consumes API result; no separate state service. No account required. User-controlled official navigation only.
- **Test/readiness/security:** five source Vitest tests exist but were not executed; source frontend build was blocked because dependencies were absent from the curated ZIP review copy. This is UI behavior, not government submission.
- **Canonical target/strategy:** integrate with canonical typography, colors, spacing and controls; do not import the source Tailwind layout.

## Non-usable source capabilities (not counted as source-real features)

The inventory still records these so they cannot be mistaken for working systems:

| Candidate | Evidence | Source state | Disposition |
|---|---|---|---|
| Legacy complaint/case creation, tracking, escalation, map, office directory, analytics | Flask `api/issues.py`, `api/tracker.py`, `api/offices.py` return 410/503 with explicit unavailable messages | `STUB` | Do not port as working features; canonical equivalents are independently documented. |
| Legacy AI chat/legal analysis | Flask `api/ai_assistant.py` returns 410; reachable `/ai-help` UI calls unavailable path | `UNREACHABLE` / `STUB` | Do not copy; canonical assistant is audited separately and remains legally ungrounded until fixed. |
| Document generation/storage/PDF and evidence upload | Flask `api/documents.py` returns 410; legacy document generators/UI are disconnected | `UNREACHABLE` / `STUB` | No file/document capability to merge. |
| Agent orchestration, HITL, event workflows and agent pages | `backend/app/agents/**` and many frontend components are not registered/reachable from active `run.py` / `AppRoutes.tsx` | `UNREACHABLE` | Preserve as excluded reference only. |
| TypeScript/Fastify API, scheduler, WebSocket and Prisma backend | `backend/src/**` and `backend/package.json`; active Compose starts Flask `run:app` | `UNREACHABLE` | Do not combine two backend runtimes. |
| Nested `scmirn/frontend` Vite scaffold | Duplicate project with no active deployment/import route | `DUPLICATE` | Exclude. |
| ZIP SQLite case data | `backend/data/scmirn.db`; 11 tables with personal case, report, chat and generated-document data | `UNSAFE` to migrate as demo data | Never import user/report rows; use schema only if separately reviewed. |
| “Connected” government systems and broad AI/legal/multilingual/map claims | No authorized live connector or source evidence; legacy endpoints disabled | `MOCK` / `NOT_TESTED` | Do not describe as deployed. |

## Package/deployment evidence

- Active Compose describes Postgres, Redis, Flask backend, retention worker, and React frontend, but was not built or run from this review copy.
- Source `README.md` says not production ready. The source folder contains environment files whose contents were deliberately not read. If they contain real credentials, rotate them through the credential owner.
- ZIP-contained SARIF artifacts report 9 HIGH/CRITICAL Redis findings and 24 HIGH/CRITICAL Postgres findings, despite contradictory zero-findings claims elsewhere. Artifacts are stale/unverified; no fresh source scan was run.
- Backend: 18 source tests passed; SQLite migration chain + trigger test: 1 passed. PostgreSQL suite, frontend test/build, container and integration suites: `NOT TESTED`.
