# Incident reporting runbook

**Draft.** The operator and legal counsel must populate current notification routes and statutory/contractual deadlines before production.

## Intake

Record incident ID, discovery time (UTC), reporter, affected service, request IDs, suspected data classes, suspected tenant scope, current release/image digest, containment actions and decision owner. Store evidence in an access-controlled location; exclude raw citizen text and credentials from broad tickets.

## Triage checklist

- Is there evidence of unauthorized access, disclosure, alteration, loss or service disruption?
- Are accounts, API keys, database roles, government connectors or signing secrets affected?
- Are personal data, children's data, precise location, evidence files, legal documents or credentials involved?
- Which processors/hosting regions/agency systems may be affected?
- Can logs prove scope without adding more sensitive content?
- Has containment preserved critical audit and forensic evidence?

## Reporting decision

Incident commander coordinates with security, privacy/legal and affected system owners. Legal/operator counsel determines whether CERT-In, privacy, government/contract, law-enforcement or data-principal notices apply, who must submit, what content is lawful, and by when under current rules. Preserve the decision and submitted receipt in the restricted incident record. This runbook does not set a universal statutory deadline.

## Recovery and closure

Confirm fixes and credentials rotated; restore service from verified artifacts/backups; test the affected user and isolation boundaries; communicate status via approved channels; record timeline, root cause, impact, notification decisions, lessons and accountable corrective actions. Perform a tabletop before production and after a material incident.
