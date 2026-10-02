# Security architecture status

The canonical technical assessment is [`../security/SECURITY_ARCHITECTURE.md`](../security/SECURITY_ARCHITECTURE.md); control gaps are listed in [`../merge/SECURITY_GAP_MATRIX.md`](../merge/SECURITY_GAP_MATRIX.md).

Current implementation includes production TLS/CA configuration validation, safe exception responses, request IDs, rate-limit/cache configuration, a source-gated API allowlist, selected hash-chain audit controls, a 25-table migration baseline, five public handoff candidates, and dependency-lock SCA/SBOM evidence. These are local code/configuration controls. There is no verified production identity boundary, tenant RLS, private scanned object store, SIEM, key-management service, deployed WAF, external audit, SAST/DAST/secret/image scan, image SBOM, or signed provenance.

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
452 columns; all 254 personal/linkable entries remain `INVENTORIED`, not
`APPROVED`. Privacy/legal sign-off and deployed processor, region, retention
and rights workflows are still release blockers. See
[`../release/PHASE4_DATA_GOVERNANCE_EVIDENCE.md`](../release/PHASE4_DATA_GOVERNANCE_EVIDENCE.md).
