# CERT-In and security assessment readiness

**Status:** internal preparation only; no CERT-In audit or certification has occurred.

## Evidence present

- Security architecture, threat model, abuse cases, incident response drafts, production TLS configuration checks, hash-pinned dependency locks, API fail-closed gate, request IDs, and privacy-safe exception behavior.
- Local unit and browser tests; prior local image build evidence is recorded in `docs/release/RELEASE_EVIDENCE.json`.

## Open before external assessment

- Fresh SAST, SCA, secret, DAST, container and IaC scans against the exact release commit and images; triage and closure evidence.
- Current SBOM, signed build provenance, artifact signature and vulnerability disposition.
- Authentication/MFA, RBAC/ABAC, tenant/RLS, CSRF/session, egress/SSRF and upload-vault controls for any enabled routes.
- Production topology, monitoring/SIEM, backups, restore/DR, incident contacts and rollback rehearsal.
- Exact scope, hosting/operator responsibility, data residency, applicable regulatory requirements, and assessor engagement.

The historic archive scan artifacts are stale and not release evidence. No security status here constitutes a finding-free result.

