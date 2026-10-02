# Database unavailable

## Symptoms

- `/api/ready` returns 503 with `{"status":"not_ready"}`.
- Backend health check remains unhealthy or migration job fails.

## Diagnosis

1. Check `scripts/deploy.sh status` and `scripts/deploy.sh logs` using the approved release environment.
2. Verify database provider status, DNS, network allowlist, credentials, CA mount and `sslmode=verify-full` from the backend runtime.
3. Separate a connection/TLS issue from an unavailable PostgreSQL service; never print the full database URL into a ticket or terminal log.

## Safe action

Keep the service out of rotation while readiness fails. Do not bypass TLS, change to SQLite, rerun destructive DDL, or restore over the source database. Ask the database operator to recover the service and preserve the incident timeline.

## Verification

Require a successful `SELECT 1`, `/api/ready`, migration state review and representative read-only integrity checks before re-enabling traffic.

## Rollback / escalation

Escalate to the named database operator. Use [`RESTORE.md`](RESTORE.md) only under the approved recovery plan. A prior application image does not repair database loss.

## Data-risk notes

Uncommitted writes may be absent or uncertain. The application has no verified multi-tenant protection or production PITR evidence; do not promise recovery point or time.
