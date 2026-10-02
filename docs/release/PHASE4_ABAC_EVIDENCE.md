# Phase 4 ABAC increment evidence

**Scope:** staff case attribute policy and authorization regression coverage.  
**Candidate:** implementation from the 2026-10-02 SCMIRN transformation session.  
**Release verdict:** `NOT PRODUCTION READY`.

## Change

- Added pure default-deny policy evaluation for MFA-authenticated staff actions, exact tenant ownership, server-defined purpose, sensitivity, case creator/owner/assignment, and independent source reviewer scope.
- Staff case list/read/create/status endpoints now call the policy evaluator. Officer list results are SQL-scoped to creator or assignee; cross-tenant and unauthorized case IDs return the same 404 response. Auditors remain read-only.
- The existing public/staff production API allowlist, `STAFF_API_ENABLED=false`, runtime database roles, forced RLS, and migration head were not changed.
- Added the policy's explicit role and schema limits in `docs/security/STAFF_AUTHORIZATION_POLICY.md`.

## Verification

- Red phase: the new focused policy tests failed collection because `app.staff_auth.authorization` did not exist.
- Focused suite after implementation: `12 passed`.
- Full backend suite against a disposable PostgreSQL 16 owner database, with the integration test provisioning and using the restricted application, worker, migrator, and auditor roles: `73 passed`, two existing `Query.get()` deprecation warnings.
- Disposable database container stopped after the run. No production database or external service was used.
- `git diff --check`: passed.

## Limits

- This does not complete the seven-role identity model; citizen, assisted-service operator and supervisor grants are not provisioned.
- Current staff case records do not carry jurisdiction or department keys. The implemented case ABAC scope is tenant plus creator/assignment; jurisdiction-sensitive case actions remain blocked until a reviewed schema migration supplies those attributes.
- Source approval is a policy contract only; no source governance endpoint or maker-checker workbench is enabled.
- PostgreSQL RLS remains an independent required boundary and was exercised separately from the pure policy tests.
- The code and tests do not authorize staff APIs for production, identity-provider use, legal processing, or government service operation.
