# External connector unavailable

## Symptoms

No government connector is enabled in production. Any screen or alert claiming a connected service must be treated as a defect until independently verified.

## Diagnosis

1. Confirm the capability declaration and release configuration. Current public routing is `NOT_SUBMITTED`.
2. If an external connector exists outside this repo, check its owner, agency sandbox/production state, credentials, certificate, request ID and official receipt channel.
3. Determine whether the remote action was accepted before considering any retry.

## Safe action

Do not retry a possibly submitted request blindly. Mark remote state unknown and reconcile with the agency through the authorized process. Do not tell a citizen an action was filed or failed without authoritative evidence.

## Verification

Require an authenticated test tenant, idempotent request, verified acknowledgement/receipt, audit trail and operator sign-off. No such integration test currently exists.

## Rollback / escalation

Escalate to the named agency integration owner. Keep the connector disabled until reconciliation and rollback controls pass.

## Data-risk notes

Treat request identifiers and payloads as personal/high-risk data. Do not paste citizen content or credentials into logs.
