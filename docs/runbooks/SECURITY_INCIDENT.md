# Security incident

## Symptoms

Suspected credential exposure, unauthorized access, data disclosure, integrity failure, hostile traffic or unexpected outbound action.

## Diagnosis

1. Contact the organization's security incident lead and preserve the relevant UTC/local timestamps, release ID, request IDs and system logs.
2. Scope affected accounts, routes, data classes, integrations, containers and backups using approved tooling.
3. Determine whether official or financial actions may have reached a remote system; reconcile with the authorized party.

## Safe action

Contain through the authorized edge or deployment operator. Revoke/rotate suspected credentials in the approved secret provider. Preserve evidence and avoid destructive cleanup until forensic needs are reviewed. Do not send external messages from this runbook without the incident lead's authorization.

## Verification

Require incident lead sign-off, verified credential rotation, clean redeployment, security tests, log review and a documented impact/notification decision.

## Rollback / escalation

Follow the organization's incident response plan and statutory/legal advice. This repository has no named incident owner or paging route.

## Data-risk notes

Assume personal data may be involved until scoped. Restrict access, preserve chain of custody and follow approved privacy-notification timelines.
