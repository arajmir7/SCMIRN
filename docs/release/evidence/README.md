# Release evidence index

This directory contains local evidence manifests, not a production approval. The baseline was captured 2026-10-01 before application changes in the merge task. Commands are recorded in [`../../merge/TEST_EVIDENCE_MATRIX.md`](../../merge/TEST_EVIDENCE_MATRIX.md).

| Evidence | Status | Notes |
|---|---|---|
| Frontend typecheck/build/Playwright | 2026-10-01 hardening snapshot passed: typecheck, build, 8 browser tests | Local only; no production deployment smoke. Current frontend evidence appears in the dated follow-up below and test matrix. |
| Backend pytest | 2026-10-01 hardening snapshot: 39 passed in both Python 3.11 hash-locked container and Python 3.13 workspace | Two SQLAlchemy `Query.get()` deprecations under Python 3.11; the wider Python 3.13 environment reports 116 legacy warnings. Later backend evidence appears in the execution state and test matrix. |
| Source API/audit/retention tests | Passed: 18 tests | Isolated curated source copy. |
| Source SQLite migration/trigger test | Passed: 1 test | PostgreSQL RLS/concurrency not verified. |
| Canonical visual baseline | Captured at `/tmp/scmirn-canonical-baseline.png` | One desktop viewport, not checked into repository. |
| Feature parity | Passed: 9 source-real features integrated, 0 unexplained | Evidence completeness gate only; run `python scripts/check_feature_parity.py`. |
| Accessibility, source-code DAST/SAST/secret scan, container scan | Not verified | The strict frontend UI audit and dependency-lock SCA do not replace these checks. Stale ZIP SARIF is not current evidence. |
| Dependency-lock SCA and dependency SBOMs | Fresh 2026-10-02 lockfile scans found no known Python/frontend dependency issues; CycloneDX dependency SBOMs exist | Does not cover source code, images/OS packages, image SBOMs, or signed provenance. |
| Backup/restore, DR, performance and rollback | Not tested | Requires controlled operator environment and rehearsal. |
| Routing schema migration | Passed SQLite upgrade/downgrade and one PostgreSQL TLS migration rehearsal | Seven routing tables; no full legacy-schema baseline or rollback rehearsal. |
| Production config/migrations | Synthetic production config and Compose model passed; earlier PostgreSQL/TLS rehearsal exists | Current image build did not contact services and used placeholder CA files; this does not establish live deployment, tenant isolation, backups or security approval. |

## Post-merge local evidence (2026-10-01)

The 2026-10-01 snapshot is recorded in [`../../merge/TEST_EVIDENCE_MATRIX.md`](../../merge/TEST_EVIDENCE_MATRIX.md) and the machine-readable [`RELEASE_EVIDENCE.json`](../RELEASE_EVIDENCE.json). That run passed frontend typecheck/build, 8 Playwright flows, 39 backend tests, source parity, OpenAPI 3.1 allowlist checks, production config validation, and both local image builds. The OpenAPI gate confirmed eight documented allowlisted paths and verified that 91 other registered API operations return 503 in synthetic production mode. This remains a prototype readiness record, not an approval for production or government use.

PostgreSQL migration and an audit UPDATE trigger have local pass evidence only; the current source was not deployed to those disposable services. RLS/tenant isolation, accessibility/axe, fresh DAST/SAST/SCA/secret and container scans, image SBOM, signed provenance, backup/restore, disaster recovery, performance and rollback remain `NOT TESTED` or `NOT VERIFIED`. Four internally reviewed service records support official handoffs; no connector or official status integration exists. See the [current assurance data room](../../assurance/README.md) and [production blocker ledger](../production-blockers.yaml).

Never replace `NOT TESTED`/`NOT VERIFIED` with a pass based on design intent. Add command, date, exit status, count and environment for each new gate.

## Current frontend follow-up — 2026-10-02

The preceding sections preserve historical release snapshots. The current UI increment introduces `/labs` prototype routing and an initial `/staff` workspace. Its current typecheck, build, Playwright and strict UI audit results are recorded in the [test evidence matrix](../../merge/TEST_EVIDENCE_MATRIX.md#frontend-labs-and-staff-workspace-2026-10-02) and [`premium-audit.json`](../../../src/frontend/premium-audit.json). Mocked browser responses do not prove a live production connection. The conservative release verdict remains `NOT PRODUCTION READY`.
