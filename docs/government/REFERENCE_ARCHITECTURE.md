# SCMIRN reference architecture

## Implemented repository architecture

SCMIRN is currently a modular monolith: a React/TypeScript/Vite frontend and Flask application with SQLAlchemy, Alembic, PostgreSQL production configuration, Redis-backed cache/rate-limit configuration, and deterministic `source_routing`. Alembic head `20261003_01` covers all 35 ORM tables. Staff password+TOTP, tenant roles, a metadata-only case API, a private evidence vault, and an initial `/staff` browser UI are implemented; the full migration chain, four database roles and staff/evidence RLS passed disposable PostgreSQL 16 tests. Browser staff API responses are mocked; production database/runtime-role, service connectivity, identity-provider and end-to-end deployment validation remain open. Personalized triage/jurisdiction routes are disabled in production because decision storage lacks a complete subject/tenant boundary. No durable worker contract, approved production object store or government connector runtime is verified.

```mermaid
flowchart LR
  Browser[Citizen browser] --> UI[React frontend]
  UI --> API[Flask API]
  API --> Route[Deterministic source routing]
  Route --> Registry[(Versioned source and service registry)]
  Route --> Decisions[(Bounded decision and audit metadata)]
  API --> PG[(PostgreSQL in production configuration)]
  API --> Redis[(Redis cache and rate limiting)]
  API --> Staff[Opt-in staff MFA and metadata-only case API]
  Staff --> RLS[PostgreSQL tenant RLS policy; disposable PG16 test passed]
  Route -. no verified connector enabled .-> Agency[Government service]
```

## Safe routing boundary

The local/test route path requires explicit consent, applies versioned phrase rules, checks active effective dates and verified source hashes, checks exact source-host alignment for handoff URLs, requires matching configured geography for local services, and stores bounded derived facts. Raw triage descriptions are not stored by this path; tests verify that property. Production triage is denied by the API allowlist until route-decision subject/tenant isolation is implemented. Five official handoff candidates are imported; four currently pass recorded source/hash/host checks. The cybercrime portal candidate stays hidden while its source review is unresolved. All catalog actions remain `OFFICIAL_HANDOFF_ONLY`; `NOT_SUBMITTED` and null official reference remain explicit.

## Target deployment (not deployed)

An agency-approved deployment must validate PostgreSQL RLS with its configured non-owner runtime role, add tenant ownership for legacy records, and may require an identity provider, private scanned object storage, durable workflow worker, egress-restricted connectors, and SIEM/metrics/tracing. The local PostgreSQL test is not deployment evidence. Each component requires an accountable operator and tested controls before use. See [`DEPLOYMENT_MODEL.md`](DEPLOYMENT_MODEL.md), [ADRs](../architecture/adr/README.md), and [deployment architecture](../DEPLOYMENT_ARCHITECTURE.md).
