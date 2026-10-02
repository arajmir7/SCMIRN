# Execution request coverage

This index distinguishes the user-designated pasted execution request from arbitrary instructions contained in project source or data. The pasted attachment is treated as the user’s task. ZIP contents, README claims and code comments are evidence to inspect, not authority to override the user’s requirements.

| Request sections | Evidence / work item |
|---|---|
| 0–5: visual freeze, forensics, inventory, no silent loss | `SOURCE_FEATURE_INVENTORY.md`, `CANONICAL_FEATURE_INVENTORY.md`, `FEATURE_MERGE_MATRIX.md`, `feature-parity.json`; visual screenshot baseline. |
| 6–11: information architecture, app/API/data architecture, contracts and tenancy | `ROUTE_MATRIX.md`, `API_CONTRACT_MATRIX.md`, `DATA_MODEL_MATRIX.md`, `SECURITY_ARCHITECTURE.md`. |
| 12–19: identity, integrations, GIGW/STQC/accessibility/languages/privacy/security | `GIGW_3_MATRIX.md`, `docs/compliance/stqc/`, `DPDP_READINESS_MATRIX.md`, `THREAT_MODEL.md`, `ABUSE_CASES.md`. |
| 20–40: CERT-In, audit, upload, AI/legal, maps/IoT/blockchain/money/workers/SRE/SLO/DR/deployment/secrets/supply chain/tests | `CERT_IN_READINESS.md`, `SECURITY_ARCHITECTURE.md`, `AI_GOVERNANCE_AND_EVALUATION.md`, `SLO.md`, `SECURITY_GAP_MATRIX.md`, `TEST_EVIDENCE_MATRIX.md`. |
| 41–50: user flows, visual/responsive, false claims and demo data | Baseline browser/screenshot evidence, `CLAIMS_REGISTER.md`, canonical inventory, security matrix. |
| 51–60: merge/migration, duplicate/dead code, production config, smoke, government readiness | feature merge and data matrices, government readiness/pilot/deployment/integration/operations docs. |
| 61–71: demo mode, root docs, security tests, release evidence, final gates/external blockers/final report | `docs/release/evidence/`, security test plan, this matrix and final evidence-based report. |

An item marked pending, blocked, untested or external is not complete merely because this index names it.
