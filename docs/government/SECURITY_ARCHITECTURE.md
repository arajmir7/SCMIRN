# Security architecture status

The canonical technical assessment is [`../security/SECURITY_ARCHITECTURE.md`](../security/SECURITY_ARCHITECTURE.md); control gaps are listed in [`../merge/SECURITY_GAP_MATRIX.md`](../merge/SECURITY_GAP_MATRIX.md).

Current implementation includes production TLS/CA configuration validation, safe exception responses, request IDs, rate-limit/cache configuration, a source-gated API allowlist, selected hash-chain audit controls, a 25-table migration baseline, five public handoff candidates, and dependency-lock SCA/SBOM evidence. These are local code/configuration controls. There is no verified production identity boundary, tenant RLS, private scanned object store, SIEM, key-management service, deployed WAF, external audit, SAST/DAST/secret/image scan, image SBOM, or signed provenance.

**State: `PARTIAL`; overall production security is not verified.**
