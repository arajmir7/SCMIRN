# Database restore

## Symptoms

Database corruption, data loss, provider outage requiring recovery, or a declared recovery exercise.

## Diagnosis

Confirm incident authority, selected backup timestamp, encryption/key availability, target isolation, expected RPO/RTO and source database state. Preserve the source until the data owner authorizes recovery.

## Safe action

Restore only to a fresh isolated target first. Never overwrite the source database as an exploratory step. Do not restore real citizen data into an unapproved environment or weaker access boundary.

## Verification

Boot the matching application release; validate schema/migration head, row counts and constraints on approved representative records, audit-chain verification and application readiness. Record wall-clock restore duration and compare with approved targets.

## Rollback / escalation

Escalate to the database/data owner if keys, backup integrity or schema compatibility is uncertain. Promote the restored target only under the approved failover plan.

## Data-risk notes

No backup/restore rehearsal or production backup service is verified in this repository. RPO/RTO values in `docs/operations/SLO.md` are proposals only.
