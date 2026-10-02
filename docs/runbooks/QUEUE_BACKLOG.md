# Queue backlog

## Symptoms

There is no production queue, broker, or queue-depth metric in the canonical Compose stack. A queue backlog alert therefore indicates an external/future component, not a current SCMIRN service.

## Diagnosis

1. Identify the actual broker, environment, consumer, and release owner from the deployment record.
2. Inspect queue depth, oldest-message age, retry rate, dead-letter count, consumer health, and schema compatibility.
3. Check whether any external side effect may already have occurred before retrying a message.

## Safe action

Do not purge, replay, or bulk-acknowledge messages without a reviewed runbook for that broker. If any official action is involved, hold retries until remote state is reconciled.

## Verification

Require backlog trend recovery, deduplication proof, poison-message review and a synthetic end-to-end check. This repo currently cannot provide those signals.

## Rollback / escalation

Escalate to the owner of the separately deployed broker/worker. Disable the relevant future feature flag if it exists and is audited.

## Data-risk notes

Messages may contain personal data. Restrict access and avoid copying payloads into logs or support tickets.
