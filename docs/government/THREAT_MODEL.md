# Threat model status

The canonical threat model and abuse cases are [`../security/THREAT_MODEL.md`](../security/THREAT_MODEL.md) and [`../security/ABUSE_CASES.md`](../security/ABUSE_CASES.md). The release-critical control register is [`../merge/SECURITY_GAP_MATRIX.md`](../merge/SECURITY_GAP_MATRIX.md).

The current high-impact open risks include abuse of the unauthenticated development/test source-triage endpoint (production returns 503), incomplete identity/tenant authorization, incomplete source publication controls, missing evidence-vault deployment and retention operations, privileged-database tampering limits on the audit chain, and missing exact-release independent scans. No production threat assessment has been signed by an operator or agency owner.
