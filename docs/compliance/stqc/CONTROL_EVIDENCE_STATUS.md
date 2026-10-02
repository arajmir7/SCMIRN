# Operational control evidence status

| Control package | Local evidence | External/production evidence required | State |
|---|---|---|---|
| Backup/restore | None for canonical production data | Encrypted backup policy, restore drill, integrity and RPO/RTO | `NOT TESTED` |
| Disaster recovery | Target topology only | Secondary site/region, failover and recovery exercise | `NOT TESTED` |
| Incident response | Draft `docs/security/INCIDENT_RESPONSE_PLAN.md` and reporting runbook | Named organization roles, contact tree, tabletop, statutory review | `DRAFT` |
| Change management | Baseline command/test evidence | Approved change control, reviewers, separation of duties, rollback | `NOT VERIFIED` |
| Vulnerability management | Stale ZIP SARIF artifacts; no fresh release scan | Current SAST/SCA/secrets/DAST/container scans and findings closure | `NOT VERIFIED` |
| Dependency management | Hashed Python production/development lockfiles and npm lockfile are present | SBOM, provenance, signature, license and CVE review | `PARTIAL` |
| Release process | Local build and tests | Signed artifact, production deployment, smoke, rollback approval | `NOT VERIFIED` |
| Monitoring | No production telemetry | SLO dashboards, alert routes, retention, SIEM integration | `NOT TESTED` |
| Data retention | Source 30-day decision TTL function/tests | Scheduled job, lag alarm, deletion evidence across replicas/backups | `PARTIAL` |
| Privacy process | DPDP data inventory draft | Legal notice, rights/grievance workflow, processor contracts and DPIA as applicable | `DRAFT` |
| Accessibility evidence | Baseline UI and tests | Full route axe + manual keyboard/SR/zoom and accessible PDF audit | `NOT TESTED` |
| Website quality/GIGW | Internal matrix and draft quality manual | Owner approval and relevant external assessment | `DRAFT` |

External assessment remains **PENDING EXTERNAL AUDIT**. This status table is a gap register, not a certificate or control attestation.
