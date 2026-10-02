# Phase 3 production-control status

**Assessment date:** 2026-10-02. **Release verdict:** `NOT PRODUCTION READY`.
This is repository and disposable-environment evidence only. No production
database, identity provider, object store, host, or government service was used.

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
- A production worker contract, scheduled retention purge, private evidence
  object store, malware scanning, signed downloads, and verifiable deletion.
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
