# ADR-0005: Identity and authorization

**Status:** Production decision deferred; privileged service disabled  
**Date:** 2026-10-01

## CONTEXT

The codebase contains user/JWT modules, but production login, MFA, RBAC/ABAC, tenant scope, session revocation and protected officer/admin routes are not verified.

## OPTIONS

1. Treat existing JWT code as production authentication.
2. Select an agency identity provider and implement tested role/tenant mapping.
3. Keep privileged workflows disabled until an accountable identity owner exists.

## DECISION

Keep production APIs limited to health/readiness and public source-gated functions. Do not expose privileged officer/admin operations. Do not claim that the presence of JWT code constitutes verified authentication or authorization.

## WHY

There is no agency, tenant model or identity provider contract in this environment.

## SECURITY IMPACT

Production authentication, authorization, four-eyes approval and tenant checks are critical open risks.

## OPERABILITY IMPACT

No identity federation, key rotation, account recovery or support process is configured.

## MIGRATION IMPACT

Provider choice must precede user identifier, role, assurance and session lifecycle decisions.

## REVERSIBILITY

Provider adapters are reversible; persisted identity mappings require migration planning.

## STATUS

Privileged functions remain disabled; provider decision is deferred pending accountable external requirements.
