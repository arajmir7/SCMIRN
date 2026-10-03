# CERT-In security readiness

**Assessment date:** 2026-10-03. **Status:** internal readiness notes only; no CERT-In certification, empanelled auditor assessment, approval or security clearance is claimed.

| Workstream | Evidence | Status / next step |
|---|---|---|
| Asset and component inventory | Canonical Flask/React tree and dependency-lock CycloneDX inventories | Partial; produce SBOMs for each exact release image and deployed assets. |
| Secure configuration | `scripts/validate_production_config.py` and production Compose validation exist | Local policy checks only; no authorized production secret, host, ingress, or identity configuration was reviewed. |
| Vulnerability management | Dated 2026-10-02 pip-audit/npm audit snapshots cover locked dependencies only; older ZIP SARIF for Redis/PostgreSQL is stale | Exact-release source, secret, image/OS, IaC, and DAST scans are absent; current findings must not be inferred from old snapshots. |
| Access control and logging | Staff password/TOTP, bounded case ABAC, PostgreSQL RLS roles, and metadata audit are locally tested | Incomplete identity/tenant model; redacted telemetry, external audit protection, and monitoring ownership remain open. |
| Incident process | Draft in `INCIDENT_RESPONSE_PLAN.md` and `INCIDENT_REPORTING_RUNBOOK.md` | Draft; confirm organization contacts, roles, reporting duties/timelines with counsel and operator. |
| Backup and recovery | No backup/restore or DR drill evidence | Not tested; perform encrypted restore drill, measure durations, and approve targets separately. |
| Penetration test | None in workspace | PENDING EXTERNAL AUDIT by an appropriately authorized assessor. |
| CERT-In obligations | Depend on organization/system/service facts and current law/directions | Legal/operator review required; verify current requirements before launch. |

The typed [production blocker ledger](../release/production-blockers.yaml) is the
current status source. Do not use “CERT-In certified” or imply an external
audit has occurred.
