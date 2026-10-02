# Database schema inventory

Purpose: generated inventory of ORM-managed tables, columns, foreign keys, indexes, uniqueness rules, and check constraints. Alembic revisions remain the executable schema source of truth.

## Migration and adoption behavior

- 20261001_01 creates the source routing registry, route decisions, and append-only routing audit table.
- 20261002_01 creates the legacy ORM tables. Its downgrade is blocked because dropping canonical application tables is destructive.
- 20261002_02 translates legacy source states to the explicit DRAFT, VERIFIED, SUPERSEDED, or REVOKED lifecycle.
- 20261002_03 adds tenant/staff identity, MFA/session, role, metadata-only case workflow and audit tables; it defines PostgreSQL RLS policies and append-only staff-history triggers.
- An empty database upgrades to head. Existing exact ORM schemas are preserved and upgraded; legacy-only schemas are preflighted; unknown tables or structural drift fail before DDL.
- Production keeps AUTO_CREATE_DB=False; migration is an explicit operator action. Development and test profiles still allow ORM auto-creation.

## Tenant isolation status

The new staff identity and case tables carry tenant_id. The PostgreSQL revision enables and forces RLS on these tables, scopes staff-table policies to transaction-local scmirn.tenant_id, and scopes staff_sessions to its exact SHA-256 token hash in scmirn.staff_session_hash. Tenant-consistent composite foreign keys protect staff, MFA, case creator and case-event relationships. The tenant directory has a read-only lookup policy for the slug-to-ID step required at login; it contains no user or case details.

The full migration chain and RLS policies were executed against a disposable PostgreSQL 16 database. An integration test used a non-owner, non-BYPASSRLS runtime role and verified forced RLS, tenant-scoped reads and writes, session-hash access and user-scoped session revocation, the staff password/TOTP and case APIs, and append-only history triggers. This is local test evidence, not a production deployment. Before enabling staff routes in a deployment, verify its migration/runtime role configuration and repeat the checks against the approved deployment setup. Legacy issue, document, chat, routing, and other non-staff records do not have a complete tenant model and remain outside this shared-tenant boundary.

Staff MFA secrets are AES-GCM encrypted with the configured 32-byte STAFF_MFA_ENCRYPTION_KEY; production configuration validates the key only when STAFF_AUTH_ENABLED=true. Session tokens are opaque and only their SHA-256 hashes are stored. Cases accept a bounded type and priority, not arbitrary citizen text or uploads. Staff and case history append-only triggers are present only in PostgreSQL.

## Tables

### audit_events

| Column | Type | Null | Default |
|---|---|---:|---|
| sequence (PK) | INTEGER | no | — |
| event_id | VARCHAR(36) | no | <callable default> |
| tenant_id | VARCHAR(120) | no | — |
| actor_id | VARCHAR(255) | no | — |
| actor_role | VARCHAR(40) | no | — |
| action | VARCHAR(120) | no | — |
| object_type | VARCHAR(80) | no | — |
| object_id | VARCHAR(120) | no | — |
| details | JSON | no | <callable default> |
| occurred_at | DATETIME | no | <callable default> |
| previous_hash | VARCHAR(64) | no | — |
| event_hash | VARCHAR(64) | no | — |

**Indexes:** ix_audit_events_occurred_at (occurred_at; non-unique); ix_audit_events_tenant_id (tenant_id; non-unique).

**Unique constraints:** unnamed (event_hash); unnamed (event_id).

### authorities

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | <callable default> |
| authority_key | VARCHAR(120) | no | — |
| version | INTEGER | no | — |
| canonical_name | VARCHAR(500) | no | — |
| authority_level | VARCHAR(32) | no | — |
| jurisdiction | JSON | no | <callable default> |
| official_source_id | VARCHAR(36) | yes | — |
| status | VARCHAR(32) | no | UNVERIFIED |
| effective_from | DATETIME | yes | — |
| effective_until | DATETIME | yes | — |
| created_at | DATETIME | no | <callable default> |

**Foreign keys:** official_source_id -> official_sources.id.

**Indexes:** ix_authorities_authority_key (authority_key; non-unique).

**Unique constraints:** uq_authority_version (authority_key, version).

**Check constraints:** ck_authority_positive_version: version > 0; ck_authority_level: authority_level IN ('CENTRAL', 'STATE', 'DISTRICT', 'LOCAL', 'REGULATOR', 'OTHER').

### blockchain_tx

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | INTEGER | no | — |
| tx_hash | VARCHAR(66) | no | — |
| block_number | INTEGER | yes | — |
| contract_address | VARCHAR(42) | yes | — |
| status | VARCHAR(20) | yes | CONFIRMED |
| payload_hash | VARCHAR(64) | no | — |
| created_at | DATETIME | yes | <callable default> |

**Unique constraints:** unnamed (tx_hash).

### chat_logs

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | INTEGER | no | — |
| session_id | VARCHAR(50) | yes | — |
| message | TEXT | yes | — |
| response | TEXT | yes | — |
| intent | VARCHAR(50) | yes | — |
| confidence | FLOAT | yes | — |
| timestamp | DATETIME | yes | <callable default> |

### documents

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | INTEGER | no | — |
| public_id | VARCHAR(16) | no | — |
| user_id | INTEGER | yes | — |
| doc_type | VARCHAR(50) | no | — |
| status | VARCHAR(20) | yes | draft |
| title | VARCHAR(200) | yes | — |
| template_data | TEXT | yes | — |
| file_path | VARCHAR(500) | yes | — |
| file_size | INTEGER | yes | — |
| jurisdiction | VARCHAR(50) | yes | — |
| created_at | DATETIME | yes | <callable default> |
| generated_at | DATETIME | yes | — |
| downloaded_at | DATETIME | yes | — |

**Foreign keys:** user_id -> users.id.

**Unique constraints:** unnamed (public_id).

### government_service_sources

| Column | Type | Null | Default |
|---|---|---:|---|
| service_version_id (PK) | VARCHAR(36) | no | — |
| source_id (PK) | VARCHAR(36) | no | — |

**Foreign keys:** service_version_id -> government_services.id; source_id -> official_sources.id.

### government_services

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | <callable default> |
| service_key | VARCHAR(120) | no | — |
| version | INTEGER | no | — |
| canonical_name | VARCHAR(500) | no | — |
| description | TEXT | yes | — |
| authority_id | VARCHAR(36) | no | — |
| department | VARCHAR(255) | yes | — |
| authority_level | VARCHAR(32) | no | — |
| jurisdiction | JSON | no | <callable default> |
| geography | JSON | no | <callable default> |
| eligibility | TEXT | yes | — |
| exclusions | JSON | no | <callable default> |
| issue_types | JSON | no | <callable default> |
| required_evidence | JSON | no | <callable default> |
| recommended_evidence | JSON | no | <callable default> |
| optional_evidence | JSON | no | <callable default> |
| application_channel | VARCHAR(2048) | yes | — |
| grievance_channel | VARCHAR(2048) | yes | — |
| appeal_channel | VARCHAR(2048) | yes | — |
| escalation_channel | VARCHAR(2048) | yes | — |
| official_url | VARCHAR(2048) | no | — |
| integration_mode | VARCHAR(48) | no | — |
| connector_id | VARCHAR(120) | yes | — |
| identity_assurance_required | VARCHAR(8) | no | A0 |
| official_sla | JSON | yes | — |
| effective_from | DATETIME | yes | — |
| effective_until | DATETIME | yes | — |
| last_verified | DATETIME | yes | — |
| status | VARCHAR(40) | no | UNVERIFIED |
| created_at | DATETIME | no | <callable default> |

**Foreign keys:** authority_id -> authorities.id.

**Indexes:** ix_government_services_service_key (service_key; non-unique).

**Unique constraints:** uq_government_service_version (service_key, version).

**Check constraints:** ck_government_service_integration_mode: integration_mode IN ('CONNECTED', 'SANDBOX_CONNECTED', 'CONNECTOR_IMPLEMENTED_NOT_AUTHORISED', 'OFFICIAL_HANDOFF_ONLY', 'PLANNED', 'UNAVAILABLE'); ck_government_service_status: status IN ('ACTIVE', 'DEPRECATED', 'SUPERSEDED', 'TEMPORARILY_UNAVAILABLE', 'UNVERIFIED'); ck_government_service_positive_version: version > 0.

### iot_assets

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | — |
| asset_type | VARCHAR(50) | no | — |
| lat | FLOAT | no | — |
| lng | FLOAT | no | — |
| ward | VARCHAR(100) | yes | — |
| health_score | INTEGER | yes | 100 |
| status | VARCHAR(20) | yes | OPTIMAL |
| predictive_maintenance_due | DATETIME | yes | — |
| last_reading | TEXT | yes | {} |
| updated_at | DATETIME | yes | <callable default> |
| created_at | DATETIME | yes | <callable default> |

### iot_readings

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | INTEGER | no | — |
| ingestion_id | VARCHAR(36) | no | — |
| processed_at | DATETIME | no | <callable default> |
| asset_id | VARCHAR(36) | no | — |
| asset_type | VARCHAR(50) | no | — |
| ward | VARCHAR(100) | yes | — |
| lat | FLOAT | no | — |
| lng | FLOAT | no | — |
| timestamp_utc | DATETIME | no | — |
| sensor_readings | TEXT | yes | {} |
| environmental_context | TEXT | yes | {} |
| health_score | INTEGER | no | 100 |
| status | VARCHAR(20) | no | OPTIMAL |
| is_anomaly | BOOLEAN | yes | False |
| anomaly_type | VARCHAR(100) | yes | — |
| severity | VARCHAR(20) | yes | LOW |
| confidence | FLOAT | yes | 0.5 |
| deviation_from_baseline | TEXT | yes | {} |
| predicted_failure_date | DATETIME | yes | — |
| remaining_useful_life_days | INTEGER | yes | 365 |
| failure_probability_7d | FLOAT | yes | 0.05 |
| failure_probability_30d | FLOAT | yes | 0.1 |
| primary_failure_mode | VARCHAR(100) | yes | — |
| secondary_failure_modes | TEXT | yes | [] |
| maintenance_triggered | BOOLEAN | yes | False |
| maintenance_priority | VARCHAR(10) | yes | P4 |
| recommended_action | VARCHAR(500) | yes | Monitor and recheck in 7 days. |
| estimated_downtime_hours | FLOAT | yes | 0.0 |
| spare_parts_required | TEXT | yes | [] |
| skill_level | VARCHAR(20) | yes | JUNIOR |
| blockchain_hash | VARCHAR(64) | no | — |

**Foreign keys:** asset_id -> iot_assets.id.

**Indexes:** ix_iot_readings_asset_id (asset_id; non-unique).

**Unique constraints:** unnamed (ingestion_id).

### issues

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | INTEGER | no | — |
| public_id | VARCHAR(16) | no | — |
| title | VARCHAR(500) | no | — |
| description | TEXT | no | — |
| category | VARCHAR(50) | no | — |
| lat | FLOAT | no | — |
| lon | FLOAT | no | — |
| location_landmarks | VARCHAR(500) | yes | — |
| priority_score | FLOAT | yes | 0 |
| priority_tier | VARCHAR(20) | yes | medium |
| ai_confidence | FLOAT | yes | 0 |
| status | VARCHAR(20) | yes | reported |
| fund_target | FLOAT | yes | 5000 |
| fund_collected | FLOAT | yes | 0 |
| media_files | TEXT | yes | [] |
| integrity_hash | VARCHAR(64) | yes | — |
| reporter_id | INTEGER | yes | — |
| reporter_phone | VARCHAR(20) | yes | — |
| created_at | DATETIME | yes | <callable default> |
| updated_at | DATETIME | yes | — |
| resolved_at | DATETIME | yes | — |

**Foreign keys:** reporter_id -> users.id.

**Unique constraints:** unnamed (public_id).

### offices

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | INTEGER | no | — |
| name | VARCHAR(200) | no | — |
| department | VARCHAR(100) | no | — |
| address | TEXT | no | — |
| lat | FLOAT | yes | — |
| lon | FLOAT | yes | — |
| officer_name | VARCHAR(100) | yes | — |
| phone | VARCHAR(50) | yes | — |
| timings | VARCHAR(100) | yes | — |
| services | TEXT | yes | — |
| rating | FLOAT | yes | — |

### official_sources

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | <callable default> |
| source_key | VARCHAR(120) | no | — |
| version | INTEGER | no | — |
| authority | VARCHAR(255) | no | — |
| title | VARCHAR(500) | no | — |
| source_type | VARCHAR(40) | no | — |
| jurisdiction | VARCHAR(120) | no | INDIA |
| canonical_url | VARCHAR(2048) | no | — |
| document_hash | VARCHAR(64) | yes | — |
| effective_from | DATETIME | yes | — |
| effective_until | DATETIME | yes | — |
| retrieved_at | DATETIME | no | <callable default> |
| verified_at | DATETIME | yes | — |
| verification_status | VARCHAR(32) | no | DRAFT |
| supersedes_id | VARCHAR(36) | yes | — |
| superseded_by_id | VARCHAR(36) | yes | — |
| reviewer | VARCHAR(255) | yes | — |
| parser_version | VARCHAR(80) | yes | — |

**Foreign keys:** superseded_by_id -> official_sources.id; supersedes_id -> official_sources.id.

**Indexes:** ix_official_sources_source_key (source_key; non-unique).

**Unique constraints:** uq_official_source_version (source_key, version).

**Check constraints:** ck_official_source_status: verification_status IN ('DRAFT', 'VERIFIED', 'SUPERSEDED', 'REVOKED'); ck_official_source_positive_version: version > 0; ck_official_source_https: canonical_url LIKE 'https://%'.

### resilience_hubs

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | — |
| lat | FLOAT | no | — |
| lng | FLOAT | no | — |
| address | VARCHAR(300) | yes | — |
| solar_generation_kw | FLOAT | yes | 0.0 |
| battery_soc_percent | FLOAT | yes | 100.0 |
| grid_connection | VARCHAR(20) | yes | CONNECTED |
| connected_loads | TEXT | yes | [] |
| occupancy | INTEGER | yes | 0 |
| supplies | TEXT | yes | {} |
| operational_mode | VARCHAR(20) | yes | NORMAL |
| updated_at | DATETIME | yes | <callable default> |
| created_at | DATETIME | yes | <callable default> |

### route_decisions

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | <callable default> |
| idempotency_key | VARCHAR(128) | yes | — |
| input_fingerprint | VARCHAR(64) | no | — |
| input_facts | JSON | no | — |
| route_rule_id | VARCHAR(36) | yes | — |
| route_rule_version | VARCHAR(160) | no | — |
| service_registry_version | VARCHAR(160) | no | — |
| source_versions | JSON | no | <callable default> |
| model_version | VARCHAR(80) | yes | — |
| output_authority_id | VARCHAR(36) | yes | — |
| outcome | VARCHAR(48) | no | — |
| explanation | TEXT | no | — |
| output | JSON | no | — |
| created_at | DATETIME | no | <callable default> |
| retention_until | DATETIME | no | — |

**Foreign keys:** output_authority_id -> authorities.id; route_rule_id -> route_rules.id.

**Indexes:** ix_route_decisions_created_at (created_at; non-unique); ix_route_decisions_input_fingerprint (input_fingerprint; non-unique).

**Unique constraints:** unnamed (idempotency_key).

### route_rules

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | <callable default> |
| rule_key | VARCHAR(120) | no | — |
| version | INTEGER | no | — |
| issue_type | VARCHAR(120) | no | — |
| match_terms | JSON | no | <callable default> |
| exclusion_terms | JSON | no | <callable default> |
| authority_id | VARCHAR(36) | no | — |
| service_version_id | VARCHAR(36) | no | — |
| source_ids | JSON | no | <callable default> |
| priority | INTEGER | no | 100 |
| effective_from | DATETIME | yes | — |
| effective_until | DATETIME | yes | — |
| status | VARCHAR(32) | no | UNVERIFIED |
| created_at | DATETIME | no | <callable default> |

**Foreign keys:** authority_id -> authorities.id; service_version_id -> government_services.id.

**Indexes:** ix_route_rules_rule_key (rule_key; non-unique).

**Unique constraints:** uq_route_rule_version (rule_key, version).

**Check constraints:** ck_route_rule_status: status IN ('ACTIVE', 'DEPRECATED', 'SUPERSEDED', 'UNVERIFIED'); ck_route_rule_positive_version: version > 0.

### srs_assets

| Column | Type | Null | Default |
|---|---|---:|---|
| asset_id (PK) | VARCHAR(40) | no | — |
| asset_type | VARCHAR(80) | no | — |
| ward | VARCHAR(100) | yes | — |
| lat | FLOAT | yes | — |
| lon | FLOAT | yes | — |
| age_years | FLOAT | yes | 0.0 |
| criticality | VARCHAR(20) | yes | MEDIUM |
| usage_index | FLOAT | yes | 50.0 |
| health_score | FLOAT | yes | 80.0 |
| predicted_failure_days | INTEGER | yes | 180 |
| degradation_rate | FLOAT | yes | 0.1 |
| last_sensor_score | FLOAT | yes | 80.0 |
| maintenance_status | VARCHAR(20) | yes | MONITOR |
| accessibility_compliant | BOOLEAN | yes | True |
| last_inspection_at | DATETIME | yes | — |
| created_at | DATETIME | yes | <callable default> |
| updated_at | DATETIME | yes | <callable default> |

**Indexes:** ix_srs_assets_health_score (health_score; non-unique); ix_srs_assets_predicted_failure_days (predicted_failure_days; non-unique).

### srs_audit_logs

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | INTEGER | no | — |
| event_type | VARCHAR(80) | no | — |
| actor_role | VARCHAR(50) | no | — |
| actor_id | VARCHAR(80) | yes | — |
| entity_type | VARCHAR(60) | no | — |
| entity_id | VARCHAR(80) | no | — |
| before_state | TEXT | yes | {} |
| after_state | TEXT | yes | {} |
| reason | VARCHAR(250) | yes | — |
| previous_hash | VARCHAR(64) | yes | — |
| immutable_hash | VARCHAR(64) | no | — |
| created_at | DATETIME | yes | <callable default> |

**Indexes:** ix_srs_audit_logs_created_at (created_at; non-unique); ix_srs_audit_logs_entity_id (entity_id; non-unique); ix_srs_audit_logs_entity_type (entity_type; non-unique); ix_srs_audit_logs_event_type (event_type; non-unique).

**Unique constraints:** unnamed (immutable_hash).

### srs_budget_events

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | INTEGER | no | — |
| work_order_id | VARCHAR(24) | no | — |
| category | VARCHAR(80) | no | — |
| planned_cost | FLOAT | no | — |
| actual_cost | FLOAT | no | — |
| variance_percent | FLOAT | no | — |
| anomaly_flag | BOOLEAN | yes | False |
| anomaly_reason | VARCHAR(200) | yes | — |
| created_at | DATETIME | yes | <callable default> |

**Indexes:** ix_srs_budget_events_anomaly_flag (anomaly_flag; non-unique); ix_srs_budget_events_created_at (created_at; non-unique); ix_srs_budget_events_work_order_id (work_order_id; non-unique).

### srs_contractors

| Column | Type | Null | Default |
|---|---|---:|---|
| contractor_id (PK) | VARCHAR(40) | no | — |
| name | VARCHAR(120) | no | — |
| specialization | VARCHAR(80) | no | general |
| availability_status | VARCHAR(20) | yes | AVAILABLE |
| capacity_per_day | INTEGER | yes | 8 |
| total_jobs | INTEGER | yes | 0 |
| sla_adherence_score | FLOAT | yes | 75.0 |
| repair_quality_score | FLOAT | yes | 75.0 |
| durability_score | FLOAT | yes | 75.0 |
| reliability_score | FLOAT | yes | 75.0 |
| fraud_flags | INTEGER | yes | 0 |
| blacklisted | BOOLEAN | yes | False |
| avg_resolution_hours | FLOAT | yes | 24.0 |
| created_at | DATETIME | yes | <callable default> |
| updated_at | DATETIME | yes | <callable default> |

### srs_issue_events

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | INTEGER | no | — |
| issue_public_id | VARCHAR(24) | no | — |
| from_status | VARCHAR(30) | yes | — |
| to_status | VARCHAR(30) | no | — |
| actor_role | VARCHAR(50) | no | — |
| actor_id | VARCHAR(80) | yes | — |
| notes | VARCHAR(500) | yes | — |
| metadata_json | TEXT | yes | {} |
| created_at | DATETIME | yes | <callable default> |

**Indexes:** ix_srs_issue_events_created_at (created_at; non-unique); ix_srs_issue_events_issue_public_id (issue_public_id; non-unique).

### srs_issues

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | INTEGER | no | — |
| public_id | VARCHAR(24) | no | — |
| source | VARCHAR(30) | no | citizen |
| title | VARCHAR(500) | no | — |
| description | TEXT | no | — |
| category | VARCHAR(60) | no | — |
| lat | FLOAT | yes | — |
| lon | FLOAT | yes | — |
| ward | VARCHAR(100) | yes | — |
| evidence_urls | TEXT | yes | [] |
| status | VARCHAR(30) | no | RECEIVED |
| severity | VARCHAR(20) | no | MEDIUM |
| risk_level | VARCHAR(20) | no | MEDIUM |
| priority_tier | VARCHAR(20) | no | MEDIUM |
| priority_score | FLOAT | no | 50.0 |
| explainability | TEXT | yes | [] |
| safety_impact | FLOAT | yes | 50.0 |
| usage_impact | FLOAT | yes | 50.0 |
| cost_impact | FLOAT | yes | 50.0 |
| duplicate_of_issue_id | VARCHAR(24) | yes | — |
| duplicate_score | FLOAT | yes | 0.0 |
| fraud_score | FLOAT | yes | 0.0 |
| is_malicious | BOOLEAN | yes | False |
| is_emergency | BOOLEAN | yes | False |
| emergency_reason | VARCHAR(200) | yes | — |
| escalated_at | DATETIME | yes | — |
| reporter_id | VARCHAR(80) | yes | — |
| reporter_reputation | FLOAT | yes | 0.5 |
| reporter_language | VARCHAR(12) | yes | en |
| citizen_feedback_rating | INTEGER | yes | — |
| citizen_feedback_comment | TEXT | yes | — |
| citizen_confirmed | BOOLEAN | yes | — |
| work_order_id | VARCHAR(24) | yes | — |
| assigned_contractor_id | VARCHAR(40) | yes | — |
| assigned_team | VARCHAR(100) | yes | — |
| sla_deadline | DATETIME | yes | — |
| accessibility_flag | BOOLEAN | yes | False |
| accessibility_barrier_type | VARCHAR(80) | yes | — |
| captured_offline | BOOLEAN | yes | False |
| captured_at | DATETIME | yes | <callable default> |
| synced_at | DATETIME | yes | — |
| created_at | DATETIME | yes | <callable default> |
| updated_at | DATETIME | yes | <callable default> |
| resolved_at | DATETIME | yes | — |
| closed_at | DATETIME | yes | — |

**Indexes:** ix_srs_issues_is_emergency (is_emergency; non-unique); ix_srs_issues_public_id (public_id; unique); ix_srs_issues_status (status; non-unique).

### srs_utility_map

| Column | Type | Null | Default |
|---|---|---:|---|
| utility_id (PK) | VARCHAR(40) | no | — |
| utility_type | VARCHAR(40) | no | — |
| ward | VARCHAR(100) | yes | — |
| geometry_json | TEXT | yes | [] |
| depth_m | FLOAT | yes | 1.5 |
| active | BOOLEAN | yes | True |
| created_at | DATETIME | yes | <callable default> |
| updated_at | DATETIME | yes | <callable default> |

### srs_work_orders

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | INTEGER | no | — |
| work_order_id | VARCHAR(24) | no | — |
| issue_public_id | VARCHAR(24) | no | — |
| status | VARCHAR(30) | no | CREATED |
| assignee_type | VARCHAR(20) | no | CONTRACTOR |
| contractor_id | VARCHAR(40) | yes | — |
| assigned_team | VARCHAR(100) | yes | — |
| sla_hours | INTEGER | yes | 24 |
| due_at | DATETIME | yes | — |
| started_at | DATETIME | yes | — |
| completed_at | DATETIME | yes | — |
| estimated_cost | FLOAT | yes | 0.0 |
| actual_cost | FLOAT | yes | 0.0 |
| warranty_days | INTEGER | yes | 90 |
| warranty_expiry | DATETIME | yes | — |
| ai_quality_score | FLOAT | yes | — |
| sensor_health_delta | FLOAT | yes | — |
| quality_score | FLOAT | yes | — |
| inspector_validated | BOOLEAN | yes | False |
| citizen_validated | BOOLEAN | yes | False |
| repeat_failure_count | INTEGER | yes | 0 |
| payment_status | VARCHAR(20) | yes | HOLD |
| created_at | DATETIME | yes | <callable default> |
| updated_at | DATETIME | yes | <callable default> |

**Indexes:** ix_srs_work_orders_contractor_id (contractor_id; non-unique); ix_srs_work_orders_issue_public_id (issue_public_id; non-unique); ix_srs_work_orders_status (status; non-unique); ix_srs_work_orders_work_order_id (work_order_id; unique).

### staff_audit_events

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | <callable default> |
| tenant_id | VARCHAR(36) | no | — |
| actor_id | VARCHAR(36) | yes | — |
| action | VARCHAR(64) | no | — |
| object_type | VARCHAR(48) | no | — |
| object_id | VARCHAR(64) | no | — |
| request_id | VARCHAR(64) | no | — |
| created_at | DATETIME | no | <callable default> |

**Foreign keys:** actor_id -> staff_users.id; tenant_id -> tenants.id.

**Indexes:** ix_staff_audit_events_tenant_id (tenant_id; non-unique).

### staff_case_events

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | <callable default> |
| tenant_id | VARCHAR(36) | no | — |
| case_id | VARCHAR(36) | no | — |
| actor_id | VARCHAR(36) | no | — |
| event_type | VARCHAR(40) | no | — |
| from_status | VARCHAR(32) | yes | — |
| to_status | VARCHAR(32) | yes | — |
| metadata_json | JSON | no | <callable default> |
| created_at | DATETIME | no | <callable default> |

**Foreign keys:** tenant_id -> staff_users.tenant_id, actor_id -> staff_users.id; tenant_id -> staff_cases.tenant_id, case_id -> staff_cases.id; tenant_id -> tenants.id.

**Indexes:** ix_staff_case_events_case_id (case_id; non-unique); ix_staff_case_events_tenant_id (tenant_id; non-unique).

### staff_cases

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | <callable default> |
| tenant_id | VARCHAR(36) | no | — |
| case_ref | VARCHAR(24) | no | — |
| case_type | VARCHAR(64) | no | — |
| title | VARCHAR(160) | no | — |
| status | VARCHAR(32) | no | OPEN |
| priority | VARCHAR(16) | no | NORMAL |
| assigned_user_id | VARCHAR(36) | yes | — |
| created_by | VARCHAR(36) | no | — |
| created_at | DATETIME | no | <callable default> |
| updated_at | DATETIME | no | <callable default> |

**Foreign keys:** tenant_id -> tenants.id; tenant_id -> staff_users.tenant_id, created_by -> staff_users.id; assigned_user_id -> staff_users.id.

**Indexes:** ix_staff_cases_assigned_user_id (assigned_user_id; non-unique); ix_staff_cases_created_by (created_by; non-unique); ix_staff_cases_tenant_id (tenant_id; non-unique).

**Unique constraints:** uq_staff_case_tenant_ref (tenant_id, case_ref); uq_staff_case_tenant_id (tenant_id, id).

**Check constraints:** ck_staff_case_status: status IN ('OPEN', 'UNDER_REVIEW', 'ACTION_REQUIRED', 'RESOLVED', 'CLOSED'); ck_staff_case_priority: priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT').

### staff_mfa_challenges

| Column | Type | Null | Default |
|---|---|---:|---|
| token_hash (PK) | VARCHAR(64) | no | — |
| tenant_id | VARCHAR(36) | no | — |
| user_id | VARCHAR(36) | no | — |
| expires_at | DATETIME | no | — |
| consumed_at | DATETIME | yes | — |
| created_at | DATETIME | no | <callable default> |

**Foreign keys:** tenant_id -> tenants.id; tenant_id -> staff_users.tenant_id, user_id -> staff_users.id.

**Indexes:** ix_staff_mfa_challenges_tenant_id (tenant_id; non-unique).

### staff_mfa_factors

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | <callable default> |
| tenant_id | VARCHAR(36) | no | — |
| user_id | VARCHAR(36) | no | — |
| secret_ciphertext | TEXT | no | — |
| active | BOOLEAN | no | False |
| enrollment_token_hash | VARCHAR(64) | yes | — |
| enrollment_expires_at | DATETIME | yes | — |
| last_totp_step | BIGINT | no | -1 |
| failed_attempts | INTEGER | no | 0 |
| locked_until | DATETIME | yes | — |
| created_at | DATETIME | no | <callable default> |
| activated_at | DATETIME | yes | — |

**Foreign keys:** tenant_id -> tenants.id; tenant_id -> staff_users.tenant_id, user_id -> staff_users.id.

**Indexes:** ix_staff_mfa_factors_tenant_id (tenant_id; non-unique).

**Unique constraints:** unnamed (user_id).

**Check constraints:** ck_staff_mfa_failed_attempts: failed_attempts >= 0.

### staff_role_grants

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | <callable default> |
| tenant_id | VARCHAR(36) | no | — |
| user_id | VARCHAR(36) | no | — |
| role | VARCHAR(32) | no | — |
| granted_by | VARCHAR(36) | yes | — |
| created_at | DATETIME | no | <callable default> |

**Foreign keys:** tenant_id -> staff_users.tenant_id, user_id -> staff_users.id; granted_by -> staff_users.id; tenant_id -> tenants.id.

**Indexes:** ix_staff_role_grants_tenant_id (tenant_id; non-unique); ix_staff_role_grants_user_id (user_id; non-unique).

**Unique constraints:** uq_staff_role_grant (tenant_id, user_id, role).

**Check constraints:** ck_staff_role_name: role IN ('TENANT_ADMIN', 'CASE_OFFICER', 'SOURCE_REVIEWER', 'AUDITOR').

### staff_sessions

| Column | Type | Null | Default |
|---|---|---:|---|
| session_hash (PK) | VARCHAR(64) | no | — |
| tenant_id | VARCHAR(36) | no | — |
| user_id | VARCHAR(36) | no | — |
| csrf_hash | VARCHAR(64) | no | — |
| mfa_verified_at | DATETIME | no | — |
| created_at | DATETIME | no | <callable default> |
| last_seen_at | DATETIME | no | <callable default> |
| idle_expires_at | DATETIME | no | — |
| absolute_expires_at | DATETIME | no | — |
| revoked_at | DATETIME | yes | — |

**Foreign keys:** tenant_id -> staff_users.tenant_id, user_id -> staff_users.id; tenant_id -> tenants.id.

**Indexes:** ix_staff_sessions_tenant_id (tenant_id; non-unique); ix_staff_sessions_user_id (user_id; non-unique).

### staff_users

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | <callable default> |
| tenant_id | VARCHAR(36) | no | — |
| email | VARCHAR(254) | no | — |
| display_name | VARCHAR(160) | no | — |
| password_hash | VARCHAR(512) | no | — |
| active | BOOLEAN | no | True |
| failed_login_count | INTEGER | no | 0 |
| locked_until | DATETIME | yes | — |
| created_at | DATETIME | no | <callable default> |
| password_changed_at | DATETIME | no | <callable default> |

**Foreign keys:** tenant_id -> tenants.id.

**Indexes:** ix_staff_users_tenant_id (tenant_id; non-unique).

**Unique constraints:** uq_staff_user_tenant_id (tenant_id, id); uq_staff_user_tenant_email (tenant_id, email).

**Check constraints:** ck_staff_failed_login_count: failed_login_count >= 0.

### tenants

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | VARCHAR(36) | no | <callable default> |
| slug | VARCHAR(80) | no | — |
| display_name | VARCHAR(160) | no | — |
| active | BOOLEAN | no | True |
| created_at | DATETIME | no | <callable default> |

**Unique constraints:** unnamed (slug).

### user_gamification

| Column | Type | Null | Default |
|---|---|---:|---|
| user_id (PK) | INTEGER | no | — |
| civic_score | INTEGER | yes | 0 |
| rank | VARCHAR(50) | yes | New Citizen |
| streak_weeks | INTEGER | yes | 0 |
| badges | TEXT | yes | [] |
| last_updated | DATETIME | yes | <callable default> |

**Foreign keys:** user_id -> users.id.

### users

| Column | Type | Null | Default |
|---|---|---:|---|
| id (PK) | INTEGER | no | — |
| public_id | VARCHAR(16) | no | — |
| phone | VARCHAR(20) | no | — |
| email | VARCHAR(120) | yes | — |
| name | VARCHAR(100) | yes | — |
| state | VARCHAR(50) | yes | — |
| district | VARCHAR(50) | yes | — |
| pincode | VARCHAR(10) | yes | — |
| preferred_language | VARCHAR(10) | yes | en |
| phone_verified | BOOLEAN | yes | False |
| password_hash | VARCHAR(256) | yes | — |
| is_active | BOOLEAN | yes | True |
| created_at | DATETIME | yes | <callable default> |
| last_login | DATETIME | yes | — |

**Unique constraints:** unnamed (public_id); unnamed (phone); unnamed (email).
