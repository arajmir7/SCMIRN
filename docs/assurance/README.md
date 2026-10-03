# SCMIRN assurance data room

**Assessment date:** 2026-10-03. **Current verdict:** `NOT PRODUCTION READY`.

This index is a review workspace for an authority, hosting operator, privacy
team, accessibility reviewer, or independent assessor. Repository evidence is
bounded to the exact command, commit, environment, and date recorded with it.
Local and disposable-environment passes are not deployment approval. No
government relationship, certification, legal approval, or production
operation is claimed.

## Architecture, APIs, and security

- [Deployment architecture](../DEPLOYMENT_ARCHITECTURE.md)
- [Security architecture](../security/SECURITY_ARCHITECTURE.md)
- [Database schema and migration behavior](../government/DATABASE_SCHEMA.md)
- [PostgreSQL data boundary and RLS limits](../security/DATA_BOUNDARY_MATRIX.md)
- [Authorization matrix](../security/authorization-matrix.yaml)
- [Threat model](../security/THREAT_MODEL.md)
- [Abuse cases](../security/ABUSE_CASES.md)
- [API catalog and route contract](../government/API_CATALOGUE.md)

## Privacy, source governance, and service boundary

- [DPDP engineering readiness](../compliance/DPDP_READINESS_MATRIX.md)
- [Government data flow](../government/DATA_FLOW.md)
- [Data governance inventory](../government/data-governance-registry.yaml)
- [Official source provenance and dated handoffs](../government/SOURCE_PROVENANCE.md)
- [Integration capability catalog](../government/INTEGRATION_CATALOG.md)
- [Case and routing execution specification](../superpowers/specs/2026-10-02-citizen-resolution-platform-design.md)

The catalog exposes four internally reviewed `OFFICIAL_HANDOFF_ONLY` service
candidates. It has no connected filing, receipt, status, or appeal integration.
The cybercrime portal candidate remains withheld pending a successful valid-TLS
source review. Catalog hashes are point-in-time evidence and there is no
scheduled drift/reviewer lifecycle yet.

## Test and release evidence

- [Typed production blocker ledger](../release/production-blockers.yaml)
- [Release-gate evidence history](../release/RELEASE_EVIDENCE.json)
- [Test evidence matrix](../merge/TEST_EVIDENCE_MATRIX.md)
- [Evidence artifact policy and historical snapshots](../release/evidence/README.md)
- [Privacy field/table/profile decisions](external/README.md)
- [Locally verifiable evidence status](evidence/README.md)

The candidate gate currently reports 12 blocking engineering workstreams as
`OPEN`; the privacy, government authorization, hosting, independent assessment,
and security-operations records are separately classified as external
dependencies. The gate must stay nonzero while local engineering controls are
open. A clean candidate gate would still not authorize government production.

## Government readiness and operations

- [GIGW 3.0 / DBIM self-assessment](../compliance/GIGW_3_MATRIX.md)
- [Government pilot readiness template](../government/PILOT_READINESS.md)
- [CERT-In/security assessment readiness](../security/CERT_IN_READINESS.md)
- [Incident reporting runbook](../security/INCIDENT_REPORTING_RUNBOOK.md)
- [SLO and operating targets](../operations/SLO.md)
- [Capacity model](../operations/CAPACITY_MODEL.md)

There is no published-release all-layer security scan or signed release
provenance. The 2026-10-03 local candidate scan is partial: the frontend image
scan passed; the backend image and infrastructure have open findings, and only
two local ARM64 images were built/scanned. The report and both image SBOMs are
linked from the [evidence index](evidence/README.md). There is no route-wide
accessibility report, backup/restore or DR rehearsal, production telemetry
deployment, live SIEM, or independent assessment in this data room. Historic
lockfile scan reports remain useful
only for their dated dependency scope. Do not create a pass artifact for
unavailable tools or external actions.

## Evidence rules

1. A local engineering closure must name its exact commit, verification date,
   command, environment, result, and artifact.
2. The release checker binds completed local evidence to the current full Git
   SHA and rejects missing, stale, or unsafe evidence paths.
3. External completion requires an independently signed manifest, a trusted
   keyring mounted outside the repository, an allowlisted signer fingerprint,
   and a digest-bound approval artifact. YAML state alone is not approval.
4. Privacy and legal approvers remain accountable humans; engineering may not
   mark their work approved.
5. When tooling or infrastructure is unavailable, record `BLOCKED_TOOLING` or
   `BLOCKED_EXTERNAL_DEPENDENCY` with owner and evidence needed.
