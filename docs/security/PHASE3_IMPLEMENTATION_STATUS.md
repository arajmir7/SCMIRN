# Phase 3 production-control status

**Assessment date:** 2026-10-02. **Release verdict:** `NOT PRODUCTION READY`.
This is repository and disposable-environment evidence only. No production
database, identity provider, object store, host, or government service was used.

> **Historical snapshot.** The Phase 3 baseline below describes the code and
> counts at its assessment date. The current schema and evidence-vault update
> are recorded in the 2026-10-03 continuation near the end of this document;
> use the [production blocker ledger](../release/production-blockers.yaml)
> and current release gate for present status.

## Implemented and exercised locally

- PostgreSQL deployment identities are separated into `scmirn_app`,
  `scmirn_migrator`, `scmirn_worker`, and `scmirn_auditor`. The provisioner
  refuses to silently adopt public-schema objects owned by another role. The
  application startup check rejects elevated, inherited, owner, or
  `BYPASSRLS` roles and verifies the staff table RLS contract.
- Alembic head `20261002_04` covers all 34 mapped tables. The web app uses its
  runtime URL; the one-shot migration container uses the separate migrator
  URL. Staff APIs default to `STAFF_API_ENABLED=false`.
- The complete inventory is in the [data-boundary matrix](DATA_BOUNDARY_MATRIX.md):
  5 `GLOBAL_REFERENCE`, 3 `TENANT_SCOPED`, 0 `SUBJECT_SCOPED`, 14
  `SECURITY_SCOPED`, 3 `AUDIT_SCOPED`, and 9 `LEGACY_UNCLASSIFIED` tables.
  The app and worker receive no grants on the quarantined legacy tables.
- The app can append routing audit events without reading their contents.
  PostgreSQL grants only the generated sequence value needed for insert
  `RETURNING`, plus execution of a narrow audit-head function. A distinct
  auditor connection has read-only audit access.
- Production triage and jurisdiction resolution stay disabled until decision
  storage has an enforced subject/tenant boundary. The API contract and
  synthetic production gate cover 15 allowed paths and reject 93 other
  registered operations with 503.
- The full backend suite passed: **67 passed**, with two existing SQLAlchemy
  `Query.get()` deprecation warnings. The opt-in PostgreSQL 16 integration
  provisioned all four roles and exercised migration, RLS, audit access,
  denial of app DDL/audit reads, and overprivileged-role rejection.

## Still open

- A complete seven-role RBAC and ABAC policy matrix, independent reviewer
  controls, MFA recovery/reset workflow, and deployment identity/federation.
- Ownership keys, migration/backfill and forced tenant/jurisdiction RLS for
  legacy citizen, issue, document, chat, route, infrastructure and other
  quarantined records. The current role grants are a containment boundary,
  not completed data isolation.
- A production worker contract, scheduled retention purge, authority-approved
  private evidence store/scanner configuration, and deletion-lag monitoring.
- Fresh candidate SAST/SCA/secret/container/IaC scans, image SBOMs, and signed
  provenance. Dependency-lock scans and source scans alone are not sufficient.
- Structured JSON logs and redaction review, production metrics/tracing,
  monitoring, actionable alert ownership, SLOs, load/capacity testing,
  backup/restore, DR, rollback, and accessibility evidence.
- External legal/privacy approval, authorized government integrations, and
  independent security assessment.

The release gate exits nonzero while these controls remain open. See the
[release evidence](../release/RELEASE_EVIDENCE.json) for the bounded test
record and the [Phase 2 historical control record](../government/INTERNAL_CONTROLS_CLOSED.md).

## 2026-10-03 continuation: private evidence controls

The current schema head is `20261003_01` with 35 mapped tables. This
continuation adds a private evidence lifecycle: restrictive local-development
storage, KMS-encrypted S3-compatible storage, ClamAV INSTREAM scanning,
checksummed metadata, tenant/case foreign keys and forced RLS, session-bound
retrieval tickets that reauthorize and audit downloads, and hold-aware
deletion that records unverified failures. The evidence feature defaults off
and its routes remain outside the production API allowlist.

Disposable PostgreSQL 16 now exercises evidence RLS, runtime-role grants,
cross-tenant/cross-case denial, `row_security=off` denial, migration upgrade
and downgrade, in addition to the existing staff-role contract. The full
backend suite passed: **102 passed**, with 118 existing deprecation warnings.
These are local test results, not evidence from a deployed authority environment.

The source and adapter code exists, but this candidate has no approved private
production bucket, KMS policy, live scanner, authority-owned retention
decision, scheduled retention worker, deletion-lag alert, or recovery drill.
RLS uses an application-set tenant GUC; it limits accidental unscoped access
under the trusted app but does not establish an independent database tenant
identity. The 35-table registry passes schema parity. The current governance
evaluation is classified as 273 personal/linkable field approvals, 35 table
ownership/retention records, and one governance-profile approval. These are
privacy/data-owner decisions, not a count of code defects. The machine-readable
[blocker ledger](../release/production-blockers.yaml) tracks each workstream and
its accountable owner and required evidence. Twelve blocking engineering
workstreams remain `OPEN`; external legal, government, infrastructure,
security-assessment, and security-operations work is recorded separately as
`BLOCKED_EXTERNAL_DEPENDENCY`. The verdict remains `NOT PRODUCTION READY`.

## 2026-10-03 candidate gate and boundary verification

The full candidate gate ran against this worktree with a disposable PostgreSQL
16 RLS URL. Backend: **114 passed**, including the RLS integration, with 118
existing SQLAlchemy deprecation warnings. Governance parity passed for 35
tables/471 columns and 294 candidates (273 pending approvals plus 21 explicit
exemptions). Frontend typecheck, Vite build and all 13 Playwright flows passed;
feature parity passed 9/9. OpenAPI/production-route parity passed for 15
allowlisted route patterns and confirmed 99 other operations return 503,
including production triage/jurisdiction resolution.

The overall candidate gate correctly exited 1: the blocker ledger has 12 open
blocking engineering controls, and no authorized production environment file,
secrets, or CA configuration was supplied. This is local candidate gate
evidence; the following separately recorded scan covers this exact source
commit, but neither record is deployment approval.

## 2026-10-03 candidate security scan

The separately recorded [candidate scan report](../assurance/evidence/security-release.json)
covers the candidate source tree and local ARM64 backend/frontend images. Semgrep
reported no findings across 231 tracked files; Gitleaks found no secrets in the
staged delta; npm audit and pip-audit found no vulnerable locked dependencies.
Bandit reported six low-severity findings. The frontend image reported no
vulnerabilities; the backend image still has 44 high and 60 medium vulnerability
records across 73 unique advisories, with no critical records. The infrastructure
scan reports four medium registry-trust findings for placeholder images, one
high KMS-policy finding for the S3 access-log destination, and one low finding
for that destination's server-access-log setting. The full release scan remains
open: the candidate images are local ARM64 builds, other required images are not
covered, DAST had no authorized target, and no signed release provenance exists.

## 2026-10-03 source-review and service-directory continuation

Alembic head is now `20261003_02`. Revision `20261003_02` records date-only
source review and verification fields, clears the false seed-time retrieval /
verification timestamps on `official-catalog-v1` rows, and clears exact
service verification timestamps for those rows. The internal review date is
retained only for services whose linked catalog sources are all marked
`VERIFIED`. No exact retrieval time or live currentness is inferred. Schema
governance parity now covers 35 tables and 474 columns; the 294 candidate
fields and outstanding external approvals are unchanged.

The public frontend now has a searchable `/services` directory backed by the
read-only service API. It displays scope, exclusions, source URLs and hashes,
and internal review dates, with explicit limits and failure states. Backend
route selection and the directory now accept only `OFFICIAL_HANDOFF_ONLY`;
other integration modes remain unroutable until an authorized connector
workflow exists. The directory does not submit information or create an
official acknowledgement. This closes neither source drift/reviewer lifecycle
nor privacy/legal, accessibility, or government approval gates.
