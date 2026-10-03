# SCMIRN execution state

**Baseline snapshot date:** 2026-10-02 (Asia/Kolkata)
**Release verdict:** `NOT PRODUCTION READY`  
**Scope:** Repository implementation, local checks, and read-only retrieval of public official source pages. No agency was contacted, no account or private API was used, and no government submission was made.

> The sections below preserve the 2026-10-02 baseline. Current verification and
> remaining release status are recorded in the 2026-10-03 continuation at the
> end of this document.

## BASELINE SNAPSHOT (2026-10-02)

- **Frontend:** React 18, TypeScript, Vite, React Router, Bootstrap and Leaflet under `src/frontend`. The home page starts with a problem statement and consent handoff to the deterministic route checker. A `/staff` browser workspace now exposes the bounded metadata-only staff API flow; browser tests use synthetic responses and do not establish production authentication. Legacy office, heatmap, tracker, analytics, document and advanced workspaces are grouped under `/labs` with prototype disclosures; prior direct routes redirect there. The current Playwright suite has 13 browser flows. No route-wide automated accessibility suite is configured.
- **Backend:** Flask application factory, SQLAlchemy, Flask-Migrate, JWT extension, Flask-Caching and Flask-Limiter under `src/backend`. The codebase mixes legacy issue/SRS endpoints with a newer `source_routing` module and partially layered domain/application packages.
- **Persistence:** Development/testing may use SQLite and `db.create_all()`. Production config requires PostgreSQL and turns off automatic table creation. Alembic head `20261002_04` builds all 34 ORM tables; exact unversioned schemas and legacy-only schemas are preflighted and preserved, while unknown tables, partial staff schemas or detected drift fail before DDL. Six migration tests use isolated SQLite databases. The full chain, four-role grants, forced staff RLS, audit write/read split and startup checks passed a disposable PostgreSQL 16 test; no production database was used. Nine legacy tables remain quarantined without app/worker grants.
- **Routing and registry:** `source_routing` has versioned source, authority, service and rule records; effective dates; deterministic phrase matching; consent; geography checks; idempotency; bounded derived facts; retention deadlines; and metadata-only audit events. The machine-readable catalog imports five `OFFICIAL_HANDOFF_ONLY` candidates from current official pages. Four pass provenance/hash/host checks; the cybercrime portal remains `DRAFT` because standard TLS verification reported an expired certificate. No route creates a government filing or receipt.
- **Urgency:** The classifier detects only a narrow possible-immediate-danger phrase signal. It does not assess severity. Route matches and phrase signals retain `UNASSESSED` until a reviewed severity policy exists.
- **AI:** Legacy AI and legal-analysis code exists, but it is not grounded in a reviewed source corpus. Production allows no generative AI route. The current source-gated route path is deterministic and does not send text to an LLM.
- **Identity and authorization:** A local operator-provisioned staff password+TOTP flow now has one-use signed MFA challenges, replay prevention, AES-GCM-encrypted TOTP secrets, hashed opaque sessions, CSRF checks, idle/absolute expiry, password change/reset, account disable, lockout, and tenant role guards. A metadata-only tenant case API is available. Staff RLS and the live login/MFA/case API path passed against disposable PostgreSQL 16; legacy records have no complete tenant model. Staff APIs remain disabled by default through `STAFF_API_ENABLED=false`. OpenAPI and synthetic production-route parity allow 15 paths; 93 other registered API operations return 503.
- **Documents and evidence:** Draft templates are frontend-side examples. There is no verified private evidence vault, malware scanning, encrypted object store, signed download, redaction or deletion workflow. Legacy upload routes are disabled in production.
- **Integrations:** No live or sandbox government connector is verified. Existing catalog documentation marks these unavailable/not implemented. There is no verified CPGRAMS, API Setu, ServicePlus, UMANG, DigiLocker, MeriPehchaan, BHASHINI, eSign, RTI, consumer, cybercrime, eCourts, legal-aid or municipal API connection.
- **Queues, storage and observability:** Redis supports production cache/rate-limit/readiness configuration. No durable queue/workflow engine or production object store is configured. Request IDs and privacy-preserving exception logging exist; production metrics, tracing, SIEM delivery, actionable alert routing and measured SLOs do not.
- **Security and operations:** Production config validation enforces TLS, CA paths, secrets and HTTPS CORS origins. Docker base images and Python dependencies are pinned; local release-tag reuse is rejected. The 2026-10-03 partial candidate scan now covers source checks, dependency locks, IaC, and two local ARM64 images; the backend and IaC retain open findings. DAST, other service-image scans, published release images, signed provenance, backup/restore, DR, and rollback rehearsal remain absent.
- **Build and tests:** Current backend suite: 81 passed with the opt-in PostgreSQL RLS integration enabled, in a temporary Python 3.11 environment installed from the hash-locked development lockfile, with two existing SQLAlchemy `Query.get()` deprecation warnings. PostgreSQL tests cover all four provisioned roles, denied app DDL and audit reads, auditor read-only access, and RLS. Current frontend verification: typecheck passed, Vite production build passed, and all 13 Playwright flows passed (7.9 seconds). The strict frontend-design-premium audit reported zero findings. These are local checks; browser API responses are mocked. Feature parity: 9/9. OpenAPI route gate: 15 allowlisted paths documented; 93 other registered API operations returned 503. The release gate exits 1 by design while production controls remain open.
- **Repository metadata and sensitive artifacts:** This workspace now has a Git baseline and source-tree traceability record. Existing development database, upload and log files were not opened during this assessment. Real `.env` files were not read.

## TARGET

Build a modular monolith that accepts a citizen's problem in plain language, uses versioned deterministic rules and official source evidence to identify a responsible service, shows evidence readiness and a transparent next step, and distinguishes SCMIRN records from official submissions. External actions must remain explicit, authorized and supported by an authoritative receipt. Citizens must be able to use the service accessibly and in Indian languages. Government deployment claims require operational and independent evidence.

## GAPS

1. The route engine still needs reviewed urgency and jurisdiction policies, stable explanation codes, multilingual/adversarial coverage, and an evidence-backed replayable test corpus. Local synthetic state/district matching now fails closed.
2. The registry has a deterministic checked-in catalog and page hashes, but lacks authenticated review/publication, reviewer separation, independent legal review, and scheduled re-verification. The cybercrime portal cannot be activated until its TLS/source review succeeds.
3. Staff password+TOTP identity, tenant roles and API/database tenant checks exist, with local PostgreSQL 16 evidence; deployment runtime-role behavior and legacy-record tenant scope remain unverified, and citizen identity/SSO are not implemented.
4. A bounded metadata-only case/status API and initial `/staff` browser workspace exist. There is no assignment/appeal/service-level work queue, evidence vault, citizen linkage, or official status federation; staff production access remains disabled by default.
5. Evidence requirements are registry metadata only; there is no consent/purpose-bound vault or safe upload pipeline.
6. Connectors are unverified; no authorized API contracts, credentials, sandboxes, receipt validation or operational ownership are present.
7. Multilingual processing, language-preserving records, accessible assisted-service/CSC flows and low-bandwidth offline behavior are not established.
8. No production queue, object storage, telemetry/alerting, backup/restore proof, DR targets, performance evidence, or production deployment operator exists.
9. Security, accessibility, AI grounding and privacy retention controls lack route-wide independent evaluation.
10. Legacy/demo workspaces now route through `/labs` and carry prototype disclosures. The information architecture is clearer, but route-wide accessibility, localization, and capability validation remain open.

## DECISIONS

- Keep the Flask/React modular monolith; do not add microservices or a workflow engine before a durable, authorized case workflow justifies it.
- Do not add a government connector or legal rule without current official provenance and required authorization. Public links remain handoffs, and only bounded facts reviewed from official sources are cataloged.
- A missing or stale source means abstention. Do not claim agency submission without an authoritative acknowledgement.
- Do not ingest ZIP/database contents that may contain citizen data; use synthetic fixtures only.
- Keep staff routes disabled in production until the approved deployment PostgreSQL role/configuration, authorization, and audit controls are validated. The local disposable PostgreSQL test is not deployment evidence. Keep uploads and legacy APIs gated.
- Preserve the current 15-path production allowlist with staff routes disabled by default; fail closed for all legacy APIs.
- Treat local builds and the prior disposable database rehearsal as bounded evidence, not a current deployment or government approval.

## IMPLEMENTED

- Prior hardening: TLS/CA config validation, hash-pinned dependencies, image digest pins, request IDs and safe exception logs, route allowlist, route/method contract gate, release-tag uniqueness check, application rollback helper, CI action pinning, feature ledger, ADRs, claims/maturity/capacity records and operator runbooks.
- Existing source-routing slice: versioned registry models, deterministic route selection, explicit consent, sensitive-text minimization, idempotency, 30-day decision-retention deadline, abstention for unverified sources, `NOT_SUBMITTED` handoff status and hash-chained audit metadata.
- Phase 2 work: added the full ORM Alembic baseline and source lifecycle migration; a deterministic official source/service catalog with four eligible handoffs; staff password+TOTP/session/RBAC flow; tenant-scoped metadata case workflow; and PostgreSQL RLS for new staff tables. SQLite tests and a PostgreSQL 16 disposable-database integration test pass; production role/configuration and legacy tenant scope remain unverified.

## BLOCKED

- Cybercrime portal source refresh depends on the portal's TLS certificate being valid and the public source being reviewable.
- Official service/source onboarding beyond safe public handoffs requires an accountable agency owner, authoritative current documents/data, written usage permission, and any needed authorized sandbox/API credentials.
- Identity federation/role mapping, organizational account recovery, and legacy case-data ownership require the selected deployment's identity provider and data ownership model; the local staff password+TOTP prototype is not an SSO integration.
- Legal basis, purpose/retention approval, DPDP review, sharing agreements, residency and citizen-facing notices need accountable legal/privacy owners.
- API Setu and other platform connections require approved consumer/publisher registration, current contracts, credentials and sandbox confirmation.
- Production operation requires a hosting operator, approved TLS ingress, secret/KMS, database/object storage, monitoring/SIEM, backup/DR and incident ownership.
- Independent security and accessibility review and any required government/STQC/CERT-In assessment require external assessors and scope.

## VERIFIED

- Backend: 81 tests passed in the hash-locked Python 3.11 environment with the opt-in PostgreSQL integration enabled; the two warnings are existing SQLAlchemy `Query.get()` deprecations. Six isolated SQLite migration tests cover zero-to-head, exact full schema, legacy-only schema, drift rejection, and status conversion/constraints. PostgreSQL 16 integration covers migration head `20261002_04`, four database roles, staff RLS, audit privilege separation and overprivileged-role rejection.
- Official page retrieval: nine sources passed standard TLS and returned a content hash; the cybercrime portal did not pass TLS validation and remains `DRAFT`. Four active handoff candidates are exposed; no endpoint submits forms or creates official references.
- Dependency scans: `pip-audit` reported no known vulnerabilities for the hash-locked Python dependencies; `npm audit` reported zero findings for the frontend lockfile. Python and frontend CycloneDX dependency SBOMs were generated. This does not cover source code, secrets, images/OS packages, or signed build provenance.
- Frontend: the prior 8-flow result is a historical snapshot. Current `npm run typecheck` and `npm run build` passed; `npm run test:e2e` passed all 13 tests in 7.9 seconds. The strict premium UI audit returned 0 findings. Browser staff-service responses were mocked; no production connection was used.
- Source feature parity: 9 features integrated, 0 unexplained.
- OpenAPI 3.1 contract and synthetic production-route gate passed: 15 allowlisted paths; 93 other registered API operations returned 503.
- The 2026-10-02 release gate passed all seven executable checks, including production configuration/Compose validation and local backend/frontend image builds using temporary synthetic secrets and placeholder CA files. It did not start a deployment or contact PostgreSQL/Redis. Its final exit code is 1 because documented production blockers remain.
- Government readiness Markdown relative links resolve. This checks links only, not whether linked claims are externally certified.
- A prior disposable PostgreSQL 16/Redis 7 TLS rehearsal passed a narrow migration/trigger/readiness/proxy smoke scope; it predates the latest source.

## UNVERIFIED

- Live government integration, legal correctness, source refresh/currentness, jurisdiction accuracy, emergency-service coverage, and localization accuracy.
- Production PostgreSQL migration/RLS execution and production runtime-role ownership/bypass properties. The local disposable PostgreSQL 16 test verified staff-table policies and cross-tenant denial; legacy-table tenant design is still open.
- Legacy-record tenant design, production staff UI/API integration and deployment auth, concurrency, assignment/appeal queues, official receipt lifecycle, secure evidence storage and deletion.
- Complete release-scope security evidence (including DAST, every release image, vulnerability disposition, and signed provenance), accessibility audit, performance/capacity, backup/restore, DR, rollback and alert response. Partial source/dependency/IaC scans and two local image scans are recorded in the 2026-10-03 candidate report; they do not close the release control.
- Production data residency, external HTTPS/WAF boundary, approved hosting and operating procedures.

## RISKS

- Urgency remains `UNASSESSED`; the narrow phrase signal is not comprehensive emergency detection and must not be marketed as such.
- Handoff URLs are limited to a verified source's exact host, but static checked-in hashes do not replace authenticated review, independent source validation, or scheduled refresh.
- Public source-route endpoints are unauthenticated and rate-limited; privacy abuse, shared-cache behavior and multi-instance limit behavior need assessment.
- Audit hashes and database triggers do not protect against a privileged database owner; there is no independent immutable anchor.
- Existing local demo persistence and sample workflows must not be used with real citizen data.
- This workspace is version-controlled and synced to `origin/main`; preserve commit and push evidence for each subsequent release increment.

## NEXT ACTION

1. Repeat the PostgreSQL/RLS integration test in CI and validate the approved deployment database role/configuration before enabling staff routes.
2. Decide the tenant model for legacy citizen/issue/document/chat/routing records; keep shared-tenant production data disabled until migrated and tested.
3. Review the initial staff workspace against the deployment identity/API contract, then build authenticated source lifecycle/publishing and refresh the cybercrime source only after TLS validation succeeds.
4. Implement a private scanned evidence vault and tenant-bound retention/deletion before accepting files.
5. Add multilingual/adversarial routing evaluation, accessibility verification, observability, performance, backup/restore, and DR evidence.

## CURRENT STATUS (2026-10-03)

The release verdict remains **`NOT PRODUCTION READY`**. The current schema has
35 mapped tables and 471 columns. The data-governance registry contains 294
potentially personal/linkable candidates: 273 await accountable field approval
and 21 are explicitly exempted. The release checker reports 35 table-governance
decisions and one profile approval as separate accountable decisions.

The full candidate gate ran with the disposable PostgreSQL 16 RLS URL: **114
backend tests passed**, including PostgreSQL RLS integration (118 existing
deprecation warnings); governance parity passed; frontend typecheck and build
passed; **13 Playwright flows passed**; feature parity passed 9/9; OpenAPI 3.1
route parity passed. The production gate permits 15 route patterns and rejects
99 other registered operations with 503. Triage and jurisdiction resolution
remain disabled in production because `route_decisions` is not tenant/subject
isolated. The four current public catalog records are handoff-only and the
cybercrime candidate remains withheld.

The release gate exited 1 as intended: 12 blocking engineering workstreams are
`OPEN`; eight privacy, government authorization, infrastructure, independent
assessment and operations records are `BLOCKED_EXTERNAL_DEPENDENCY`. No
authorized production environment file, secrets, or CA configuration was
supplied. No production deployment, independent accessibility assessment,
published-release all-layer scan or signed provenance, backup/restore/DR
rehearsal, or live SIEM operation is evidenced. A partial local candidate
security scan and two image SBOMs are recorded in the
[assurance data room](../assurance/README.md); backend and IaC findings remain
open, and DAST/provenance and other service-image scans remain unavailable.
See the [typed blocker ledger](../release/production-blockers.yaml).

### Candidate security evidence — 2026-10-03

The [machine-readable scan report](../assurance/evidence/security-release.json)
records scans against source commit `51260c1` and two locally built ARM64 images.
Semgrep reported zero findings across 231 tracked files; Bandit reported six
LOW findings; dependency audits reported zero known vulnerabilities in the
locked Python and frontend dependencies; Gitleaks found zero secrets in the
single-commit delta. Trivy reported 44 HIGH and 60 MEDIUM backend image records
across 73 unique advisories, no frontend image vulnerabilities, and six open
infrastructure findings. The two CycloneDX SBOMs are package inventories only,
not vulnerability analysis or signed provenance. The result is partial and
does not close ENG-005.
