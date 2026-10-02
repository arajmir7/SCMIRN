"""Complete baseline for legacy ORM tables.

Revision ID: 20261002_01
Revises: 20261001_01

Creates every canonical legacy ORM table omitted by the source-routing-only
revision. Existing matching tables are preserved for safe adoption of a schema
previously provisioned by the development ORM. The migration environment checks
existing table structure before this revision is allowed to run.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261002_01"
down_revision = "20261001_01"
branch_labels = None
depends_on = None


def _has_table(name):
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade():
    if not _has_table('blockchain_tx'):
        op.create_table('blockchain_tx',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tx_hash', sa.String(length=66), nullable=False),
        sa.Column('block_number', sa.Integer(), nullable=True),
        sa.Column('contract_address', sa.String(length=42), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('payload_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tx_hash')
        )
        # ### end Alembic commands ###

    if not _has_table('chat_logs'):
        op.create_table('chat_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=50), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('intent', sa.String(length=50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        # ### end Alembic commands ###

    if not _has_table('iot_assets'):
        op.create_table('iot_assets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('ward', sa.String(length=100), nullable=True),
        sa.Column('health_score', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('predictive_maintenance_due', sa.DateTime(), nullable=True),
        sa.Column('last_reading', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        # ### end Alembic commands ###

    if not _has_table('offices'):
        op.create_table('offices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('officer_name', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('timings', sa.String(length=100), nullable=True),
        sa.Column('services', sa.Text(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        # ### end Alembic commands ###

    if not _has_table('resilience_hubs'):
        op.create_table('resilience_hubs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('address', sa.String(length=300), nullable=True),
        sa.Column('solar_generation_kw', sa.Float(), nullable=True),
        sa.Column('battery_soc_percent', sa.Float(), nullable=True),
        sa.Column('grid_connection', sa.String(length=20), nullable=True),
        sa.Column('connected_loads', sa.Text(), nullable=True),
        sa.Column('occupancy', sa.Integer(), nullable=True),
        sa.Column('supplies', sa.Text(), nullable=True),
        sa.Column('operational_mode', sa.String(length=20), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        # ### end Alembic commands ###

    if not _has_table('srs_assets'):
        op.create_table('srs_assets',
        sa.Column('asset_id', sa.String(length=40), nullable=False),
        sa.Column('asset_type', sa.String(length=80), nullable=False),
        sa.Column('ward', sa.String(length=100), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('age_years', sa.Float(), nullable=True),
        sa.Column('criticality', sa.String(length=20), nullable=True),
        sa.Column('usage_index', sa.Float(), nullable=True),
        sa.Column('health_score', sa.Float(), nullable=True),
        sa.Column('predicted_failure_days', sa.Integer(), nullable=True),
        sa.Column('degradation_rate', sa.Float(), nullable=True),
        sa.Column('last_sensor_score', sa.Float(), nullable=True),
        sa.Column('maintenance_status', sa.String(length=20), nullable=True),
        sa.Column('accessibility_compliant', sa.Boolean(), nullable=True),
        sa.Column('last_inspection_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('asset_id')
        )
        op.create_index(op.f('ix_srs_assets_health_score'), 'srs_assets', ['health_score'], unique=False)
        op.create_index(op.f('ix_srs_assets_predicted_failure_days'), 'srs_assets', ['predicted_failure_days'], unique=False)
        # ### end Alembic commands ###

    if not _has_table('srs_audit_logs'):
        op.create_table('srs_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=80), nullable=False),
        sa.Column('actor_role', sa.String(length=50), nullable=False),
        sa.Column('actor_id', sa.String(length=80), nullable=True),
        sa.Column('entity_type', sa.String(length=60), nullable=False),
        sa.Column('entity_id', sa.String(length=80), nullable=False),
        sa.Column('before_state', sa.Text(), nullable=True),
        sa.Column('after_state', sa.Text(), nullable=True),
        sa.Column('reason', sa.String(length=250), nullable=True),
        sa.Column('previous_hash', sa.String(length=64), nullable=True),
        sa.Column('immutable_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('immutable_hash')
        )
        op.create_index(op.f('ix_srs_audit_logs_created_at'), 'srs_audit_logs', ['created_at'], unique=False)
        op.create_index(op.f('ix_srs_audit_logs_entity_id'), 'srs_audit_logs', ['entity_id'], unique=False)
        op.create_index(op.f('ix_srs_audit_logs_entity_type'), 'srs_audit_logs', ['entity_type'], unique=False)
        op.create_index(op.f('ix_srs_audit_logs_event_type'), 'srs_audit_logs', ['event_type'], unique=False)
        # ### end Alembic commands ###

    if not _has_table('srs_budget_events'):
        op.create_table('srs_budget_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('work_order_id', sa.String(length=24), nullable=False),
        sa.Column('category', sa.String(length=80), nullable=False),
        sa.Column('planned_cost', sa.Float(), nullable=False),
        sa.Column('actual_cost', sa.Float(), nullable=False),
        sa.Column('variance_percent', sa.Float(), nullable=False),
        sa.Column('anomaly_flag', sa.Boolean(), nullable=True),
        sa.Column('anomaly_reason', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_srs_budget_events_anomaly_flag'), 'srs_budget_events', ['anomaly_flag'], unique=False)
        op.create_index(op.f('ix_srs_budget_events_created_at'), 'srs_budget_events', ['created_at'], unique=False)
        op.create_index(op.f('ix_srs_budget_events_work_order_id'), 'srs_budget_events', ['work_order_id'], unique=False)
        # ### end Alembic commands ###

    if not _has_table('srs_contractors'):
        op.create_table('srs_contractors',
        sa.Column('contractor_id', sa.String(length=40), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('specialization', sa.String(length=80), nullable=False),
        sa.Column('availability_status', sa.String(length=20), nullable=True),
        sa.Column('capacity_per_day', sa.Integer(), nullable=True),
        sa.Column('total_jobs', sa.Integer(), nullable=True),
        sa.Column('sla_adherence_score', sa.Float(), nullable=True),
        sa.Column('repair_quality_score', sa.Float(), nullable=True),
        sa.Column('durability_score', sa.Float(), nullable=True),
        sa.Column('reliability_score', sa.Float(), nullable=True),
        sa.Column('fraud_flags', sa.Integer(), nullable=True),
        sa.Column('blacklisted', sa.Boolean(), nullable=True),
        sa.Column('avg_resolution_hours', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('contractor_id')
        )
        # ### end Alembic commands ###

    if not _has_table('srs_issue_events'):
        op.create_table('srs_issue_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('issue_public_id', sa.String(length=24), nullable=False),
        sa.Column('from_status', sa.String(length=30), nullable=True),
        sa.Column('to_status', sa.String(length=30), nullable=False),
        sa.Column('actor_role', sa.String(length=50), nullable=False),
        sa.Column('actor_id', sa.String(length=80), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_srs_issue_events_created_at'), 'srs_issue_events', ['created_at'], unique=False)
        op.create_index(op.f('ix_srs_issue_events_issue_public_id'), 'srs_issue_events', ['issue_public_id'], unique=False)
        # ### end Alembic commands ###

    if not _has_table('srs_issues'):
        op.create_table('srs_issues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.String(length=24), nullable=False),
        sa.Column('source', sa.String(length=30), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=60), nullable=False),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('ward', sa.String(length=100), nullable=True),
        sa.Column('evidence_urls', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('priority_tier', sa.String(length=20), nullable=False),
        sa.Column('priority_score', sa.Float(), nullable=False),
        sa.Column('explainability', sa.Text(), nullable=True),
        sa.Column('safety_impact', sa.Float(), nullable=True),
        sa.Column('usage_impact', sa.Float(), nullable=True),
        sa.Column('cost_impact', sa.Float(), nullable=True),
        sa.Column('duplicate_of_issue_id', sa.String(length=24), nullable=True),
        sa.Column('duplicate_score', sa.Float(), nullable=True),
        sa.Column('fraud_score', sa.Float(), nullable=True),
        sa.Column('is_malicious', sa.Boolean(), nullable=True),
        sa.Column('is_emergency', sa.Boolean(), nullable=True),
        sa.Column('emergency_reason', sa.String(length=200), nullable=True),
        sa.Column('escalated_at', sa.DateTime(), nullable=True),
        sa.Column('reporter_id', sa.String(length=80), nullable=True),
        sa.Column('reporter_reputation', sa.Float(), nullable=True),
        sa.Column('reporter_language', sa.String(length=12), nullable=True),
        sa.Column('citizen_feedback_rating', sa.Integer(), nullable=True),
        sa.Column('citizen_feedback_comment', sa.Text(), nullable=True),
        sa.Column('citizen_confirmed', sa.Boolean(), nullable=True),
        sa.Column('work_order_id', sa.String(length=24), nullable=True),
        sa.Column('assigned_contractor_id', sa.String(length=40), nullable=True),
        sa.Column('assigned_team', sa.String(length=100), nullable=True),
        sa.Column('sla_deadline', sa.DateTime(), nullable=True),
        sa.Column('accessibility_flag', sa.Boolean(), nullable=True),
        sa.Column('accessibility_barrier_type', sa.String(length=80), nullable=True),
        sa.Column('captured_offline', sa.Boolean(), nullable=True),
        sa.Column('captured_at', sa.DateTime(), nullable=True),
        sa.Column('synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_srs_issues_is_emergency'), 'srs_issues', ['is_emergency'], unique=False)
        op.create_index(op.f('ix_srs_issues_public_id'), 'srs_issues', ['public_id'], unique=True)
        op.create_index(op.f('ix_srs_issues_status'), 'srs_issues', ['status'], unique=False)
        # ### end Alembic commands ###

    if not _has_table('srs_utility_map'):
        op.create_table('srs_utility_map',
        sa.Column('utility_id', sa.String(length=40), nullable=False),
        sa.Column('utility_type', sa.String(length=40), nullable=False),
        sa.Column('ward', sa.String(length=100), nullable=True),
        sa.Column('geometry_json', sa.Text(), nullable=True),
        sa.Column('depth_m', sa.Float(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('utility_id')
        )
        # ### end Alembic commands ###

    if not _has_table('srs_work_orders'):
        op.create_table('srs_work_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('work_order_id', sa.String(length=24), nullable=False),
        sa.Column('issue_public_id', sa.String(length=24), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('assignee_type', sa.String(length=20), nullable=False),
        sa.Column('contractor_id', sa.String(length=40), nullable=True),
        sa.Column('assigned_team', sa.String(length=100), nullable=True),
        sa.Column('sla_hours', sa.Integer(), nullable=True),
        sa.Column('due_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('actual_cost', sa.Float(), nullable=True),
        sa.Column('warranty_days', sa.Integer(), nullable=True),
        sa.Column('warranty_expiry', sa.DateTime(), nullable=True),
        sa.Column('ai_quality_score', sa.Float(), nullable=True),
        sa.Column('sensor_health_delta', sa.Float(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('inspector_validated', sa.Boolean(), nullable=True),
        sa.Column('citizen_validated', sa.Boolean(), nullable=True),
        sa.Column('repeat_failure_count', sa.Integer(), nullable=True),
        sa.Column('payment_status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_srs_work_orders_contractor_id'), 'srs_work_orders', ['contractor_id'], unique=False)
        op.create_index(op.f('ix_srs_work_orders_issue_public_id'), 'srs_work_orders', ['issue_public_id'], unique=False)
        op.create_index(op.f('ix_srs_work_orders_status'), 'srs_work_orders', ['status'], unique=False)
        op.create_index(op.f('ix_srs_work_orders_work_order_id'), 'srs_work_orders', ['work_order_id'], unique=True)
        # ### end Alembic commands ###

    if not _has_table('users'):
        op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.String(length=16), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=True),
        sa.Column('district', sa.String(length=50), nullable=True),
        sa.Column('pincode', sa.String(length=10), nullable=True),
        sa.Column('preferred_language', sa.String(length=10), nullable=True),
        sa.Column('phone_verified', sa.Boolean(), nullable=True),
        sa.Column('password_hash', sa.String(length=256), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('phone'),
        sa.UniqueConstraint('public_id')
        )
        # ### end Alembic commands ###

    if not _has_table('documents'):
        op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.String(length=16), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('doc_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('template_data', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('jurisdiction', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.Column('downloaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id')
        )
        # ### end Alembic commands ###

    if not _has_table('iot_readings'):
        op.create_table('iot_readings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ingestion_id', sa.String(length=36), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=False),
        sa.Column('asset_id', sa.String(length=36), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=False),
        sa.Column('ward', sa.String(length=100), nullable=True),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('timestamp_utc', sa.DateTime(), nullable=False),
        sa.Column('sensor_readings', sa.Text(), nullable=True),
        sa.Column('environmental_context', sa.Text(), nullable=True),
        sa.Column('health_score', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_anomaly', sa.Boolean(), nullable=True),
        sa.Column('anomaly_type', sa.String(length=100), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('deviation_from_baseline', sa.Text(), nullable=True),
        sa.Column('predicted_failure_date', sa.DateTime(), nullable=True),
        sa.Column('remaining_useful_life_days', sa.Integer(), nullable=True),
        sa.Column('failure_probability_7d', sa.Float(), nullable=True),
        sa.Column('failure_probability_30d', sa.Float(), nullable=True),
        sa.Column('primary_failure_mode', sa.String(length=100), nullable=True),
        sa.Column('secondary_failure_modes', sa.Text(), nullable=True),
        sa.Column('maintenance_triggered', sa.Boolean(), nullable=True),
        sa.Column('maintenance_priority', sa.String(length=10), nullable=True),
        sa.Column('recommended_action', sa.String(length=500), nullable=True),
        sa.Column('estimated_downtime_hours', sa.Float(), nullable=True),
        sa.Column('spare_parts_required', sa.Text(), nullable=True),
        sa.Column('skill_level', sa.String(length=20), nullable=True),
        sa.Column('blockchain_hash', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['iot_assets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ingestion_id')
        )
        op.create_index(op.f('ix_iot_readings_asset_id'), 'iot_readings', ['asset_id'], unique=False)
        # ### end Alembic commands ###

    if not _has_table('issues'):
        op.create_table('issues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.String(length=16), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lon', sa.Float(), nullable=False),
        sa.Column('location_landmarks', sa.String(length=500), nullable=True),
        sa.Column('priority_score', sa.Float(), nullable=True),
        sa.Column('priority_tier', sa.String(length=20), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('fund_target', sa.Float(), nullable=True),
        sa.Column('fund_collected', sa.Float(), nullable=True),
        sa.Column('media_files', sa.Text(), nullable=True),
        sa.Column('integrity_hash', sa.String(length=64), nullable=True),
        sa.Column('reporter_id', sa.Integer(), nullable=True),
        sa.Column('reporter_phone', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id')
        )
        # ### end Alembic commands ###

    if not _has_table('user_gamification'):
        op.create_table('user_gamification',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('civic_score', sa.Integer(), nullable=True),
        sa.Column('rank', sa.String(length=50), nullable=True),
        sa.Column('streak_weeks', sa.Integer(), nullable=True),
        sa.Column('badges', sa.Text(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id')
        )
        # ### end Alembic commands ###


def downgrade():
    raise RuntimeError(
        "Refusing to drop canonical application tables. Restore an approved "
        "backup or write a reviewed forward migration instead."
    )
