# Data model matrix

| Source model/table | Purpose and persisted fields | PII / retention | Canonical mapping / migration decision |
|---|---|---|---|
| `OfficialSource` / `official_sources` | Versioned publisher/title/type/jurisdiction/HTTPS URL/hash/review/effective/reviewer/parser fields | No citizen PII; immutable versions; legal-source freshness needs a human review lifecycle | Add as source registry table; unavailable candidate seeded with `document_hash=NULL`, never active. |
| `Authority` / `authorities` | Versioned authority identity, hierarchy, geography, source FK, effective status | No citizen PII; immutable versions | Add with FK to source; only source-backed status supports routing. |
| `GovernmentService` / `government_services` | Versioned service description, authority, jurisdiction, evidence lists, official/grievance channels, connector mode/SLA | No citizen PII; may contain official contact channels | Add; no real connector is installed or authorized. |
| service/source association | Many-to-many link between service version and official sources | No citizen PII | Add; route gate requires selected source IDs belong to service. |
| `RouteRule` / `route_rules` | Versioned terms/exclusions/authority/service/source IDs/priority/effective dates | No citizen PII | Add; seed cyber-fraud candidate as unavailable-source configuration. |
| `RouteDecision` / `route_decisions` | HMAC input fingerprint, bounded facts/output, rule/service/source versions, outcome, expiry, idempotency hash | Raw report description is not stored; route metadata expires after 30 days | Add; verify query and output do not carry free text; run retention purge. |
| `AuditEvent` / `audit_events` | Sequence, actor/tenant metadata, action/object, bounded details, timestamps, previous/event hashes | Must reject description, document, address, phone, token and related sensitive fields | Add; metadata-only hash chain, DB triggers. Not external/WORM immutability. |

## Candidate source DB — explicitly not imported

The ZIP database was deserialized in memory and inspected only for schema names and table row counts. It contains 11 tables: `users` 1, `civic_issues` 7, `civic_problems` 22, `generated_documents` 2, `issue_updates` 7, `departments` 16, `problem_categories` 5, `chat_sessions` 13, `chat_messages` 26, `government_offices` 0, `issue_media` 0. User/report text, contact details, AI analysis and generated document content are personal/sensitive information. No row values were printed or copied. All source data is rejected for migration; build target tables from reviewed schemas only.

## Canonical baseline model families

At the inventory baseline, `src/backend/app/infrastructure/database/models.py` defined `issues`, `users`, `documents`, `offices`, `chat_logs`, IoT assets/readings, simulated blockchain transactions, gamification, resilience hubs, SRS issues/events/work orders/assets/utilities/budget/audit rows; initialization used `db.create_all()` and no versioned migration directory existed. Several tables store report/chat text or demo metrics. Do not map source route decisions into citizen case records or the legacy chat log.

## Post-merge schema and production behavior

`src/backend/app/infrastructure/database/migrations/versions/20261001_01_source_gated_routing.py` creates only the seven new source-routing/metadata-audit tables and their indexes/constraints. The Alembic rehearsal passed on a fresh temporary SQLite database with both upgrade and downgrade, and on disposable PostgreSQL 16 with TLS and hostname verification. A direct audit-row UPDATE was rejected by the PostgreSQL trigger. Production disables automatic table creation and fails startup if any required routing/audit table is missing; an isolated `SCMIRN_MIGRATION_MODE=true` command skips that check and rejects all application traffic. The later baseline covers all 35 ORM tables at Alembic head `20261003_02`; that revision adds date-only source review fields without inventing retrieval/verification timestamps. Staff/case/evidence RLS passed a separate disposable PostgreSQL 16 test. This routing migration is not a baseline for the legacy model families and does not add RLS to route/audit rows. Production role grants, legacy tenant isolation, backup/restore, route/audit delete denial and downgrade procedure remain unverified.

## Merge controls

- Use fresh schema only for new registry, decisions and audit models; never migrate source database rows.
- Use unique `(key, version)` constraints and foreign keys; registry version updates must create a new row.
- Route decisions keep derived facts and HMAC, not free text. The HMAC is not a substitute for deletion or encryption.
- Purge only expired decisions; append a count-only audit event in the same controlled operation.
- SQLite and PostgreSQL are not equivalent evidence. The local PostgreSQL tests cover the staff/case RLS boundary but do not prove legacy row-level isolation, production migration safety across existing schemas, concurrency, backup/restore or rollback.
