# ADR-0009: Observability

**Status:** Minimal probes accepted; production monitoring deferred  
**Date:** 2026-10-01

## CONTEXT

The backend exposes liveness and dependency readiness checks and emits application logs. No trace collector, metrics backend, SLO dashboard, paging route or production log-retention policy is configured.

## OPTIONS

1. Treat container health checks as production observability.
2. Select metrics/logging/tracing providers after a production operator and data residency requirements are known.
3. Expose no health endpoint.

## DECISION

Keep `/api/health` dependency-independent and `/api/ready` dependent on PostgreSQL and Redis. Do not claim SLO, production availability or alert coverage. Logs use generated request IDs and safe generic exception messages; full telemetry remains a deployment prerequisite.

## WHY

Health probes support the local Compose rehearsal without implying an operated monitoring service.

## SECURITY IMPACT

Requests receive server-generated IDs. Exception messages are suppressed in the app error logger to reduce citizen-data leakage. Legacy route logs remain a privacy-review item, and centralized controls are absent.

## OPERABILITY IMPACT

No 24/7 owner, alert route or runbook response SLA has been named.

## MIGRATION IMPACT

Telemetry provider choice must include data residency, retention, access control, redaction and operator integration.

## REVERSIBILITY

High while only local logs and probes are used.

## STATUS

Local probes accepted; production observability architecture is deferred.
