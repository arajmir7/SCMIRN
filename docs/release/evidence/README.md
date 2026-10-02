# Release evidence index

This directory contains local evidence manifests, not a production approval. The baseline was captured 2026-10-01 before application changes in the merge task. Commands are recorded in [`../../merge/TEST_EVIDENCE_MATRIX.md`](../../merge/TEST_EVIDENCE_MATRIX.md).

| Evidence | Status | Notes |
|---|---|---|
| Frontend typecheck/build/Playwright | Current hardening run passed: typecheck, build, 8 browser tests | Local only; no production deployment smoke. |
| Backend pytest | Current hardening run: 39 passed in both Python 3.11 hash-locked container and Python 3.13 workspace | Two SQLAlchemy `Query.get()` deprecations under Python 3.11; the wider Python 3.13 environment reports 116 legacy warnings. |
| Source API/audit/retention tests | Passed: 18 tests | Isolated curated source copy. |
| Source SQLite migration/trigger test | Passed: 1 test | PostgreSQL RLS/concurrency not verified. |
| Canonical visual baseline | Captured at `/tmp/scmirn-canonical-baseline.png` | One desktop viewport, not checked into repository. |
| Feature parity | Passed: 9 source-real features integrated, 0 unexplained | Evidence completeness gate only; run `python scripts/check_feature_parity.py`. |
| Accessibility, DAST/SAST/SCA/secret scan, container scan | Not verified | Stale ZIP SARIF is not a current scan. |
| Backup/restore, DR, performance and rollback | Not tested | Requires controlled operator environment and rehearsal. |
| Routing schema migration | Passed SQLite upgrade/downgrade and one PostgreSQL TLS migration rehearsal | Seven routing tables; no full legacy-schema baseline or rollback rehearsal. |
| Production config/migrations | Synthetic production config and Compose model passed; earlier PostgreSQL/TLS rehearsal exists | Current image build did not contact services and used placeholder CA files; this does not establish live deployment, tenant isolation, backups or security approval. |

## Post-merge local evidence (2026-10-01)

The final local evidence is recorded in [`../../merge/TEST_EVIDENCE_MATRIX.md`](../../merge/TEST_EVIDENCE_MATRIX.md) and the machine-readable [`RELEASE_EVIDENCE.json`](../RELEASE_EVIDENCE.json). The current run passed frontend typecheck/build, 8 Playwright flows, 39 backend tests, source parity, OpenAPI 3.1 allowlist checks, production config validation, and both local image builds. The OpenAPI gate confirmed eight documented allowlisted paths and verified that 91 other registered API operations return 503 in synthetic production mode. This remains a prototype readiness record, not an approval for production or government use.

PostgreSQL migration and an audit UPDATE trigger have local pass evidence only; the current source was not deployed to those disposable services. RLS/tenant isolation, accessibility/axe, fresh DAST/SAST/SCA/secret and container scans, SBOM, signed provenance, backup/restore, disaster recovery, performance and rollback remain `NOT TESTED` or `NOT VERIFIED`. The official service registry has no verified source configured; source-gated routing therefore abstains.

Never replace `NOT TESTED`/`NOT VERIFIED` with a pass based on design intent. Add command, date, exit status, count and environment for each new gate.
