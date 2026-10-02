# Route matrix

## Public browser routes

| Product | Route | Entry | State |
|---|---|---|---|
| SCMIRN(3) source | `/` | `frontend/src/pages/LandingPage.tsx` + `CivicResolutionIntake` | Primary intake. |
| SCMIRN(3) source | `/services`, `/rights` | `GovernmentServices` | Source-verified catalog; expected empty because seed source is unavailable. |
| SCMIRN(3) source | `/documents`, `/progress`, `/file-complaint` | pages with explicit unavailable messaging | Not live document/case workflows. |
| SCMIRN(3) source | `/ai-help` | `AIAssistant` | UI calls disabled legacy AI endpoint. |
| SCMIRN(3) source | `/map`, `/offices`, `/tracker`, old issue/document aliases | React redirects | Redirects do not prove a feature exists. |
| SCMIRN(3) duplicate | nested `scmirn/frontend` routes | Vite scaffold | Not referenced by active Compose. |
| Canonical SCMIRN | `/` | `src/frontend/src/pages/HomePage.tsx` | Public home with current visual identity. |
| Canonical SCMIRN | `/offices`, `/heatmap`, `/tracker`, `/analytics`, `/documents`, `/platform` | React lazy routes in `src/frontend/src/App.tsx` | Existing visual routes; several display DB/demo/simulation data. |
| Canonical SCMIRN | unknown | React Router redirect to `/` | Current behavior. |

## Active source API routes

| Verb | Route | State / target |
|---|---|---|
| POST | `/api/v1/triage` | Active deterministic consented routing. |
| POST | `/api/v1/jurisdiction/resolve` | Alias to same resolver. |
| GET | `/api/v1/services` | Active, filters unverified sources. |
| GET | `/api/v1/services/{service_id}` | Active source-gated lookup. |
| POST | `/api/v1/evidence/check` | Active ID checklist; no file contents. |
| GET | `/api/v1/sources/{source_key}` | Active provenance record. |
| GET | `/health`, `/ready` | Runtime health/readiness. |

## Canonical APIs to preserve

Canonical route decorators are under `src/backend/app/api/v1/**`, `src/backend/app/core/services/geospatial_service/app/routes.py`, and the registered blueprints in `src/backend/app/__init__.py`. Families include issue/report/donation, AI and rights analysis, documents, office lookup, heatmap, IoT, blockchain simulation, gamification, resilience, twin simulation, city-brain simulation, enterprise simulation, SRS and health. They do not share source route semantics. The new triage API uses a separate `/api/v1/triage` route; it does not take over existing `/api/issues` or `/api/report-issue`.

## Merged production API boundary

In the canonical backend's `production` configuration, the request gate permits `GET /api/health`, `GET /api/v1/services` and service descendants, `GET /api/v1/sources/*`, and `POST /api/v1/triage`, `/api/v1/jurisdiction/resolve`, and `/api/v1/evidence/check`. Other `/api/*` and `/uploads/*` requests return `503 PRODUCTION_ENDPOINT_DISABLED`. `SCMIRN_MIGRATION_MODE=true` blocks all application HTTP requests while migrations run. These controls have unit coverage, but have not been exercised behind a deployed ingress or against PostgreSQL.

The service catalog has no verified official source configured. It therefore returns no eligible official handoff. The permitted routes provide deterministic routing/evidence checks only; they do not file complaints, upload evidence, process payments, or retrieve official case status. Legacy APIs remain present for local prototype routes but are disabled by the production gate.

## Not active in source runtime

Flask `backend/app/agents/**` controllers are not registered by the active `backend/app/__init__.py`. The TypeScript Fastify app at `backend/src/**` is not started by Compose, which launches Python `run:app`. Source React paths not wired to API can show unavailable pages, not usable service. Treat these as unreachable, not missing integrations.
