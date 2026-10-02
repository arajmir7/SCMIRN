# Application rollback

## Symptoms

Release health fails, production smoke regresses, or the operator detects a release-specific defect.

## Diagnosis

Record current release ID, previous retained image ID/digest, migration head, health/smoke result and whether the schema changed. Confirm compatibility with the previous binary before action.

## Safe action

Use an approved change window. Set `SCMIRN_RELEASE_ID` in the protected environment file to the retained prior build and run `SCMIRN_ENV_FILE=.env.production scripts/deploy.sh rollback`. The helper refuses to build/pull missing images, does not restart the migration service, and checks readiness, frontend root/nested route, and disabled API boundary. It does not reverse migrations.

## Verification

Check readiness, representative read-only behavior, error rate, and release/image identity. Obtain operator approval for any schema or traffic change.

## Rollback / escalation

If the old image is incompatible or recovery does not succeed, stop further automated retries and escalate to the deployment/database owners. Restore through [`RESTORE.md`](RESTORE.md) only when data loss is confirmed and the restore plan is approved.

## Data-risk notes

No rollback rehearsal has passed. Schema compatibility, previous image retention and remote deployment behavior are not verified. Do not promise no data loss.
