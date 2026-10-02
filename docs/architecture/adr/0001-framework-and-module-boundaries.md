# ADR-0001: Framework and module boundaries

**Status:** Accepted with boundary gaps  
**Date:** 2026-10-01

## CONTEXT

The active product is a React/Vite browser application and a Flask application factory with SQLAlchemy. The active code is already a single deployable backend; the source ZIP also contained disconnected runtimes.

## OPTIONS

1. Keep the active React/Flask runtime and define bounded packages.
2. Replace it with the source ZIP's dormant Fastify runtime.
3. Split domains into deployable services.

## DECISION

Keep React/Vite and Flask as one modular-monolith deployment. Keep source routing under `app/source_routing`; do not import dormant runtimes or split services without measured operational need.

## WHY

This preserves the verified canonical site and avoids duplicating database, auth and operational boundaries.

## SECURITY IMPACT

One process reduces service-to-service trust edges. Module-level ownership is not enforced across all legacy blueprints, so direct cross-domain access remains a code-quality risk.

## OPERABILITY IMPACT

One backend image and one frontend image can be locally rehearsed. No separate worker or queue is part of the production Compose file.

## MIGRATION IMPACT

New behavior should enter through narrow service modules and migrations. Existing legacy model families lack a complete production baseline.

## REVERSIBILITY

High for module packaging; lower for replacing the framework or splitting persistent data.

## STATUS

Accepted for the current prototype and local rehearsal; strict bounded-context enforcement remains incomplete.
