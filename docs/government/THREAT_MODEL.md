# Threat model status

The canonical threat model and abuse cases are [`../security/THREAT_MODEL.md`](../security/THREAT_MODEL.md) and [`../security/ABUSE_CASES.md`](../security/ABUSE_CASES.md). The release-critical control register is [`../merge/SECURITY_GAP_MATRIX.md`](../merge/SECURITY_GAP_MATRIX.md).

The current high-impact open risks include unauthenticated source triage abuse, incomplete identity/tenant authorization, incomplete source publication controls, absence of a secure evidence vault, incomplete retention operations, privileged-database tampering limits on the audit chain, and missing current independent scans. No production threat assessment has been signed by an operator or agency owner.

