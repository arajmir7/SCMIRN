# Phase 4 field-governance inventory evidence — historical baseline

**Assessment date:** 2026-10-02. **Status:** engineering inventory; privacy/legal approval incomplete.  
**Release verdict:** `NOT PRODUCTION READY`.

> This is the historical 2026-10-02 snapshot (34 tables, 452 columns, 254
> candidate fields). The current 2026-10-03 schema has 35 tables and 471
> columns, 294 potentially personal/linkable candidates (273 pending approval
> plus 21 explicit exemptions), 35 table-governance decisions, and one profile
> approval. See the [current DPDP readiness matrix](../compliance/DPDP_READINESS_MATRIX.md)
> and [typed blocker ledger](production-blockers.yaml) for present status.

## Implementation

- Added [`data-governance-registry.yaml`](../government/data-governance-registry.yaml), enumerating all **452 mapped columns across 34 tables**.
- The registry records **254 potentially personal or linkable fields**, **21 explicit candidate exemptions**, and the remaining schema fields with classification reasons. Field records include classification, purpose, processing/notice status, processor, storage, region, encryption, authorized roles, retention, deletion, export, correction and grievance metadata, directly or through a named profile.
- Current personal-field purpose descriptions are derived from code and table use. They are `INVENTORIED`, not `APPROVED`. Processing justifications and accountable data owners remain unassigned; processor, region, rights and retention controls are incomplete.
- Added `scripts/check_data_governance.py`. CI runs exact ORM-to-registry parity. A newly mapped column without a field record fails; newly refreshed records start `UNREVIEWED` and fail the default check until classified.
- Release verification uses `--require-approved`; the current registry produces **254 approval errors**, one for each personal/linkable field without an accountable approval.

## Verification

- Focused governance tests: **8 passed**.
- Full backend suite with a disposable PostgreSQL 16 instance and restricted runtime-role integration: **81 passed**, two existing SQLAlchemy `Query.get()` deprecation warnings.
- Schema parity command: passed for 34 tables and 452 columns.
- Strict release approval evaluation: **289 issues**, including 254 personal/linkable field approvals plus unresolved profile and table governance controls.
- `git diff --check`: passed.
- The disposable PostgreSQL container was stopped after the run. No production database, personal dataset or external service was used.

## Limits

This registry is not a legal processing basis, DPDP compliance statement, data fiduciary assignment, deployment-region proof, rights workflow, deletion proof or retention scheduler. A named privacy/legal owner must review purposes and approve each applicable field and table profile. The engineering release gate intentionally remains blocked until then.
