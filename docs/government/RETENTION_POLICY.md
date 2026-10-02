# Retention policy status

**Status:** a complete organization-approved retention schedule does not exist. This document records verified implementation behavior and the policy work required; it does not create legal retention periods.

| Record | Verified behavior | Policy decision required |
|---|---|---|
| Source-routing decisions | Stores bounded facts, output and HMAC fingerprint with a 30-day `retention_until`; purge function supports dry run, deletion, and count-only audit metadata. Tests cover expiry deletion. | Approve purpose and period; schedule least-privileged purge, measure lag, alert on failure, and assess replica/backup lifecycle. |
| Raw source-triage text | Not stored in `RouteDecision` facts/output in tested route. | Verify logs, proxies, tracing, crash reporting and backups in actual deployment. |
| Audit metadata | Hash-chain prototype is append-only at application/DB layer for covered operations. | Assign retention, legal hold, access/export, key and independent anchor policy. |
| Legacy cases, chats, documents, uploads | No complete TTL/deletion schedule verified. Several production endpoints are gated. | Keep disabled for production personal data until per-record retention and verified deletion lifecycle exist. |
| Backups and replicas | No restore or backup retention evidence for current deployment. | Define encrypted backup schedule, expiry, restore testing and deletion propagation. |

No expiry is inferred for records where the repository does not enforce one. The purge command is not a production scheduler.

