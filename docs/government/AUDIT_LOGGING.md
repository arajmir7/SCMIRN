# Audit logging status

The source-routing audit prototype stores metadata and uses a cryptographic chain with database protections for covered writes. Tests detect altered content and reject sensitive free-text details. This is tamper-evident application evidence, not immutable storage: a privileged database owner can still affect records, a global append sequence under concurrency is not fully proven, DELETE denial is not fully verified, and no independent WORM/anchor is configured.

No production security event pipeline, SIEM integration, alert owner, or organization-approved log retention/residency policy is present. Never log passwords, tokens, OTPs, secrets, or raw high-risk document contents. See [`../security/SECURITY_ARCHITECTURE.md`](../security/SECURITY_ARCHITECTURE.md) and [`RETENTION_POLICY.md`](RETENTION_POLICY.md).

