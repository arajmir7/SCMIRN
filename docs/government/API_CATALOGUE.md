# API catalogue

The machine-readable contract is [`../enterprise/openapi-enterprise.yaml`](../enterprise/openapi-enterprise.yaml), OpenAPI 3.1. The production route/method gate allows 15 source/health/staff paths; staff APIs remain disabled unless `STAFF_API_ENABLED=true` and the production MFA key passes validation. The 2026-10-03 synthetic check verified that 99 other registered API operations return 503. This is a local configuration test, not an external ingress or PostgreSQL auth test.

| Method and path | Purpose | Production boundary |
|---|---|---|
| `GET /api/health` | Liveness | Public health only. |
| `GET /api/ready` | Dependency readiness | Public readiness response; configured dependency failures fail closed. |
| `POST /api/v1/triage` | Consented source-gated route decision | Development/test only; production allowlist returns 503 until route-decision subject/tenant isolation is implemented. |
| `POST /api/v1/jurisdiction/resolve` | Compatibility route to deterministic resolver | Development/test only; same production-disabled boundary as triage. |
| `GET /api/v1/services` | List active, date-reviewed `OFFICIAL_HANDOFF_ONLY` service records | Local catalog currently lists four dated internal source-review records; this is not a live source check. Production database seeding is an explicit operator action. |
| `GET /api/v1/services/{service_id}` | Read a listed handoff record | Details include dated review metadata and source hashes. The official page may have changed since that review. |
| `POST /api/v1/evidence/check` | Check evidence metadata for a source-backed service | Checklist is metadata-only. A separate restricted staff evidence vault exists in code, but its routes are disabled in production pending approved storage/scanner/retention operations. |
| `GET /api/v1/sources/{source_key}` | Read source metadata | Exact retrieval/verification timestamps remain null when not recorded. Catalog records carry a 2026-10-02 internal review date; there is no scheduled drift review. |

`/services` is a public discovery directory. It returns only `OFFICIAL_HANDOFF_ONLY` records; connected, sandbox, unauthorized, planned, and unavailable modes are not routable through this resolver. The browser displays source URLs, SHA-256 hashes, scope/exclusion metadata, and the recorded internal review date, and only renders a same-host HTTPS action when source status/hash/date checks pass. It does not submit data or create a government reference.

The staff API adds password+TOTP login, enrollment confirmation, current identity, logout/password change, and a tenant-filtered metadata-only case workflow. Cases have bounded types/status transitions; caller-supplied text and uploads are not accepted. Staff RLS passed a disposable PostgreSQL 16 test with a non-owner, non-BYPASSRLS role. Production staff access is opt-in and must remain disabled until the deployment database role/configuration and operational controls are reviewed. The contract does not certify the registered but gated legacy APIs.
