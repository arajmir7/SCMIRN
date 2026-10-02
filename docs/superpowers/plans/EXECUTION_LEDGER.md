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
- Implementation: centralized deny-by-default staff attribute policy integrated with staff case list/read/create/status paths; current staff officers are creator/assignment scoped, administrator/auditor reads remain tenant scoped, and auditor remains read-only.
- Tests: focused policy and staff API tests passed (12 passed); full backend suite with disposable PostgreSQL 16/restricted role integration passed (73 passed, two existing deprecation warnings).
- Commits: none in this execution.

## Increment log

| Increment | Change | Verification | Commit |
| --- | --- | --- | --- |
| Plan | Approved architecture and execution sequence | Repository baseline checked | pending |
| Phase 4 ABAC | Default-deny policy and scoped case access; policy and tests documented | Full backend + disposable PostgreSQL 16: 73 passed, 2 warnings | pending |

## Open gates

- Complete RBAC role model and policy review.
- Citizen ownership/jurisdiction schema and forced RLS for quarantined tables.
- MFA recovery/federated identity.
- Private evidence vault, retention worker, privacy request workflows.
- Source/service domain migration and maker-checker UI.
- Connector contracts and externally authorized sandboxes.
- Citizen/officer/admin/Labs frontend transformation, i18n, PWA and accessibility evidence.
- SAST/SCA/Gitleaks/container/IaC/DAST, SBOM/provenance, backup/restore/rollback/load/DR.
- Government, legal/privacy and independent certification approvals.
