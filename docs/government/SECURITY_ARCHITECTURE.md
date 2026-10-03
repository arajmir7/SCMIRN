# Security architecture status

The canonical technical assessment is [`../security/SECURITY_ARCHITECTURE.md`](../security/SECURITY_ARCHITECTURE.md); control gaps are listed in [`../merge/SECURITY_GAP_MATRIX.md`](../merge/SECURITY_GAP_MATRIX.md).

Current implementation includes production TLS/CA configuration validation, safe exception responses, request IDs, rate-limit/cache configuration, a source-gated API allowlist, selected hash-chain audit controls, a 35-table migration baseline, four internally reviewed official handoffs plus one withheld candidate, and dependency-lock SCA/SBOM evidence. Staff and evidence forced RLS have passed disposable PostgreSQL 16 tests, and a private evidence lifecycle exists in code. These are local code/configuration controls. There is no verified production identity or complete tenant boundary, approved production object store/scanner, SIEM, key-management policy, deployed WAF, external audit, exact-release SAST/DAST/secret/image scan, image SBOM, or signed provenance.

**State: `PARTIAL`; overall production security is not verified.**

The 2026-10-02 ABAC increment adds a default-deny staff policy for the existing
case API: MFA, tenant, server purpose, sensitivity, creator/assignment and
reviewer separation are evaluated in application code, while SQL filters and
PostgreSQL RLS remain separate controls. See
[`../security/STAFF_AUTHORIZATION_POLICY.md`](../security/STAFF_AUTHORIZATION_POLICY.md)
and [`../release/PHASE4_ABAC_EVIDENCE.md`](../release/PHASE4_ABAC_EVIDENCE.md).
The role taxonomy, department/jurisdiction case keys, source-governance routes,
and staff production authorization remain incomplete; this does not change the
partial security status.

The field-level inventory is checked against ORM metadata in CI and recorded
in [`data-governance-registry.yaml`](data-governance-registry.yaml). It covers
471 columns and 294 potentially personal/linkable candidates: 273 await
accountable field approval and 21 have explicit candidate exemptions. None of
the pending entries may be changed to `APPROVED` by engineering. Privacy/legal sign-off and deployed processor, region, retention
and rights workflows are still release blockers. See
[`../release/PHASE4_DATA_GOVERNANCE_EVIDENCE.md`](../release/PHASE4_DATA_GOVERNANCE_EVIDENCE.md).

The `20261003_01` evidence revision adds forced tenant RLS and case/creator
composite references. The application-set tenant GUC provides query-scoping
defense for a trusted application; it is not a separate database tenant
credential. Evidence upload and retrieval remain disabled in production until
the authority's store, scanner and retention policy are approved and deployed.
