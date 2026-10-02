# Operations model

**State:** target operating model; no production operator or duty roster was supplied.

## Roles

- **Product/service owner:** public scope, help/grievance content and release acceptance.
- **Agency data/content owner:** official sources, service records, legal dates and correction path.
- **SRE/operator:** deployment, monitoring, backup/restore, availability and rollback.
- **Security/privacy lead:** access review, incident response, vulnerability and retention evidence.
- **Support/grievance staff:** citizen questions, escalation and correction requests.
- **External auditor:** independent penetration/STQC/security review; not an internal engineering role.

## Daily/weekly operations

- Check availability/readiness, error/latency, queue/retention lag, auth failures and suspicious traffic.
- Review service/source expiry and mark routes unavailable when evidence becomes stale.
- Review backups, restore sampling, disk/storage, upload malware scan and secret expiry.
- Triage user grievances, privacy requests and incident reports through approved restricted systems.
- Release only signed, scanned artifacts with migration/rollback evidence and named approver.

## Missing production inputs

Named operator, support contact, escalation tree, SLO/SLA, maintenance window, recovery target, on-call schedule, data-owner roster and agency integration owner are `UNASSIGNED`. Complete these before pilot.
