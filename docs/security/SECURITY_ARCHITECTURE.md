# Security architecture and target controls

## Current verified shape

Canonical app: React/Vite SPA → Flask API → SQLAlchemy datastore and upload paths. Development/testing can use SQLite and `db.create_all()`; production config requires PostgreSQL and disables table auto-creation. Alembic head `20261002_03` describes all 34 ORM tables. Nine official pages have content hashes and four `OFFICIAL_HANDOFF_ONLY` service records can be listed; the cybercrime candidate is still gated by an unverified portal TLS certificate. No government filing or connector is enabled.

## Required production boundary

```mermaid
flowchart LR
  C[Citizen browser] -->|TLS, public limited APIs| W[Reverse proxy / WAF]
  W --> F[React static frontend]
  W --> A[Flask API]
  A --> DB[(PostgreSQL, least-privilege runtime role)]
  A --> O[(Private object store + malware scan)]
  A --> P[Approved external providers]
  M[Isolated migration job] -->|migrator credential| DB
  S[Monitoring / SIEM / immutable backup] <-- A
  G[Government connector] -. disabled until written approval .-> A
```

## Controls and current state

- **Identity/access:** a local staff password + TOTP flow, hashed opaque sessions, CSRF protection, lockout, password lifecycle, CLI provisioning and role guards are implemented for a bounded metadata-only case API. Unit tests and the end-to-end password/TOTP flow passed on disposable PostgreSQL 16 with a non-owner, non-BYPASSRLS role. OIDC/SAML, staff console, recovery/SSO, independent review and deployment-specific auth remain `NOT VERIFIED`. Staff routes remain disabled by default and require `STAFF_AUTH_ENABLED=true` plus a 32-byte secret-manager key.
- **Tenant isolation:** revision `20261002_03` defines forced PostgreSQL RLS for tenant/staff identity and case tables, tenant transaction scope, session-hash and same-tenant session-management scope, and composite tenant foreign keys. The full migration chain and these policies passed local disposable PostgreSQL 16 runtime-role tests, including cross-tenant read/write denials. Production database/runtime-role behavior remains unverified. Legacy citizen, issue, document, chat and route records remain outside a complete tenant model; the runtime DB role must not own tables or bypass policies.
- **Secrets:** use mounted secret manager or managed identity; never ZIP `.env`, plaintext environment, image layer, logs or browser bundle. Rotate any possibly exposed ZIP values through owner.
- **Data:** minimize free text/PII, encrypt in transit/at rest, separate public aggregates from case data, classify and delete by policy, and redact telemetry.
- **Audit:** append-only metadata, bounded schema, independent hash verification and external/WORM anchor; current chain is not externally immutable.
- **Uploads:** private storage, allowlisted formats, byte/signature validation, malware scanning, random names, size limits and authorized download URLs.
- **API:** strict schema validation, request IDs, no-store for sensitive results, rate limits, timeouts, idempotency for side effects, safe error envelopes.
- **AI:** deterministic route engine is preferred for source-backed handoff; block ungrounded legal claims, disclose limitations, allow human review and audit model/provider/version.
- **Integrations:** adapters disabled by default; enable only with written authorization, least-privileged credentials, sandbox evidence, timeout/retry/idempotency, kill switch and operational owner.
- **Supply chain:** Python/frontend dependency lockfiles and CycloneDX dependency SBOMs exist. A 2026-10-02 `pip-audit`/`npm audit` snapshot reported no known dependency vulnerabilities; image scanning, SAST, DAST, secret scanning, signed provenance and reviewed exceptions remain open. See [dependency scan evidence](DEPENDENCY_SCAN_2026-10-02.md).

No “secure” claim is supported by this design document. Independent testing and accountable operation remain required.
