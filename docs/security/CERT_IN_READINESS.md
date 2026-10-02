# CERT-In security readiness

**Status:** internal readiness notes only; no CERT-In certification, empanelled auditor assessment, approval or security clearance is claimed.

| Workstream | Evidence | Status / next step |
|---|---|---|
| Asset and component inventory | Canonical Flask/React tree; source component inventory under `docs/compliance/stqc/` | Partial; produce SBOM for exact release image and deployed assets. |
| Secure configuration | Production gate code exists in source archive; canonical uses dev/SQLite defaults | Not verified; implement production config and secret provider, reject placeholders. |
| Vulnerability management | ZIP SARIF snapshots have 9 Redis and 24 Postgres HIGH/CRITICAL entries, status/date unclear | Not verified; rescan exact current dependencies/images, remediate and retain signed output. |
| Access control and logging | Hash-chain prototype tests; canonical protected roles/tenant scope incomplete | Not verified; implement and test; external log protection/monitoring needed. |
| Incident process | Draft in `INCIDENT_RESPONSE_PLAN.md` and `INCIDENT_REPORTING_RUNBOOK.md` | Draft; confirm organization contacts, roles, reporting duties/timelines with counsel and operator. |
| Backup and recovery | No production backup/restore evidence | Not tested; perform restore drill and validate RPO/RTO. |
| Penetration test | None in workspace | PENDING EXTERNAL AUDIT by an appropriately authorized assessor. |
| CERT-In obligations | Depend on organization/system/service facts and current law/directions | Legal/operator review required; verify current requirements before launch. |

Do not use “CERT-In certified” or imply an external audit has occurred.
