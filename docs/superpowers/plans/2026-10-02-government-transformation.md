# SCMIRN Government Transformation Execution Plan

## Goal

Advance SCMIRN from mixed prototype workspaces to a source-verifiable citizen-resolution and government-interoperability platform while preserving Phase 3 production controls. Keep the repo buildable and each increment testable. The full supplied prompt is the requirements authority; this plan breaks it into reviewable local steps and does not imply external approval.

## Architecture and stack

- Flask + SQLAlchemy/Alembic backend; PostgreSQL restricted runtime identities and forced RLS.
- React + TypeScript + Vite public frontend.
- Official-source lifecycle and deterministic routing remain the only authority for public recommendations.
- Separate public, staff, governance and Labs route/workspace boundaries.
- No API integration is live without authorized credentials, a real endpoint and recorded evidence.

## Spec

[`docs/superpowers/specs/2026-10-02-citizen-resolution-platform-design.md`](../specs/2026-10-02-citizen-resolution-platform-design.md)

## Global constraints

- Work on the user-designated `main` baseline because the request explicitly directs continuing from it; preserve unrelated user changes (the tree was clean at start).
- No secrets, `.env`, production data, or logs in tool output or commits.
- Tests first for behavior changes. Do not replace release evidence or weaken controls to get green checks.
- Keep `STAFF_API_ENABLED=false`, keep non-allowlisted APIs blocked, keep government submissions and receipts unimplemented until authorized.
- Commit only after tests and review. Push only the completed, locally verified commit; report remote state exactly.

## Review Focus

1. Cross-tenant and cross-assignment reads/writes; missing attributes must deny, and error behavior must not create a case-ID oracle.
2. A stale/unverified source, ambiguous jurisdiction, failed connector or absent SLA must abstain instead of recommending, submitting, or inventing a deadline.
3. Duplicate/replayed staff MFA, case events, webhooks and retention work must not repeat sensitive side effects.
4. Citizen data, uploads, translated legal/eligibility content and logs must respect minimization, consent and retention boundaries.
5. Responsive/keyboard/screen-reader and offline/error states must remain usable without claiming a government service succeeded.

## Execution steps

### 1. Trust boundary and governance (current)

- Add a centralized default-deny ABAC evaluator and use it for staff case visibility and mutation; preserve database tenant filters and non-enumerating 404s. **Implemented for the existing four staff grants** in `authorization.py`; target citizen/operator/supervisor role provisioning and service-level scope remain open.
- Add negative unit and authenticated API tests before policy code.
- Add machine-readable data governance coverage and a CI parity gate for persisted fields. **Implemented** for all 452 current SQLAlchemy columns; strict release mode remains blocked on 254 personal/linkable field approvals and accountable privacy ownership.
- Complete missing ownership, role/reviewer-separation, privacy, evidence, retention, supply-chain, observability, backup and accessibility controls in independently reviewable slices. Keep blocked controls explicit.

### 2. Domain core

- Introduce normalized jurisdiction, department, office, service/source/rule versions, eligibility/evidence, SLA, grievance/escalation/appeal and event entities only with defined owner, scope, retention, authorization and migration.
- Migrate citizen routing toward versioned graph explanations; source staleness or missing provenance abstains.
- Add maker-checker review and append-only event semantics.

### 3. Interoperability contracts

- Define capability-based provider contracts, strict request/response schemas, idempotency, timeouts, replay protection, webhook signatures and sandbox contract tests.
- API Setu, Open311, DigiLocker, identity/federation, BHASHINI, department and state/ULB adapters remain disabled or blocked until genuine external prerequisites are supplied.

### 4. Product frontends

- Reframe citizen navigation around service resolution and source provenance; provide clear privacy/consent and abstention states.
- Add officer/admin screens only for real authorized APIs; unauthenticated users must never reach staff data.
- Move unsupported demos under an explicit Labs route, or remove them from production navigation. Every action maps to a real contract.
- Add localization architecture, Hindi only for verified copy, PWA/offline behavior, WCAG checks and responsive state coverage.

### 5. Assurance and bounded pilot profile

- Run backend/frontend/PostgreSQL/release/security/API/accessibility/build/restore/rollback checks against the exact candidate. Record unrun scans as not run.
- Add pilot configuration placeholders for one approved authority, geography, limited services, operator, infrastructure, identity, privacy basis and support process. Do not invent values or claim a pilot.
- Update product, security, privacy, integration and operations docs; self-review changed paths; commit each coherent increment.

## Current test-first task

- Files: `src/backend/app/staff_auth/authorization.py`, `src/backend/app/staff_auth/api.py`, `src/backend/tests/unit/test_staff_authorization.py`, `src/backend/tests/unit/api/test_staff_auth.py`.
- First add tests for default-deny/missing tenant/MFA/purpose, auditor read-only, reviewer separation, officer owner/assignment scoping, administrator tenant scoping and cross-tenant denial.
- Run the focused test and confirm it fails because the policy contract is absent.
- Implement the pure policy evaluator, integrate it with case list/read/create/status routes, and rerun focused then complete backend tests.
- Verify PostgreSQL tests use restricted runtime identities; never infer RLS coverage from SQLite.

## Verification and completion

Run the full repository gate only with its required disposable PostgreSQL and explicit production configuration prerequisites. Freshly capture results for each command. Scan changed files for disabled controls, false affordances, PII in logs, insecure fallbacks and stale docs. Do not mark the whole transformation complete while any internal requirement is open. Final verdict remains `NOT PRODUCTION READY` until every applicable external and internal proof is present.
