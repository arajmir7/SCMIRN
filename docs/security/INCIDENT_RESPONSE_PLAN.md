# Incident response plan — draft

**State:** operational draft pending organization-specific staffing, contact details, legal review and tabletop exercise. This is not evidence of a completed incident program.

## Roles

| Role | Responsibility | Assigned person/team |
|---|---|---|
| Incident commander | Severity, coordination, containment decision and incident log | `UNASSIGNED` — operator must appoint |
| Security lead | Triage, evidence preservation, scope and eradication | `UNASSIGNED` |
| Service/SRE lead | Availability, isolation, restore, monitoring and rollback | `UNASSIGNED` |
| Privacy/legal lead | Data-subject impact, statutory/contract notifications and advice | `UNASSIGNED` |
| Communications lead | Citizen, agency, vendor and public updates | `UNASSIGNED` |

## Response sequence

1. Detect from alerts, staff report, provider notice or citizen complaint; open an incident record and assign severity.
2. Preserve time, request IDs, deployment/image digests and relevant logs. Avoid copying unnecessary personal data into tickets.
3. Contain using API/connector kill switch, credential rotation, account revocation, tenant isolation, upload disablement or service isolation.
4. Determine affected data, users, systems, providers and government integrations; consult privacy/legal lead immediately for personal data or statutory obligations.
5. Eradicate cause, patch or rollback; validate with tests and independent review for high impact.
6. Recover from known-good release/backup; verify integrity, audit chain, queues and external connectors before reopening traffic.
7. Notify affected parties/agencies/regulators only through accountable organizational/legal authority and applicable timelines.
8. Complete lessons, controls and evidence retention; track actions to closure.

## Severity

- **P0:** suspected unauthorized access to citizen data, tenant crossover, privileged compromise, secret exposure, malicious deployment, false government submission or destructive data event.
- **P1:** exploitable high-severity vulnerability, broad outage, failed retention, suspected data integrity issue or connector behavior outside authorization.
- **P2:** limited defect without current evidence of exposure; monitor and remediate through change process.

## Evidence and contacts

Keep a restricted incident log, timestamps in UTC, hashes of preserved evidence and chain-of-custody details. Populate organization contacts, hosting/provider escalation contacts and legal reporting decision owner before deployment. Run tabletop exercise and record outcome; none is evidenced yet.
