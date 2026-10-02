# SCMIRN Security Architecture Proposal and Gap Summary

> **Status (2026-10-01): internal design material only.** The controls below are target requirements unless the current implementation boundary explicitly says they are present. No external security audit, SOC 2/ISO certification, government approval, or finding-free scan is established.

## Controls present in the local prototype

- Consent-gated source triage, deterministic abstention and no agency submission.
- Route decisions store a keyed fingerprint and bounded derived facts; raw descriptions are not persisted by the route service.
- Idempotency, a 30-day purge command, rate limits and metadata-only hash-chained audit records.
- Production requires configured secrets, PostgreSQL, TLS Redis and HTTPS CORS; the production API gate disables legacy, upload, document and simulation routes.

These controls have local unit or migration evidence only. PostgreSQL behavior, tenant isolation/RLS, identity, WAF, centralized monitoring, incident response execution, backups, independent testing and deployment controls are not verified. See [`../security/THREAT_MODEL.md`](../security/THREAT_MODEL.md), [`../merge/SECURITY_GAP_MATRIX.md`](../merge/SECURITY_GAP_MATRIX.md), and [`../merge/TEST_EVIDENCE_MATRIX.md`](../merge/TEST_EVIDENCE_MATRIX.md).

## Security Objectives
1. Protect citizen data and critical infrastructure operations.
2. Maintain verifiable auditability for all high-impact actions.
3. Achieve continuous compliance with enterprise and public-sector frameworks.

## Threat Model
### Assets
1. Citizen PII and case records.
2. Operational control-plane actions.
3. Infrastructure telemetry and predictions.
4. Contracts and procurement records.

### Adversaries
1. External attackers targeting civic infrastructure.
2. Insider misuse or privilege abuse.
3. Supply-chain tampering in software dependencies.
4. Disinformation or social engineering campaigns.

### Key Attack Scenarios
1. API credential theft and unauthorized data exfiltration.
2. Lateral movement between microservices.
3. Command injection into automation workflows.
4. Tampering with historical records or compliance evidence.

## Controls
1. Zero-trust network policy and least-privilege access.
2. SSO with SAML/OIDC and adaptive MFA.
3. Signed container images and runtime workload policies.
4. Encryption:
- in transit: TLS 1.3
- at rest: AES-256
- long-term: post-quantum migration roadmap
5. Immutable audit trail using Hyperledger Fabric.
6. Air-gapped backup snapshots for recovery integrity.
7. AI-assisted anomaly detection for behavioral outliers.
8. Automated kill switch for rapid containment.

## Incident Response
1. Detection and triage within minutes via central SOC telemetry.
2. Immediate containment through node isolation and policy hardening.
3. Forensic evidence capture and chain-of-custody controls.
4. Recovery with staged service restoration and validation checks.

## Compliance Mapping
1. SOC 2 Type II:
- access control
- change management
- logging and monitoring
2. ISO 27001:
- risk assessment
- asset management
- incident response
3. GDPR:
- data minimization
- subject rights support
- breach notification workflows
4. CCPA:
- data access and deletion handling
- consumer privacy disclosures

## Penetration Testing Program
1. Continuous red-team automation for web/API controls.
2. Quarterly manual penetration testing for business logic and privilege paths.
3. Annual third-party assessment for governance and assurance.

## Residual Risks
1. Legacy system connectors with constrained security models.
2. Model drift affecting automated decisions.
3. Third-party dependency vulnerabilities between patch windows.
