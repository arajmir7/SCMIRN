# ADR-0004: Background work and messaging

**Status:** Deferred; no queue or workflow engine is deployed  
**Date:** 2026-10-01

## CONTEXT

The source archive contained disconnected workers and workflow code. The canonical production Compose stack has a one-shot migration job but no queue, broker, scheduled purge worker, or external consequential connector.

## OPTIONS

1. Add a broker/workflow engine now.
2. Keep bounded synchronous/local operations until a real asynchronous use case and delivery guarantees are approved.
3. Reuse disconnected source worker code without production tests.

## DECISION

Do not add a queue or workflow engine without an active production workload. Retention purge remains a CLI operation. If a future external action is introduced, design idempotency and reconciliation first, then select transactional outbox/inbox semantics.

## WHY

No current broker-backed behavior exists to justify another operational dependency.

## SECURITY IMPACT

No external filing is allowed, so there is no hidden retry path. A future connector must represent unknown remote state and reconcile before retry.

## OPERABILITY IMPACT

There is no queue backlog or worker alert to operate today. The purge is not automatically enforced.

## MIGRATION IMPACT

Adding durable jobs later requires schema, retry, deduplication, poison-message and operator migration plans.

## REVERSIBILITY

High because no broker is chosen or deployed.

## STATUS

Deferred. Queue/workflow/transactional outbox implementation is not present and is not a production capability.
