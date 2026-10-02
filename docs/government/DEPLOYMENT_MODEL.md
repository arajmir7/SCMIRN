# Deployment model

## Current verified local model

Canonical public frontend is React/Vite and Flask serves APIs. Development remains SQLite. A separate production-oriented Compose rehearsal used disposable PostgreSQL 16 and Redis 7 with verified TLS/hostnames, applied migration `20261001_01`, checked health/proxy routes and confirmed safe routing abstention. This is local integration evidence only; no production deployment, external HTTPS termination, DNS, secrets provider, backup/restore or rollback was exercised.

## Target deployment boundary

```mermaid
flowchart TB
  Citizen[Citizen browser] --> Edge[TLS reverse proxy / WAF]
  Staff[Authorized staff] --> Edge
  Edge --> Static[React static assets]
  Edge --> API[Flask API]
  API --> PG[(PostgreSQL primary + encrypted backup)]
  API --> Files[Private scanned object storage]
  API --> Providers[Approved providers only]
  Migration[Isolated migration job] --> PG
  Logs[Monitoring / SIEM] <-- API
  Agency[Agency endpoint] -. disabled until approval .-> API
```

## Deployment gates

- Separate environments and secret stores; no `.env`/ZIP files in images.
- Non-root containers, pinned images, least-privilege runtime DB role, separate migration role.
- TLS, security headers, restrictive CORS, rate limits, health/readiness checks and bounded timeouts.
- Versioned migration, backup, restore, rollback and image digest recorded per release.
- No demo seeding, synthetic metrics or connector credentials in production.
- Government integration remains disabled until written authority, sandbox validation and accountable owner.

This is a target topology, not proof of an existing production deployment.
