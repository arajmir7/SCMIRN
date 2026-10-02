# SCMIRN SRS Traceability

This document maps implemented backend APIs to the requested SRS requirements.

## Functional Requirements

| FR | Implemented API |
|---|---|
| FR-01 Citizen Issue Reporting | `POST /api/v1/scmirn/issues/report` |
| FR-02 Multi-Source Issue Detection | `POST /api/v1/scmirn/issues/detect` |
| FR-03 Duplicate and Fraud Detection | Embedded in `POST /api/v1/scmirn/issues/report` response |
| FR-04 Issue Classification and Prioritization | Embedded in `POST /api/v1/scmirn/issues/report` response |
| FR-05 Emergency Issue Escalation | Embedded in `POST /api/v1/scmirn/issues/report` response |
| FR-06 Complaint Lifecycle Tracking | `POST /api/v1/scmirn/issues/{id}/transition`, `GET /api/v1/scmirn/issues/{id}/lifecycle` |
| FR-07 Citizen Notification and Feedback | `POST /api/v1/scmirn/issues/{id}/feedback` |
| FR-08 Digital Work Order Generation | `POST /api/v1/scmirn/work-orders/generate` |
| FR-09 Contractor Assignment and SLA Tracking | `POST /api/v1/scmirn/work-orders/{id}/assign` |
| FR-10 Repair Quality Verification | `POST /api/v1/scmirn/work-orders/{id}/verify` |
| FR-11 Contractor Performance Scoring | `GET /api/v1/scmirn/contractors/{id}/performance` |
| FR-12 Infrastructure Health Monitoring | `POST /api/v1/scmirn/assets/health` |
| FR-13 Predictive Maintenance Scheduling | `GET /api/v1/scmirn/assets/maintenance-schedule` |
| FR-14 Flood Risk Prediction | `POST /api/v1/scmirn/risk/flood-predict` |
| FR-15 Traffic Impact Management | `POST /api/v1/scmirn/traffic/impact-simulate` |
| FR-16 Underground Utility Protection | `POST /api/v1/scmirn/utilities/register`, `POST /api/v1/scmirn/utilities/pre-dig-verify` |
| FR-17 Accessibility Issue Management | `POST /api/v1/scmirn/issues/{id}/accessibility` |
| FR-18 Digital Twin Visualization | `GET /api/v1/scmirn/digital-twin/overview` |
| FR-19 Public Transparency Dashboards | `GET /api/v1/scmirn/dashboards/public` |
| FR-20 Governance and Audit Logging | `GET /api/v1/scmirn/governance/audit-logs` |
| FR-21 Budget and Cost Monitoring | `POST /api/v1/scmirn/finance/budget-event`, `GET /api/v1/scmirn/finance/budget-summary` |
| FR-22 Multilingual Support | Language-aware notification messages in issue intake service |
| FR-23 Offline and Low-Connectivity Operation | `POST /api/v1/scmirn/sync/offline-issues` |
| FR-24 Manual Override and Exception Handling | `POST /api/v1/scmirn/governance/manual-override` |

## Non-Functional Coverage Highlights

| NFR | Implemented Control |
|---|---|
| NFR-05 Security | Role-gated manual override endpoint and existing rate limiting |
| NFR-06 Privacy | Public responses avoid exposing sensitive reporter details |
| NFR-08 Explainability | Priority explainability payload included in intake response |
| NFR-09 Maintainability | Dedicated modular service `scmirn_srs_service.py` |
| NFR-12 Auditability | Immutable hash-chained audit records (`srs_audit_logs`) |
| NFR-13 Resilience | Offline queue synchronization path |
| NFR-15 Localization | Language-specific citizen status messaging |
