# ADR-0003: Database and tenant isolation

**Status:** PostgreSQL selection accepted; tenant model and RLS deferred  
**Date:** 2026-10-01

## CONTEXT

The production configuration requires PostgreSQL with `sslmode=verify-full`. The local rehearsal applied the new routing/audit migration, but it is not a baseline for all legacy tables and there is no verified tenant boundary or RLS policy.

## OPTIONS

1. SQLite for production.
2. PostgreSQL with a reviewed single-tenant model and least-privilege roles.
3. PostgreSQL with tenant-scoped tables, RLS and cross-tenant tests.

## DECISION

Use PostgreSQL for the production-oriented runtime path. Do not enable government or multi-tenant data until tenant ownership, RLS policies, role grants and cross-tenant tests are designed and reviewed. No tenant isolation guarantee is made now.

## WHY

The deployed schema needs PostgreSQL-specific trigger validation, and SQLite cannot prove those controls. An unreviewed tenant model would be unsafe.

## SECURITY IMPACT

No production auth/tenant scope is verified. Runtime database role separation and RLS are release blockers.

## OPERABILITY IMPACT

Database operations, backups, restore, connection pool sizing, monitoring and failover belong to the future database operator.

## MIGRATION IMPACT

`20261001_01` creates seven routing/audit tables only. Legacy schema baseline, empty/current/previous schema testing and compatible rollback remain incomplete.

## REVERSIBILITY

PostgreSQL choice is reversible with data export; table ownership and tenant key choices become expensive once data is stored.

## STATUS

PostgreSQL accepted for the local production rehearsal. Tenant design and production role grants are deferred and release-blocking.
