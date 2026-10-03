# SCMIRN Transformation Execution Ledger

## Baseline

- Branch: `main`
- Baseline commit: `e3223ff4bace21bb16dba5feb912f3e3d6d6ed14`
- Initial working tree: clean
- User designated baseline: preserved Phase 3 release evidence

## Current status

- Requirements/design: recorded in `docs/superpowers/specs/2026-10-02-citizen-resolution-platform-design.md`.
- Execution plan: `docs/superpowers/plans/2026-10-02-government-transformation.md`.
- Phase 3 controls: preserved; no production/API flags changed.
- Implementation: centralized deny-by-default staff attribute policy integrated with staff case list/read/create/status paths; current staff officers are creator/assignment scoped, administrator/auditor reads remain tenant scoped, and auditor remains read-only. The current frontend increment adds a prototype-disclosed Labs index and an initial staff workspace for the metadata-only API.
- Tests: focused policy and staff API tests passed (12 passed); full backend suite with disposable PostgreSQL 16/restricted role integration passed (81 passed, two existing deprecation warnings), including the field registry gate.
- ABAC increment commit: `748d52a79e9d706b556957f8076e0fb807518451`, pushed to `origin/main`.
- Data governance increment: `97546e7cab8083a6276e76d8661cf5ae3792c9b4`, pushed to `origin/main`; strict approval reports 289 issues, including 254 personal/linkable fields without accountable approvals.
- Frontend increment: `192bc4b` (`Add Labs and staff workspace UI`), pushed to `origin/main`; typecheck/build passed, 13 Playwright tests passed, and strict UI audit reported zero findings. Staff browser tests use mocked API responses and do not verify deployment.

## Increment log

| Increment | Change | Verification | Commit |
| --- | --- | --- | --- |
| Plan | Approved architecture and execution sequence | Preserved in the committed transformation history | Included in prior commits |
| Phase 4 ABAC | Default-deny policy and scoped case access; policy and tests documented | At commit time, full backend + disposable PostgreSQL 16: 73 passed, 2 warnings | `748d52a79e9d706b556957f8076e0fb807518451` pushed |
| Phase 4 data governance | Inventory all ORM columns and add CI/release validation | Registry parity passed (34 tables, 452 columns); strict approval reports 289 issues incl. 254 unapproved personal fields; full backend 81 passed | `97546e7cab8083a6276e76d8661cf5ae3792c9b4` pushed |
| Frontend Labs and staff workspace | Route prototype workspaces through `/labs/*`; add metadata-only `/staff` UI and resilient auth/API states; preserve capability disclosures | Typecheck/build passed; 13 Playwright tests passed; strict premium audit 0 findings; API responses mocked in browser tests | `192bc4b` pushed |

## Open gates

- Complete RBAC role model and policy review.
- Citizen ownership/jurisdiction schema and forced RLS for quarantined tables.
- Accountable privacy/legal review of 254 personal/linkable field records and explicit processor, region, retention and citizen rights controls.
- MFA recovery/federated identity.
- Authority-approved production evidence configuration, scheduled retention worker, and privacy request workflows.
- Source/service domain migration and maker-checker UI.
- Connector contracts and externally authorized sandboxes.
- Complete citizen/officer/admin workflows; initial `/staff` and `/labs` surfaces exist, while authenticated source publishing, assignment/review queues, i18n, PWA, and independent accessibility evidence remain open.
- SAST/SCA/Gitleaks/container/IaC/DAST, SBOM/provenance, backup/restore/rollback/load/DR.
- Government, legal/privacy and independent certification approvals.

## 2026-10-03 continuation from `91d1290f21558ebe7678809db04d1c03114ab199`

- Added Alembic head `20261003_01` for tenant/case-bound evidence metadata,
  forced RLS, composite tenant/case and tenant/creator references, and
  non-empty retention-policy constraints. The app role has evidence workflow
  grants; worker and auditor roles do not.
- Added private local-development and KMS-encrypted S3-compatible storage,
  streaming size/type/signature validation, SHA-256 checksums, ClamAV
  INSTREAM scanning, fail-closed quarantine/promotion, MFA/ABAC staff routes,
  session/case-bound app-proxied retrieval, metadata-only audit, and
  legal-hold-aware deletion with verified status.
- Evidence remains off by default; production routes remain outside the API
  allowlist. The tenant RLS policy uses an application-set GUC, so this is
  query-scope protection for a trusted app, not an independent DB tenant
  credential.
- Registry parity passed for **35 tables / 471 columns**; 294 potential
  personal/linkable fields are registered or explicitly exempted. Strict
  approval fails with **309 issues**, including 273 personal-data approvals,
  35 unresolved table-owner/retention records, and one unresolved profile.
- Backend tests passed: **102 passed**, including disposable PostgreSQL 16
  migration upgrade/downgrade, evidence tenant/case RLS and `row_security=off`
  checks; 118 existing warnings remain.
- The repository release gate ran: backend, registry parity, frontend
  typecheck/build, 13 Playwright flows, feature parity and OpenAPI route parity
  passed. The gate exits nonzero because strict privacy approval is unresolved
  and no production config/CA file was supplied; operational, external
  security, accessibility and DR blockers remain.
- Commit and push status: pending final review and verification.
