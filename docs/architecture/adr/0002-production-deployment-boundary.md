# ADR-0002: Production deployment boundary

**Status:** Accepted for local rehearsal; live topology not selected  
**Date:** 2026-10-01

## CONTEXT

The development Compose stack uses SQLite and demo settings. A separate production Compose file now requires PostgreSQL, verified TLS Redis, immutable image release IDs and an HTTPS origin.

## OPTIONS

1. Reuse development Compose.
2. Keep an isolated production Compose topology with external data services and external HTTPS termination.
3. Select a cloud/Kubernetes provider before an operator and environment are known.

## DECISION

Use the separate Compose file for reproducible local integration rehearsal only. Pin Python, Node and Nginx base images by digest and install Python dependencies from a versioned hash-checked lock. Keep public HTTPS termination, DNS, WAF, secrets, data services and monitoring outside this stack. No live hosting provider or Kubernetes production target is selected.

## WHY

This avoids claiming that local containers provision a complete government deployment and keeps secrets/data services externally managed.

## SECURITY IMPACT

Backend host port is not published; frontend binds to loopback. PostgreSQL and Redis require CA validation; Redis requires hostname verification. Base images are digest-pinned but have no fresh CVE scan. Host, proxy and external service controls remain unverified.

## OPERABILITY IMPACT

`scripts/deploy.sh` validates, builds, migrates, waits for health, and smoke-checks local HTTP routes. It is not a remote deployment orchestrator.

## MIGRATION IMPACT

External deployment must preserve exact release ID, image digest, configuration schema and migration head.

## REVERSIBILITY

High before adoption by a hosting platform; topology changes need a separately rehearsed migration plan.

## STATUS

Local production rehearsal path accepted. Live production topology is deferred to an accountable operator.
