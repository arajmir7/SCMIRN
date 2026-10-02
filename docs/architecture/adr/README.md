# Architecture decision records

These records describe implemented choices and explicitly deferred choices; a target-state diagram is not evidence of implementation.

| Concern | Record | Status |
|---|---|---|
| Backend/frontend framework and modular monolith | [ADR-0001](0001-framework-and-module-boundaries.md) | Accepted with boundary gaps |
| Production deployment topology | [ADR-0002](0002-production-deployment-boundary.md) | Accepted for local rehearsal |
| Database and tenant isolation | [ADR-0003](0003-database-and-tenant-isolation.md) | Partial; RLS/tenant choice deferred |
| Worker, workflow and event architecture | [ADR-0004](0004-background-work-and-messaging.md) | Deferred |
| Authentication and authorization | [ADR-0005](0005-identity-and-authorization.md) | Production decision deferred |
| AI, search and retrieval | [ADR-0006](0006-ai-and-knowledge-boundary.md) | Production runtime deferred |
| Official sources and government connectors | [ADR-0007](0007-source-provenance-and-connectors.md) | Accepted fail-closed boundary |
| Documents, uploads and object storage | [ADR-0008](0008-document-and-object-storage.md) | Production storage deferred |
| Observability and operations | [ADR-0009](0009-observability.md) | Minimal local probes accepted; production stack deferred |

## Required future decision coverage

Four-eyes approval, feature flags, kill switches, idempotent connector submission, outbox/inbox, AI evaluation, SLO targets, production WAF/proxy, object storage and tenant-specific RLS need approved owners and environment constraints before an implementation choice is made. Until then, the associated capabilities remain disabled or explicitly local/demo-only.
