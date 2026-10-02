# SCMIRN

SCMIRN is a civic technology prototype. The canonical application is a React/Vite frontend in `src/frontend` and a Flask API in `src/backend`.

**Status (2026-10-02): not production ready.** SCMIRN has no government deployment, agency account, approved filing connector, certified legal content, or external compliance certification. Do not enter real citizen, case, contact, or identity data in the demo. Local verification includes 65 backend tests, a disposable PostgreSQL 16 tenant/RLS integration, and a 17-path production API allowlist; these checks do not establish deployment readiness.

## Available workflow

The Problem Solver submits a description only after explicit consent. The Flask route service uses deterministic, versioned rules, stores bounded derived facts rather than the raw description, applies an idempotency key, and sets a 30-day deletion deadline. It reports `NOT_SUBMITTED`; SCMIRN does not file a request with an agency. An official handoff is displayed only when the route has a current verified HTTPS source with a valid SHA-256 content hash.

The source registry contains five official handoff candidates; four currently pass source/hash/host checks, and the cybercrime candidate remains `DRAFT` after standard TLS validation failed. Each available destination remains a public handoff only; the route does not file with an agency or create an official receipt. Emergency signals return a human-help warning and no authority.

The issue map, office directory, tracker, analytics, IoT, legal, resilience, digital twin, city-organism, enterprise and blockchain workspaces are local demos or simulations. Their records are not independently verified or connected to government systems. Report submission saves only a local SCMIRN demo record. Document output is an unreviewed template. Payments are disabled; the API returns `503` without changing funding totals.

## Run locally

Frontend, from `src/frontend`:

```sh
npm ci
npm run dev
```

Backend, from `src/backend`:

```sh
python -m venv .venv
source .venv/bin/activate
pip install --require-hashes -r requirements-dev.lock
APP_CONFIG=development flask --app wsgi:app run --port 5000
```

Development uses SQLite, creates tables for local development and seeds only the source-routing candidate. `DEMO_MODE` is enabled by default for local demos; it must never be enabled for public use. Use synthetic data only.

## Source-routing operations

The routing API is under `/api/v1`:

- `POST /api/v1/triage` — requires `consent_to_process: true`; send an `Idempotency-Key` header.
- `GET /api/v1/services` — lists only source-verified active services.
- `POST /api/v1/evidence/check` — checks evidence identifiers without accepting uploaded evidence.
- `GET /api/v1/sources/<source_key>` — returns the source record and verification state.

Operator commands:

```sh
flask --app wsgi:app seed-routing-registry
flask --app wsgi:app purge-route-decisions --dry-run
flask --app wsgi:app verify-route-audit-chain
```

The retention purge is a CLI operation; no production scheduler is configured. Set up monitoring and scheduling only after an operator, retention policy and PostgreSQL environment have been reviewed.

## Production boundary

`APP_CONFIG=production` requires environment-provided 32-character secrets, a `postgresql+psycopg://` database URL, a TLS `rediss://` Redis URL for caching and rate limits, and HTTPS CORS origins. Do not use a `.env` file for production secrets.

The production Compose profile is separate from the local development stack. Copy `.env.production.example` to `.env.production`, replace every placeholder, set an unused `SCMIRN_RELEASE_ID`, and protect the file as a secret. `scripts/deploy.sh validate` checks production policy and Compose configuration; `build` and `deploy` refuse to reuse backend or frontend release tags already present locally; `deploy` runs the schema migration, starts services, waits for health checks, and smoke-checks the frontend root, a nested route, proxied API readiness, and one disabled legacy API. `rollback` starts retained local images for the release ID in the environment file and never builds or pulls them. `status`, `logs`, and `stop` are also available. The script does not provision PostgreSQL/Redis, establish a TLS reverse proxy, or deploy to a remote host.

The web container binds to `127.0.0.1` on `SCMIRN_HTTP_PORT` (default `8080`). Put a separately managed HTTPS reverse proxy in front of it and set `CORS_ORIGINS` to the public HTTPS origin. The backend has no published host port. The Compose profile requires:

- `SCMIRN_SECRET_KEY` and `SCMIRN_JWT_SECRET_KEY` — independent random secrets, each at least 32 characters.
- `SCMIRN_RELEASE_ID` — an immutable, non-placeholder image tag for this release.
- `DATABASE_URL` — PostgreSQL with the installed Psycopg 3 SQLAlchemy driver; use TLS and certificate verification for remote databases.
- `REDIS_URL` — `rediss://` URL for TLS-protected Redis.
- `SCMIRN_POSTGRES_CA_FILE` and `SCMIRN_REDIS_CA_FILE` — absolute paths to the CA certificates mounted read-only for hostname and certificate verification. Connection URLs must include `sslmode=verify-full&sslrootcert=/run/postgres-ca.crt` and `ssl_ca_certs=/run/redis-ca.crt&ssl_cert_reqs=required&ssl_check_hostname=true`, respectively. Redis hostname verification is explicit because redis-py 5.x defaults it off; redis-py connection URLs accept TLS options via query parameters ([documentation](https://redis.readthedocs.io/en/stable/connections.html)).
- `CORS_ORIGINS` — comma-separated HTTPS origins only.
- `SCMIRN_HTTP_PORT` — optional loopback port for the HTTPS proxy upstream.

The one-shot migration container runs with `SCMIRN_MIGRATION_MODE=true`; this blocks all HTTP traffic in that container while Alembic runs. The application container starts only after the migration exits successfully. Alembic head `20261002_03` covers the current 34 ORM tables. Staff authentication and metadata-only case endpoints are present but disabled by default; staff/case RLS passed against a disposable PostgreSQL 16 runtime role. Production database role validation, RLS for legacy citizen/report/document/chat/route data, and production migration/restore rehearsals remain open. The production API allowlist documents 17 paths; 91 other registered API operations are rejected. Legacy reporting, uploads, documents, offices, tracking, analytics and simulation APIs remain unavailable.

The retention purge is not scheduled by this stack. Configure and monitor an operator-controlled scheduled job only after the retention policy and operational owner are approved. Database backup, restore, point-in-time recovery, TLS proxy configuration, external audit, and production smoke beyond the script's local checks are not configured or verified. Before a pilot, define the database provider's backup policy and demonstrate restoration into an isolated environment.

To apply the routing schema manually from `src/backend` in an isolated operator job:

```sh
APP_CONFIG=production SCMIRN_MIGRATION_MODE=true flask --app wsgi:app db upgrade
```

Unset `SCMIRN_MIGRATION_MODE` before starting the application. Production configuration and the migration path have local code-level checks, but still require environment-specific verification. Route/audit and legacy-data tenant isolation, production database least-privilege validation, retention scheduling, backup/restore, current source/container scanning, legal review, accessibility review and external assessments remain open.

## Verification

From `src/frontend`:

```sh
npm run typecheck
npm run build
npm run test:e2e
```

From `src/backend`:

```sh
python -m pytest tests -q
```

The evidence and limitations are tracked in [`docs/merge/TEST_EVIDENCE_MATRIX.md`](docs/merge/TEST_EVIDENCE_MATRIX.md), [`docs/merge/GOVERNMENT_READINESS_MATRIX.md`](docs/merge/GOVERNMENT_READINESS_MATRIX.md), and [`docs/release/evidence/README.md`](docs/release/evidence/README.md). The ZIP inventory and disposition are documented under [`docs/merge`](docs/merge/).

## Troubleshooting

- `scripts/deploy.sh validate` reports a missing environment variable: confirm `.env.production` exists, uses unquoted `KEY=VALUE` entries, and contains no example placeholders.
- Migration fails: check external PostgreSQL DNS/TLS/credentials, PostgreSQL reachability from Docker, and the migration container logs with `scripts/deploy.sh logs`.
- Backend stays unhealthy: confirm PostgreSQL migration completed, TLS Redis is reachable from the backend network, and the configured URLs use `postgresql+psycopg://` and `rediss://`.
- Browser requests fail through the proxy: check that `/api/` is forwarded to the frontend container unchanged and that the proxy serves the site over HTTPS.
- The deployment smoke check is not a backup, security, accessibility, government integration, or production approval.
