# Government pilot readiness

**Verdict:** not ready to pilot with production citizen data. Internal engineering work can continue in an isolated synthetic-data environment.

## What SCMIRN can do at baseline

- Render the current citizen-facing React experience and route through the canonical Flask APIs.
- Store and display SCMIRN issue/document/chat records and run local analytics/simulations.
- Run selected deterministic/enterprise/IoT/twin code paths against development data; their operational inputs are not verified government feeds.
- SCMIRN source code implements consented source-gated routing; four public official handoffs are verified at source/hash/host level. Cybercrime remains hidden because its portal did not pass TLS validation. No filing or official receipt is produced.

## Readiness boundaries

| Capability | State |
|---|---|
| Tested locally | Backend suite: 65 passed with the PostgreSQL RLS integration enabled; six SQLite migration tests cover zero-to-head and existing-schema paths, and the full migration/RLS flow also passed on disposable PostgreSQL 16. Python/frontend dependency scans and SBOMs are recorded. Earlier frontend typecheck/build/8 browser tests and the limited PostgreSQL Compose rehearsal are documented separately. |
| Simulated | Canonical sample issues, funding counters, IoT, blockchain, resilience, digital twin, enterprise metrics and multiple civic AI/legal outputs. |
| Needs government data | Office/service records, jurisdiction boundaries, live agency status, city asset/sensor feeds and verified legal sources. |
| Needs official credentials | Government grievance, SSO, DigiLocker/eSign, notification, payment or case status connectors. |
| Needs legal approval | Data sharing, legal content, retention, privacy notice/rights, payment and agency submissions. |
| Needs external security assessment | CERT-In empanelled penetration/security audit, STQC evaluation and any agency security review. |

Before a pilot: signed scope and data agreement; named agency/system owner; isolated sandbox; synthetic data; staff MFA and role/tenant access tests in the approved deployment; production PostgreSQL role/RLS validation; source review; privacy impact/legal approval; SAST/DAST/secret/container scan and penetration test; accessibility audit; DR/restore; incident contacts; rollback rehearsal and citizen grievance owner. The current code does not accept production citizen cases or evidence.
