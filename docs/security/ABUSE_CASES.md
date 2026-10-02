# Abuse cases and security test plan

| ID | Abuse case | Required test / expected outcome | Current evidence |
|---|---|---|---|
| AB-01 | Access a protected staff API without credentials | 401/403; no data mutation | Staff auth tests pass; login/MFA and case APIs also passed on disposable PostgreSQL 16 as a non-owner, non-BYPASSRLS role. Production ingress remains unverified. |
| AB-02 | Cross-tenant case IDOR | Tenant A cannot read tenant B's case; database RLS also denies | SQLite API returns 404; disposable PostgreSQL test confirms cross-tenant reads and writes are denied. Legacy issue/audit/document records remain outside this staff tenant boundary. |
| AB-03 | Caller changes role/tenant through mass assignment | Server derives tenant and principal; only bounded case type/priority accepted | Local case API tests cover role denial and ignore extra description input. No route-wide schema test. |
| AB-04 | Expired/revoked staff session | Deny access; revoked session cannot be reused | Unit tests cover idle expiry, logout/password revocation path, and one-use MFA challenge; disposable PostgreSQL test exercises session-hash scope and revocation. |
| AB-05 | CSRF against cookie-authenticated operations | Double-submit token blocks mutation; cookie is HttpOnly for session and Strict same-site | Local missing-token test passes; no browser-origin or deployed cross-origin test. |
| AB-06 | SQL/NoSQL/template injection | Parameterized queries and safe template rendering | Not comprehensively tested. |
| AB-07 | Stored/reflected XSS in report, chat or document | Payload rendered as text; CSP blocks unsafe execution | Not comprehensively tested. |
| AB-08 | SSRF through source URL, maps or connector fields | URL allowlist, redirect/DNS/IP checks; no arbitrary fetch | Source code has no runtime fetch; future adapters remain disabled. |
| AB-09 | Malicious/oversized/invalid-MIME upload | Reject by size, extension, signature and scan; store outside executable web root | Not tested. |
| AB-10 | Replay/idempotency conflict | Same key/same content returns same outcome; changed input conflicts; no duplicate side effect | Source backend has 1 unit contract test; canonical report routes not idempotent. |
| AB-11 | Abuse public endpoints | Per-IP/account limits, payload bounds, alerting and graceful 429 | Baseline only some route decorators; triage limits need verification. |
| AB-12 | Prompt injection asks for secret/data/legal fabrication | Assistant refuses data/tool exfiltration and labels unsupported law/status | Not tested; canonical AI not source-grounded. |
| AB-13 | False official handoff through stale/missing source hash | No handoff unless all sources meet verification gate; no submission reference | Source backend negative tests pass; source frontend tests not run. |
| AB-14 | Audit tampering | Update/delete trigger blocks normal writer; verifier flags altered chain; access alarms | Disposable PostgreSQL test confirms case and staff audit history rejects update/delete. External anchoring and privileged-owner tampering remain untested. |
| AB-15 | Demo data shown as real activity or donated funds | Production refuses fixture seed/simulation; UI labels demo state | Canonical first-empty-read seed and donation path require correction. |

Release security suite must add tests for every applicable row, including both allow and deny paths. Passing unit tests is not an external security assessment.
