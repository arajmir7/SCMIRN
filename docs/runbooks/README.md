# Operator runbooks

These are decision and containment guides for the current prototype. Commands against a named production environment require the designated operator's change window and approved secrets procedure. The local Compose checks do not establish a live on-call service.

| Runbook | State |
|---|---|
| [DATABASE_DOWN](DATABASE_DOWN.md) | Production PostgreSQL is external; no automated failover is configured. |
| [REDIS_DOWN](REDIS_DOWN.md) | Readiness fails closed when production Redis is unavailable. |
| [QUEUE_BACKLOG](QUEUE_BACKLOG.md) | No queue is currently deployed. |
| [CONNECTOR_DOWN](CONNECTOR_DOWN.md) | No government connector is enabled. |
| [AUTH_FAILURE](AUTH_FAILURE.md) | Production identity federation is not configured. |
| [AI_RUNTIME_DOWN](AI_RUNTIME_DOWN.md) | Production source-gated routing is deterministic; legacy AI is disabled. |
| [OBJECT_STORAGE_DOWN](OBJECT_STORAGE_DOWN.md) | No production object store is configured; upload routes are disabled. |
| [AUDIT_FAILURE](AUDIT_FAILURE.md) | Routing/audit writes are part of PostgreSQL transactions; no external anchor is configured. |
| [SECURITY_INCIDENT](SECURITY_INCIDENT.md) | Requires an accountable organization contact and approved incident process. |
| [ROLLBACK](ROLLBACK.md) | Release-ID rollback helper exists; rehearsal is not yet verified. |
| [RESTORE](RESTORE.md) | Restore is a required operator gate; no restore rehearsal is verified. |

Every capability marked absent remains absent during incident handling: do not fabricate queue, filing, receipt, identity, object-storage, or official-status outcomes.
