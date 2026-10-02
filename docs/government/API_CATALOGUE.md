# API catalogue

The machine-readable contract is [`../enterprise/openapi-enterprise.yaml`](../enterprise/openapi-enterprise.yaml), OpenAPI 3.1. The production route/method gate allows 15 source/health/staff paths; staff APIs remain disabled unless `STAFF_API_ENABLED=true` and the production MFA key passes validation. Its synthetic check verified that 93 other registered API operations return 503. This is a local configuration test, not an external ingress or PostgreSQL auth test.

| Method and path | Purpose | Production boundary |
|---|---|---|
| `GET /api/health` | Liveness | Public health only. |
| `GET /api/ready` | Dependency readiness | Public readiness response; configured dependency failures fail closed. |
| `POST /api/v1/triage` | Consented source-gated route decision | Four reviewed handoff candidates are available locally; no filing. Rate-limited; abuse review remains open. |
| `POST /api/v1/jurisdiction/resolve` | Compatibility route to deterministic resolver | Same source/consent restrictions as triage. |
| `GET /api/v1/services` | List currently verified active services | Local catalog lists four source-checked handoffs; production database seeding is an explicit operator action. |
| `GET /api/v1/services/{service_id}` | Read a service record | Details are limited to source-checked handoff metadata. |
| `POST /api/v1/evidence/check` | Check evidence metadata for a source-backed service | No file upload or evidence vault; checklist is metadata-only. |
| `GET /api/v1/sources/{source_key}` | Read source metadata | Cybercrime portal candidate is DRAFT and hidden; other source records remain subject to freshness review. |

The staff API adds password+TOTP login, enrollment confirmation, current identity, logout/password change, and a tenant-filtered metadata-only case workflow. Cases have bounded types/status transitions; caller-supplied text and uploads are not accepted. Staff RLS passed a disposable PostgreSQL 16 test with a non-owner, non-BYPASSRLS role. Production staff access is opt-in and must remain disabled until the deployment database role/configuration and operational controls are reviewed. The contract does not certify the registered but gated legacy APIs.
