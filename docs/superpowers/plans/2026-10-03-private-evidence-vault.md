# Private Evidence Vault Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement this plan task-by-task. The request explicitly directs execution, so proceed inline without an approval pause.

**Goal:** Add a private, tenant/case-bound evidence lifecycle with fail-closed scanning, restricted retrieval, database isolation, audit events, and testable deletion.

**Architecture:** Keep evidence metadata in a dedicated tenant-RLS table. Store bytes only in a private local development store or configured private S3-compatible store. Stage every upload in quarantine, verify size/type/signature and checksum, then mark it clean only after the configured scanner accepts it. Expose staff routes only behind existing MFA, ABAC, feature, and production API gates.

**Tech Stack:** Flask, SQLAlchemy, Alembic, PostgreSQL RLS, boto3, Python sockets, itsdangerous, pytest.

**Spec:** User-supplied continuation brief at `/Users/ajmiraribam/.codex/attachments/839177f7-c1b2-4fb1-91d2-eca163563d07/Pasted text.txt`.

## Global Constraints

- Keep evidence routes out of the production API allowlist; `EVIDENCE_VAULT_ENABLED` defaults false.
- Do not treat an unavailable scanner as a clean scan; quarantine stays private and retrieval denies.
- Keep object names opaque; filenames, bytes, narratives, tokens, and scan content never enter audit or telemetry.
- Restrict evidence to the requesting staff member's tenant and a case they may access under the default-deny ABAC policy.
- Keep local files outside public/static paths with restrictive permissions; production uses private S3-compatible configuration and short-lived retrieval URLs.
- Preserve database runtime role separation, forced RLS, narrow grants, and disabled APIs.

## Review Focus

1. A valid-looking extension with a mismatched magic signature must not reach storage or become retrievable.
2. Scanner timeout, malformed scanner response, or malware finding must never result in a clean state.
3. Cross-tenant and unassigned same-tenant staff must not upload, inspect, retrieve, or delete evidence.
4. A retrieval ticket must be short-lived and bound to the evidence, tenant, case, user, and exact active staff session; every download is re-authorized and audited, and a leaked ticket must not outlive that session.
5. Legal hold, object deletion failure, and retries must remain visible and must not claim successful deletion.

---

### Task 1: Quarantine, validation, checksum, and scanning core

**Files:**
- Create: `src/backend/app/evidence_vault/storage.py`
- Create: `src/backend/app/evidence_vault/scanning.py`
- Create: `src/backend/app/evidence_vault/service.py`
- Test: `src/backend/tests/unit/test_evidence_vault.py`

**Interfaces:**
- `EvidenceStore.put_quarantine(key: str, source_path: str) -> None`, `promote(key: str) -> None`, `open(key: str)`, and `delete(key: str) -> bool`. The API owns signed retrieval tickets so every backend returns through the session/case reauthorization and audit path; direct object-store presigned URLs are not exposed.
- `MalwareScanner.scan(path: str) -> str` returns a scanner version only for a clean result and raises typed errors otherwise.
- `EvidenceVault.upload(...)` returns evidence metadata only after scanner success and private promotion.

- [x] Add tests for signature mismatch, oversize rejection, scan unavailable, malware rejection, checksum, private local file mode, public-root rejection, and clean promotion; run to confirm failures.
- [x] Implement the local private store, S3-compatible store, strict MIME/signature allowlist, ClamAV INSTREAM adapter, and fail-closed upload service.
- [x] Run the focused evidence tests, then the backend suite.

### Task 2: Tenant/case metadata and PostgreSQL RLS contract

**Files:**
- Modify: `src/backend/app/staff_auth/models.py`
- Create: `src/backend/app/infrastructure/database/migrations/versions/20261003_01_private_evidence_vault.py`
- Modify: `src/backend/app/infrastructure/database/security.py`
- Modify: `scripts/provision_postgres_roles.py`
- Modify: `src/backend/tests/integration/test_postgres_staff_rls.py`
- Modify: `src/backend/tests/unit/test_database_security_contract.py`
- Modify: `docs/security/DATA_BOUNDARY_MATRIX.md`
- Modify: `docs/government/data-governance-registry.yaml`

**Interfaces:**
- `EvidenceObject` uses a composite tenant/case foreign key; evidence rows are forced tenant-RLS and the application gets only workflow-scoped CRUD grants.
- The worker receives no evidence grants until a separately verified worker contract exists.

- [x] Add the mapped evidence table classification and prove matrix/registry parity fails before the schema inventory is updated.
- [x] Add tenant/case constraints, forced RLS, scoped policy, and migration downgrade behavior.
- [x] Extend disposable PostgreSQL tests for empty scope, cross-tenant reads/writes, cross-case tenant FK, and runtime-role non-bypass.
- [x] Run focused schema tests and the PostgreSQL integration against disposable PostgreSQL 16; run the backend suite.

### Task 3: Staff authorization and evidence lifecycle API

**Files:**
- Modify: `src/backend/app/staff_auth/authorization.py`
- Create: `src/backend/app/evidence_vault/api.py`
- Modify: `src/backend/app/config.py`
- Modify: `src/backend/app/__init__.py`
- Test: `src/backend/tests/unit/api/test_staff_auth.py`

**Interfaces:**
- Add default-deny `evidence:upload`, `evidence:read`, and `evidence:delete` actions for assigned/creator case officers only; auditor and tenant administrator grants do not imply evidence content access.
- Staff endpoints support upload, metadata, temporary retrieval, and hold-aware deletion. Every content retrieval is audited and re-authorized.

- [x] Add tests for unauthorized horizontal/vertical access, disabled feature state, clean retrieval tickets, session/case binding, ticket expiry, metadata-only audit, and legal-hold deletion denial; run to confirm failures.
- [x] Wire dependency-injected storage/scanner providers and endpoints while preserving the production allowlist block. Downloads proxy through the API; direct object-store presigned URLs are not exposed.
- [x] Run API tests and the full backend suite; check that production defaults deny the route.

### Task 4: Release evidence and governance record

**Files:**
- Modify: `docs/security/PHASE3_IMPLEMENTATION_STATUS.md`
- Modify: `docs/superpowers/plans/EXECUTION_LEDGER.md`
- Modify: `scripts/release_gate.sh` only if required to express the new evidence gate accurately.

- [x] Record implemented scope, tests, PostgreSQL availability, and remaining external dependencies; do not claim production readiness.
- [x] Run the release gate and preserve its nonzero result while any release blocker remains.
