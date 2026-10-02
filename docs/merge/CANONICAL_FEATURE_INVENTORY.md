# Canonical SCMIRN feature inventory

**Visual baseline:** the canonical site at `/` was captured at 1440×1000 in `/tmp/scmirn-canonical-baseline.png`. The existing navbar, dark civic hero, gradient report action, Bootstrap cards, floating assistant, map, and footer are the visual source of truth. No design replacement is authorized.

**Baseline execution:** `npm run typecheck` passed; `npm run build` passed; Playwright reported 8 passed; backend pytest reported 19 passed, 115 deprecation warnings. Initial test evidence is recorded in [`TEST_EVIDENCE_MATRIX.md`](TEST_EVIDENCE_MATRIX.md). The working directory has no `.git` metadata, so a commit SHA or clean-tree claim is unavailable.

| ID | Feature / active entry | API and data | State / evidence | Integration note |
|---|---|---|---|---|
| CAN-01 | Public home, nav, hero, features and footer — `src/frontend/src/App.tsx`, `pages/HomePage.tsx`, `components/layout/*` | React Router; API-backed data plus hard-coded copy | `VERIFIED_WORKING` for render and navigation via Playwright; several public claims are unsupported | Preserve visual composition; qualify/remove unverified metrics and “live”/government claims. |
| CAN-02 | Assistant panel / Problem Solver — `components/assistant/AssistantPanel.tsx` | `POST /api/ai-assistant`; current legacy `ai_engine` and `chat_logs` persistence | `PARTIAL`; browser panel works, answer grounding/PII retention are not approved | Add source-gated triage intake and explicit consent; do not imply AI legal advice. |
| CAN-03 | Rights analysis — HomePage form | `POST /api/rights/analyze`; local `ai_engine` | `PARTIAL`; e2e verifies response rendering/error states; no authoritative legal-source/version binding | Use source-gated resolver for routing; label any separate legal content as informational and unverified. |
| CAN-04 | Issue/report submission — `ReportIssueModal`, `CivicIssueMap` | `POST /api/report-issue`, `POST /api/donate`; `issues`, reporter contact, media, funding fields | `PARTIAL`; Playwright verifies multipart post and map actions. Donation path lacks a verified payment integration; reports are not submitted to government. | Preserve modal styling; display “SCMIRN record only” / no government filing; prevent payment-success claims. |
| CAN-05 | Issue map/heatmap — `CivicIssueMap`, `HeatmapPage`, `useIssues` | `/api/issues`, `/api/issues/stats`, nearby/geocoding APIs; issue rows | `PARTIAL`; data is DB-backed but `seed_database()` inserts demo records on first empty list request | Keep map presentation; segregate seed fixtures and mark demo data, block demo seeding in production. |
| CAN-06 | Office lookup — `OfficesPage` | `GET /api/offices`; seeded `offices` rows | `PARTIAL`; browser render/search works; officer/contact source and freshness are not verified | Do not present seeded entries as live government directory; map source-gated service catalog in Rights Engine. |
| CAN-07 | Tracker — `TrackerPage` | `GET /api/tracker/summary`; joins issue data | `PARTIAL`; list summary renders; no external government status feed | State “SCMIRN record status”; do not imply official status or escalation. |
| CAN-08 | Analytics — `AnalyticsPage` | `GET /api/analytics/summary`; aggregates app DB | `PARTIAL`; browser summaries render; sample data and representativeness unverified | Keep charts; qualify source, scope, date and demo state. |
| CAN-09 | Document generator — modal and Documents page | `POST /api/documents/generate`, download endpoint; `documents` table | `PARTIAL`; e2e proves generated response, not legal validity or official acceptance | Avoid “legally valid”/filing claims; only draft assistance unless independently reviewed. |
| CAN-10 | Platform workspaces: IoT, Legal Copilot, Blockchain, Gamification, Resilience, Digital Twin, City Organism, Enterprise | `/api/v1/iot/*`, `/ai/*`, `/blockchain/*`, `/gamification/*`, `/resilience/*`, `/twin/*`, `/city-brain/*`, `/enterprise/*`; mixed SQL, simulation and fixed demo data | `MOCK` / `PARTIAL`; all workspaces render and have controls (Playwright); data feeds and actions are not verified production systems | Keep available only with explicit demo/simulation labeling; no government, blockchain, sensor, payment, or connector claims. |
| CAN-11 | Authentication | `/api/v1/auth/health`; auth modules and user table | `STUB` / `PARTIAL`; no full authenticated citizen/admin route boundary or MFA | Do not expose privileged workspaces as government administration; external identity/MFA remain a blocker. |
| CAN-12 | File upload and generated document downloads | `/api/uploads/<filename>`, multipart report, `/api/documents/*` | `PARTIAL`; path exists; malware scanning, private object storage and complete access checks unverified | Do not import source evidence upload feature; require hardening before production. |
| CAN-13 | Enterprise OpenAPI/docs | `docs/enterprise/openapi-enterprise.yaml` and architecture/security/ROI/design-system docs | `NOT_TESTED` as a deployment contract; docs describe broader platform than proven live code | Reconcile claims with route inventory and mark simulations/external boundaries. |

## Runtime observations (baseline snapshot, 2026-10-01)

- Flask app factory registers the current active API blueprints from `src/backend/app/__init__.py`; frontend routes are `/`, `/offices`, `/heatmap`, `/tracker`, `/analytics`, `/documents`, and `/platform`.
- Existing legacy Jinja UI is not the registered public frontend. It remains under `docs/legacy/flask-frontend-reference/`.
- `src/backend/app/infrastructure/database/database.py` uses `db.create_all()` and has sample issue/office seeds. No `src/backend/migrations/` directory was present at inventory time.
- `/api/issues` invokes demo seeding when no issues exist. This is a production data-separation blocker.
- Current project has no checked-out `.git` metadata in this workspace; initial SHA and tree cleanliness cannot be asserted.

## Post-merge implementation update — 2026-10-01

The descriptions above record the pre-change baseline. The following changes preserve the canonical page composition while replacing unsupported claims and disabling unsupported production actions:

| Area | Implemented update | Evidence / remaining boundary |
|---|---|---|
| Assistant and rights entry | Replaced legacy AI chat and `/api/rights/analyze` UI with explicit-consent source-gated triage, deterministic result, provenance and `NOT_SUBMITTED` status. | `AssistantPanel.tsx`, `resolution.ts`, `test_source_routing.py`, `migration.spec.ts`; no verified official service currently exists. |
| Public claims | Removed user counts, resolution metrics, AI/legal promises, live/government coverage claims and landlord legal-answer mockup. | `HomePage.tsx`, `CLAIMS_REGISTER.md`; layout composition remains canonical. |
| Demo record reporting | Added SCMIRN-only disclosure, sensitive-data warning, explicit consent, optional exact-location choice, and no AI/agency filing claim. Production APIs are gated. | `ReportIssueModal.tsx`, `issues.py`; development demo still stores text/media, so use synthetic data only. |
| Map and funding | Removed fundraising controls and external image loads; disclosed tile providers; location requires explicit request; unmatched external search requires opt-in. | `CivicIssueMap.tsx`, `migration.spec.ts`; OpenStreetMap/Esri map tiles remain third-party requests. |
| Office/tracker/analytics/documents | Labeled records as samples; removed predictions, official case-flow and legal validity language; draft generation requires synthetic-data confirmation. | Corresponding React pages and modal; production APIs return unavailable. |
| Advanced workspaces | Added prototype/simulation labels; blockchain hash output is in-memory and marked `SIMULATED`, with no database or chain transaction. | `PlatformPage.tsx`, workspace components, `blockchain.py`; production gate blocks simulation APIs. |
| Production safety | Required explicit secret/PostgreSQL/TLS Redis/HTTPS CORS config, disabled schema auto-create/seeding, added routing migration and production API allowlist; migration mode rejects traffic. Disposable PostgreSQL/Redis TLS Compose rehearsal completed migration, health, proxy and safe-abstention checks. | `config.py`, `database.py`, `__init__.py`, Alembic migration and release evidence; no RLS, identity, full schema baseline, backup/restore or live deployment proof. |
| Footer/docs | Removed fake newsletter/social/policy controls; root README and enterprise/OpenAPI docs now separate prototype evidence from target-state proposals. | `README.md`, `docs/enterprise/*`, `openapi-enterprise.yaml`. |

## Frontend Labs and staff update — 2026-10-02

The original inventory and preceding implementation notes are preserved as dated snapshots. Current frontend routing and evidence are:

| Area | Current implementation | Evidence and limits |
|---|---|---|
| Public navigation | Adds `/labs` and `/staff` navigation. Prior `/offices`, `/heatmap`, `/tracker`, `/analytics`, `/documents`, and `/platform` paths redirect to matching `/labs/*` routes. | Covered by Playwright route/navigation checks. This is UI routing, not a service authorization boundary. |
| Labs | `/labs` lists the office directory, issue map, tracker, analytics, draft templates, and platform showcase as demo workspaces. Nested routes show the Labs disclosure; synthetic/personal-data warnings identify their boundaries. | UI labels and navigation verified locally. Underlying sample APIs and demos remain unfit for real casework. |
| Staff workspace | `/staff` checks session state, provides password + MFA screens when the API requires sign-in, and supports bounded metadata case list/create/status update, CSRF headers, and read-only auditor UI. Disabled, malformed-response, network, empty and role states are handled. | 13 Playwright tests cover the 5 new staff/Labs flows plus existing routes; staff endpoints are mocked in browser tests. Backend staff auth, ABAC and PostgreSQL RLS have separate disposable-database evidence. Production identity and API connectivity remain unverified, and staff API stays disabled by default. |
| Evidence | TypeScript typecheck and Vite build pass; strict premium UI audit reports zero findings; the full Playwright suite passes 13 tests. | Local static/browser evidence only. No route-wide axe scan, screen reader review, independent WCAG/GIGW audit, or production deployment smoke was run. |

The conservative readiness verdict remains `NOT PRODUCTION READY`.
