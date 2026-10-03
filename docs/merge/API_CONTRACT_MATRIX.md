# API contract matrix

## Integrated canonical source-routing API

The Flask routing blueprint is mounted at `/api/v1`; the staff identity blueprint is mounted at `/api/v1/staff`. The production gate permits source/health operations plus opt-in staff operations; staff APIs require explicit config and a valid production MFA key. Four official handoff candidates pass local source checks, but production registry seeding is an operator action.

| Method/path | Request | Response / errors | Auth / state / target |
|---|---|---|---|
| `POST /api/v1/triage` and `/api/v1/jurisdiction/resolve` | JSON `description` (1–8000), optional `state`/`district` (<=120), required `consent_to_process=true`; optional `Idempotency-Key` <=128 | 200 route result or explicit `ROUTE_UNCERTAIN`, `JURISDICTION_AMBIGUOUS`, `URGENT_HUMAN_HELP_REQUIRED`, `OFFICIAL_HANDOFF_ONLY`; 400 invalid/consent; 409 key conflict. Result includes `submission_status=NOT_SUBMITTED`, null official reference, versions and sources. | Public, rate-limited, no authentication or per-tenant boundary; description is not stored. Production allowlisted. |
| `GET /api/v1/services` | none | `{items: ServiceSummary[], count}`; four local `OFFICIAL_HANDOFF_ONLY` records have date-only internal source-review metadata. | Public discovery listing; production allowlisted; production seed remains operator-controlled. Review dates are not live checks, and other connector modes are filtered out. |
| `GET /api/v1/services/{service_id}` | service identifier | ServiceSummary or 404 | Public; production allowlisted. |
| `POST /api/v1/evidence/check` | `{service_id: string, provided_evidence_ids?: string[]}` max 100 | checklist status `READY`, `INCOMPLETE`, `UNCONFIGURED`, `SOURCE_UNVERIFIED`, `SERVICE_UNAVAILABLE`; 400 bad input. Does not accept evidence file contents. | Public, rate-limited; production allowlisted. |
| `GET /api/v1/sources/{source_key}` | path key | source provenance, hash, dates, status/review state; 404 missing | Public, rate-limited; production allowlisted; never interpret DRAFT or REVOKED as usable. |
| `POST /api/v1/staff/auth/login` | tenant slug, email, password | Signed short-lived MFA challenge; no session yet; generic 401 on failure and 429 on limit. | Operator-provisioned staff only; disabled unless explicitly enabled. |
| `POST /api/v1/staff/auth/mfa` | challenge, six-digit TOTP | One-use challenge, replay-protected TOTP, hashed opaque session cookie and CSRF cookie. | Requires active staff account and factor; production key must be configured. |
| `POST /api/v1/staff/auth/mfa/enroll/confirm` | tenant slug, operator-delivered token, TOTP | Activates provisioned TOTP factor; token is consumed once. | Rate-limited; enrollment values are emitted once by the operator CLI. |
| `GET /api/v1/staff/auth/me` | HttpOnly staff session cookie | Current tenant-bound staff identity and roles. | Authenticated staff; disabled by default in production. |
| `POST /api/v1/staff/auth/logout` | session cookie + CSRF header | Revokes current session and clears cookies. | Authenticated staff, CSRF required. |
| `POST /api/v1/staff/auth/password/change` | current/new password + session + CSRF header | Changes password and revokes all staff sessions. | Authenticated staff; password policy enforced. |
| `GET/POST /api/v1/staff/cases` | GET: session; POST: case type/priority + CSRF | List or create bounded metadata-only cases. No free text or upload accepted. | Tenant admin/case officer writes; admin/officer/auditor reads. |
| `GET /api/v1/staff/cases/{case_id}` | session | Tenant-filtered case metadata and status events; cross-tenant IDs return 404. | Tenant admin/case officer/auditor. |
| `POST /api/v1/staff/cases/{case_id}/status` | status + session + CSRF | Validated status transition plus append-only metadata event. | Tenant admin/case officer; production RLS still awaits PostgreSQL verification. |
| `GET /api/health` | none | process health | Production allowlisted; not a readiness certification. |

## Source endpoints disabled or dormant

| Path family | Active behavior | Disposition |
|---|---|---|
| `/api/issues*`, `/api/tracker*`, `/api/offices*` | 410/503 legacy unavailable responses | Not copied as source functionality. |
| `/api/documents*`, `/api/ai*` legacy | 410 with provenance/evidence limitations | Not copied; canonical API is inventoried separately. |
| `/api/agents*` | Agent controllers are not registered from active Flask app | `UNREACHABLE`. |
| Fastify `/api/v1/*` in `backend/src/routes` | Not started by active Compose/runtime | `UNREACHABLE`; no route-contract merge. |

## Legacy API overlap and boundary

Canonical Flask still registers `/api/issues`, `/api/report-issue`, `/api/donate`, `/api/tracker/summary`, `/api/analytics/summary`, `/api/rights/analyze`, `/api/ai-assistant`, `/api/documents/*`, `/api/offices`, and `/api/v1/{iot,blockchain,ai,gamification,resilience,twin,city-brain,enterprise,scmirn}` for local compatibility/demo behavior. The production gate returns 503 for these families and `/uploads/*`; both donation handlers independently return 503 without changing funds. No legacy endpoint is silently reinterpreted as source routing.

## Canonical resolution contract to adopt

The integrated browser client uses the source JSON contract and outcome vocabulary. OpenAPI states that no endpoint files a government complaint. Do not return an active source or handoff merely because a registry row exists: require HTTPS canonical URL, current effective dates, catalog status `VERIFIED`, a recorded exact verification timestamp or date-only internal verification date, 64-hex document hash, and service/authority/rule consistency. This validates stored catalog metadata; it does not re-fetch the official page or confirm currentness.
