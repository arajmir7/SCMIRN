# Feature merge matrix

This matrix records each source behavior, its canonical landing point and bounded acceptance evidence. It does not convert a source README claim into a working capability. The local prototype integration is complete for these nine source-real behaviors; the result is not production readiness. Final dispositions are machine-checked by [`feature-parity.json`](feature-parity.json) and [`../../scripts/check_feature_parity.py`](../../scripts/check_feature_parity.py).

| Source ID | Source capability | Source state | Canonical target | Proposed disposition | Acceptance evidence / boundary |
|---|---|---|---|---|---|
| SRC-01 | Consent-gated description intake and sensitive-data warning | `PARTIAL` | Problem Solver panel and homepage route handoff | `INTEGRATED` | `src/frontend/tests/migration.spec.ts`: consent blocks submit; 8,000-character cap, privacy warning, clear/reset behavior and error/result states. |
| SRC-02 | Deterministic issue/urgency classification with emergency abstention | `PARTIAL` | `src/backend/app/source_routing/service.py` | `INTEGRATED` | `test_source_routing.py`: unknown/candidate abstention, urgent warning, synthetic verified source handoff; no LLM inference. |
| SRC-03 | Versioned official-source/service/authority/rule registry and effective window | `PARTIAL` | Routing models and Alembic migration | `INTEGRATED` | Version keys, foreign keys, constraints, ORM update guards; SQLite upgrade/downgrade and disposable PostgreSQL 16 TLS upgrade passed at revision `20261001_01`; audit UPDATE trigger rejected mutation. Registry seed remains unavailable and inactive; full schema baseline, RLS, delete denial and rollback remain unverified. |
| SRC-04 | SHA-256 provenance gate and source record endpoint | `PARTIAL` | Triage service, source endpoint and `AssistantPanel` | `INTEGRATED` | HTTPS + 64-hex hash + `VERIFIED` + dates; browser handoff helper fails closed; current candidate has no hash. |
| SRC-05 | Source-verified service catalog and evidence checklist | `PARTIAL` | `/api/v1/services`, `/api/v1/evidence/check` | `INTEGRATED` | Empty catalog and unverified evidence status tested; only identifiers accepted, no evidence upload implied. |
| SRC-06 | Idempotency, keyed fingerprint and 30-day decision record | `VERIFIED_WORKING` within source tests | Triage endpoint and `route_decisions` | `INTEGRATED` | Same key/input replays; key reuse with changed facts returns 409; DB assertion confirms raw description absent. |
| SRC-07 | Expiry purge and count-only retention event | `PARTIAL` | `purge-route-decisions` CLI | `INTEGRATED` | Dry-run, expiry deletion and audit tests pass. Runtime scheduling, alerting and deletion verification remain `NOT VERIFIED`. |
| SRC-08 | Append-only hash-chained metadata audit | `PARTIAL` | Audit service, model hooks and PostgreSQL migration trigger | `INTEGRATED` | Sensitive-field rejection and tamper tests pass; SQLite migration passes; disposable PostgreSQL trigger rejected an UPDATE. Delete denial, external anchoring and database-owner tampering are unverified. |
| SRC-09 | Citizen route outcome, provenance and not-submitted status | `PARTIAL` | `AssistantPanel` and `resolution.ts` handoff guard | `INTEGRATED` | Browser verifies uncertain result and `NOT_SUBMITTED`; synthetic valid handoff has a hash gate; no agency filing exists. |

## Explicitly excluded source candidates

These do not enter the parity denominator because code tracing shows they are not usable source features in the active source release. They remain visible in the source inventory:

| Candidate | Evidence | Action |
|---|---|---|
| Flask legacy cases, documents, tracker, offices, AI and public map | Active handlers return 410/503 unavailable responses | Do not duplicate canonical feature labels or revive disconnected prototypes. |
| Agent/HITL pages, TypeScript/Fastify runtime and nested Vite app | Not wired to the active Flask `run:app` and React route table | Exclude as `UNREACHABLE`/`DUPLICATE`; retain the canonical runtime only. |
| Seeded SQLite user/case/chat/document data | Contains report text/contact details and generated content | Exclude all rows; never merge source data. |
| Cybercrime official handoff | Candidate page retrieval unavailable; missing document hash | Keep record unavailable; no active official route until a human verifies an authoritative snapshot. |

## Visual integration rule

The source Tailwind UI is not copied. The new interaction uses existing SCMIRN colors, Bootstrap controls, card treatment, typography, responsive breakpoints, navigation, map and footer. Unsupported metrics and live/official claims are qualified in the claims register without replacing the page composition.
