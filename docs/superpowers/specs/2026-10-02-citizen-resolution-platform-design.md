# SCMIRN Citizen Resolution Platform Design

**Status:** approved for implementation from the user supplied execution prompt  
**Baseline:** `main` at `e3223ff4bace21bb16dba5feb912f3e3d6d6ed14`  
**Product claim:** source-verifiable citizen resolution and government interoperability; never a replacement government portal.

## Product and users

The primary user is a citizen trying to understand the next official action for a public service or grievance. Supporting users are assisted-service operators, government officers, service and source reviewers, tenant administrators, and auditors. The service must explain where a route came from, what evidence is required, whether an official service-level deadline is verified, and whether the action remains with the citizen or was actually submitted.

The public interface is a responsive web application. Staff, governance, and connector operations are separate authenticated planes. Prototype workspaces stay in a clearly marked Labs boundary and never imply live records or agency connectivity.

## Approved architecture

1. **Citizen resolution portal:** deterministic, source-bound resolution and official handoff; explicit abstention; consent and privacy controls; no autonomous legal or jurisdictional decision by an LLM.
2. **Officer workspace:** tenant and jurisdiction scoped, MFA gated, append-only case events, assignment aware access, audited actions. It stays disabled until identity, RLS and deployment prerequisites pass.
3. **Service and source workbench:** versioned service/source/rule records, freshness and maker-checker lifecycle, no automatic publication from scraping or translation.
4. **Integration and trust plane:** capability based adapters, sandbox contracts, signed events and explicit fail-closed status. Credentials and external authority are not present in this repository.

## Trust and data boundaries

- Preserve the Phase 3 Postgres identities, forced RLS, migration separation, audit separation, public API allowlist, TLS verification, retention deadlines and `NOT_SUBMITTED` contract.
- Keep the 9 legacy unclassified tables and other unscoped data quarantined until ownership, jurisdiction/subject boundaries, migration, RLS and restricted-role tests are proven.
- Persist only bounded derived routing facts. Do not copy citizen free text into logs, metrics, traces or analytics.
- Do not enable staff, evidence upload, submission, receipt or status sync based on configuration alone.
- Any missing tenant, ownership, assignment, reviewer separation, source verification or external prerequisite results in denial/abstention.

## Resolution graph and lifecycle

The target graph is intent → need → geography → jurisdiction → authority → service version → eligibility/evidence → official channel → external receipt/status → SLA → escalation/appeal → outcome. Every authoritative edge carries a reviewed source/version/hash, effective period, jurisdiction and routing-rule version. SCMIRN-generated identifiers are never called government references. An SLA is shown only from an approved current source; otherwise the UI says `OFFICIAL SLA NOT VERIFIED`.

Case events are append only; the current internal state is derived from events. External status and receipt remain separate and unavailable until a contract is authorized and verified. Failed connectors never turn into a successful submission.

## UI and interaction direction

- Information-first civic service UI with clear route, source provenance, last review state, required next action and `NOT SUBMITTED` status.
- Existing runtime CSS and font values remain the canonical token source until deliberately changed and verified. `DESIGN.md` mirrors those values; it does not introduce a parallel token set.
- Mobile/reflow, keyboard/focus, readable errors, loading/empty/offline/unavailable/stale-source states and touch-friendly controls are required.
- No fake KPI counts, institutional marks, decorative live-status indicators, inert buttons or implied agency endorsement.
- Existing analytics, map, tracker, generator and broad legacy consoles are Labs only unless backed by an allowed, evidenced API.

## External readiness boundary

API Setu, department systems, ServicePlus, CPGRAMS, DigiLocker, identity/federation, BHASHINI, Open311 and state/municipal systems remain `BLOCKED_EXTERNAL_DEPENDENCY` until approved specifications, sandbox credentials, accountable owners, legal/privacy review and external test evidence exist. No provider is to be called live or sandbox verified solely because an interface or fake server exists.

## Decisions requiring accountable review

This specification does not decide legal processing bases, retention periods, official SLA values, source owners, government identity assurance, evidence policies or agency workflow. Those need named privacy/legal/department/identity owners. Unknowns remain configuration placeholders or blocked states.
