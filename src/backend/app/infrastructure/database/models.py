"""
SQLAlchemy ORM models.
These are database-specific implementations, not domain entities.
"""

from datetime import datetime
import json

from app.extensions import db


class IssueORM(db.Model):
    """Database model for civic issues."""
    
    __tablename__ = 'issues'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(16), unique=True, nullable=False)
    
    # Content
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    
    # Location
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    location_landmarks = db.Column(db.String(500))
    
    # Priority (AI-calculated)
    priority_score = db.Column(db.Float, default=0)
    priority_tier = db.Column(db.String(20), default='medium')
    ai_confidence = db.Column(db.Float, default=0)
    
    # Status
    status = db.Column(db.String(20), default='reported')
    
    # Funding
    fund_target = db.Column(db.Float, default=5000)
    fund_collected = db.Column(db.Float, default=0)
    
    # Media
    media_files = db.Column(db.Text, default='[]')  # JSON array
    
    # Security
    integrity_hash = db.Column(db.String(64))
    
    # Reporter (optional for anonymous)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reporter_phone = db.Column(db.String(20))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    def to_entity(self):
        """Convert ORM to domain entity."""
        from app.core.entities.issue import Issue, Location, MediaFile, IssueStatus, PriorityTier
        import json
        
        location = Location(latitude=self.lat, longitude=self.lon) if self.lat and self.lon else None
        
        # Parse media files
        media_urls = json.loads(self.media_files) if self.media_files else []
        media_files = [MediaFile(url=url, file_type='image') for url in media_urls]
        
        return Issue(
            id=self.id,
            public_id=self.public_id,
            title=self.title,
            description=self.description,
            category=self.category,
            location=location,
            priority_score=self.priority_score,
            priority_tier=PriorityTier(self.priority_tier),
            status=IssueStatus(self.status),
            fund_target=self.fund_target,
            fund_collected=self.fund_collected,
            media_files=media_files,
            integrity_hash=self.integrity_hash,
            created_at=self.created_at,
            ai_confidence=self.ai_confidence,
            reporter_id=self.reporter_id
        )


class UserORM(db.Model):
    """Database model for users."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(16), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    name = db.Column(db.String(100))
    state = db.Column(db.String(50))
    district = db.Column(db.String(50))
    pincode = db.Column(db.String(10))
    preferred_language = db.Column(db.String(10), default='en')
    phone_verified = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)


class DocumentORM(db.Model):
    """Database model for generated documents."""
    
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(16), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    doc_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='draft')
    title = db.Column(db.String(200))
    template_data = db.Column(db.Text)  # JSON
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    jurisdiction = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    generated_at = db.Column(db.DateTime)
    downloaded_at = db.Column(db.DateTime)


class OfficeORM(db.Model):
    """Database model for government offices."""
    
    __tablename__ = 'offices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    officer_name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    timings = db.Column(db.String(100))
    services = db.Column(db.Text)
    rating = db.Column(db.Float)


class ChatLogORM(db.Model):
    """Database model for AI chat logs."""
    
    __tablename__ = 'chat_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50))
    message = db.Column(db.Text)
    response = db.Column(db.Text)
    intent = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# ============================
# IoT Predictive Maintenance
# ============================

class IoTAssetORM(db.Model):
    """Database model for an IoT-connected civic asset."""

    __tablename__ = 'iot_assets'

    # Use UUID strings so external systems can supply stable IDs
    id = db.Column(db.String(36), primary_key=True)
    asset_type = db.Column(db.String(50), nullable=False)

    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    ward = db.Column(db.String(100), nullable=True)

    # Current state snapshot
    health_score = db.Column(db.Integer, default=100)
    status = db.Column(db.String(20), default='OPTIMAL')
    predictive_maintenance_due = db.Column(db.DateTime, nullable=True)

    last_reading = db.Column(db.Text, default='{}')  # JSON
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_last_reading(self, payload: dict) -> None:
        self.last_reading = json.dumps(payload, ensure_ascii=False)


class IoTReadingORM(db.Model):
    """Database model for an ingested IoT reading + computed analytics."""

    __tablename__ = 'iot_readings'

    id = db.Column(db.Integer, primary_key=True)
    ingestion_id = db.Column(db.String(36), unique=True, nullable=False)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    asset_id = db.Column(db.String(36), db.ForeignKey('iot_assets.id'), nullable=False, index=True)
    asset_type = db.Column(db.String(50), nullable=False)
    ward = db.Column(db.String(100), nullable=True)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)

    timestamp_utc = db.Column(db.DateTime, nullable=False)
    sensor_readings = db.Column(db.Text, default='{}')  # JSON
    environmental_context = db.Column(db.Text, default='{}')  # JSON

    # Computed outputs
    health_score = db.Column(db.Integer, nullable=False, default=100)
    status = db.Column(db.String(20), nullable=False, default='OPTIMAL')

    is_anomaly = db.Column(db.Boolean, default=False)
    anomaly_type = db.Column(db.String(100), nullable=True)
    severity = db.Column(db.String(20), default='LOW')
    confidence = db.Column(db.Float, default=0.5)
    deviation_from_baseline = db.Column(db.Text, default='{}')  # JSON

    predicted_failure_date = db.Column(db.DateTime, nullable=True)
    remaining_useful_life_days = db.Column(db.Integer, default=365)
    failure_probability_7d = db.Column(db.Float, default=0.05)
    failure_probability_30d = db.Column(db.Float, default=0.10)
    primary_failure_mode = db.Column(db.String(100), nullable=True)
    secondary_failure_modes = db.Column(db.Text, default='[]')  # JSON array

    maintenance_triggered = db.Column(db.Boolean, default=False)
    maintenance_priority = db.Column(db.String(10), default='P4')
    recommended_action = db.Column(db.String(500), default='Monitor and recheck in 7 days.')
    estimated_downtime_hours = db.Column(db.Float, default=0.0)
    spare_parts_required = db.Column(db.Text, default='[]')  # JSON array
    skill_level = db.Column(db.String(20), default='JUNIOR')

    blockchain_hash = db.Column(db.String(64), nullable=False)


# ============================
# Blockchain Transparency Layer
# ============================

class BlockchainTransactionORM(db.Model):
    """Database model for a simulated blockchain transaction/audit record."""

    __tablename__ = 'blockchain_tx'

    id = db.Column(db.Integer, primary_key=True)
    tx_hash = db.Column(db.String(66), unique=True, nullable=False)  # e.g. 0x + 64 hex OR sha256 hex
    block_number = db.Column(db.Integer, nullable=True)
    contract_address = db.Column(db.String(42), nullable=True)
    status = db.Column(db.String(20), default='CONFIRMED')
    payload_hash = db.Column(db.String(64), nullable=False)  # sha256 of canonical payload
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================
# Gamified Civic Engagement
# ============================

class UserGamificationORM(db.Model):
    """Database model for user gamification state."""

    __tablename__ = 'user_gamification'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    civic_score = db.Column(db.Integer, default=0)
    rank = db.Column(db.String(50), default='New Citizen')
    streak_weeks = db.Column(db.Integer, default=0)
    badges = db.Column(db.Text, default='[]')  # JSON array
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================
# Resilience Hub Network
# ============================

class ResilienceHubORM(db.Model):
    """Database model for a resilience hub / micro-grid node."""

    __tablename__ = 'resilience_hubs'

    id = db.Column(db.String(36), primary_key=True)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(300), nullable=True)

    solar_generation_kw = db.Column(db.Float, default=0.0)
    battery_soc_percent = db.Column(db.Float, default=100.0)
    grid_connection = db.Column(db.String(20), default='CONNECTED')
    connected_loads = db.Column(db.Text, default='[]')  # JSON array
    occupancy = db.Column(db.Integer, default=0)
    supplies = db.Column(db.Text, default='{}')  # JSON object
    operational_mode = db.Column(db.String(20), default='NORMAL')

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================
# SCMIRN SRS Runtime Models
# ============================

class SRSIssueORM(db.Model):
    """Production-focused issue model mapped to SRS FR-01..FR-07."""

    __tablename__ = 'srs_issues'

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(24), unique=True, nullable=False, index=True)

    source = db.Column(db.String(30), nullable=False, default='citizen')
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(60), nullable=False)

    lat = db.Column(db.Float, nullable=True)
    lon = db.Column(db.Float, nullable=True)
    ward = db.Column(db.String(100), nullable=True)

    evidence_urls = db.Column(db.Text, default='[]')  # JSON array

    status = db.Column(db.String(30), nullable=False, default='RECEIVED', index=True)
    severity = db.Column(db.String(20), nullable=False, default='MEDIUM')
    risk_level = db.Column(db.String(20), nullable=False, default='MEDIUM')
    priority_tier = db.Column(db.String(20), nullable=False, default='MEDIUM')
    priority_score = db.Column(db.Float, nullable=False, default=50.0)
    explainability = db.Column(db.Text, default='[]')  # JSON array

    safety_impact = db.Column(db.Float, default=50.0)
    usage_impact = db.Column(db.Float, default=50.0)
    cost_impact = db.Column(db.Float, default=50.0)

    duplicate_of_issue_id = db.Column(db.String(24), nullable=True)
    duplicate_score = db.Column(db.Float, default=0.0)
    fraud_score = db.Column(db.Float, default=0.0)
    is_malicious = db.Column(db.Boolean, default=False)

    is_emergency = db.Column(db.Boolean, default=False, index=True)
    emergency_reason = db.Column(db.String(200), nullable=True)
    escalated_at = db.Column(db.DateTime, nullable=True)

    reporter_id = db.Column(db.String(80), nullable=True)
    reporter_reputation = db.Column(db.Float, default=0.5)
    reporter_language = db.Column(db.String(12), default='en')

    citizen_feedback_rating = db.Column(db.Integer, nullable=True)
    citizen_feedback_comment = db.Column(db.Text, nullable=True)
    citizen_confirmed = db.Column(db.Boolean, nullable=True)

    work_order_id = db.Column(db.String(24), nullable=True)
    assigned_contractor_id = db.Column(db.String(40), nullable=True)
    assigned_team = db.Column(db.String(100), nullable=True)
    sla_deadline = db.Column(db.DateTime, nullable=True)

    accessibility_flag = db.Column(db.Boolean, default=False)
    accessibility_barrier_type = db.Column(db.String(80), nullable=True)

    captured_offline = db.Column(db.Boolean, default=False)
    captured_at = db.Column(db.DateTime, default=datetime.utcnow)
    synced_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)


class SRSIssueEventORM(db.Model):
    """Lifecycle event stream for complaint tracking and auditability."""

    __tablename__ = 'srs_issue_events'

    id = db.Column(db.Integer, primary_key=True)
    issue_public_id = db.Column(db.String(24), nullable=False, index=True)
    from_status = db.Column(db.String(30), nullable=True)
    to_status = db.Column(db.String(30), nullable=False)
    actor_role = db.Column(db.String(50), nullable=False)
    actor_id = db.Column(db.String(80), nullable=True)
    notes = db.Column(db.String(500), nullable=True)
    metadata_json = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class SRSWorkOrderORM(db.Model):
    """Work order and verification state for execution workflows."""

    __tablename__ = 'srs_work_orders'

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.String(24), unique=True, nullable=False, index=True)
    issue_public_id = db.Column(db.String(24), nullable=False, index=True)

    status = db.Column(db.String(30), nullable=False, default='CREATED', index=True)
    assignee_type = db.Column(db.String(20), nullable=False, default='CONTRACTOR')
    contractor_id = db.Column(db.String(40), nullable=True, index=True)
    assigned_team = db.Column(db.String(100), nullable=True)

    sla_hours = db.Column(db.Integer, default=24)
    due_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    estimated_cost = db.Column(db.Float, default=0.0)
    actual_cost = db.Column(db.Float, default=0.0)
    warranty_days = db.Column(db.Integer, default=90)
    warranty_expiry = db.Column(db.DateTime, nullable=True)

    ai_quality_score = db.Column(db.Float, nullable=True)
    sensor_health_delta = db.Column(db.Float, nullable=True)
    quality_score = db.Column(db.Float, nullable=True)
    inspector_validated = db.Column(db.Boolean, default=False)
    citizen_validated = db.Column(db.Boolean, default=False)

    repeat_failure_count = db.Column(db.Integer, default=0)
    payment_status = db.Column(db.String(20), default='HOLD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SRSContractorORM(db.Model):
    """Contractor performance ledger for assignment and governance."""

    __tablename__ = 'srs_contractors'

    contractor_id = db.Column(db.String(40), primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    specialization = db.Column(db.String(80), nullable=False, default='general')
    availability_status = db.Column(db.String(20), default='AVAILABLE')
    capacity_per_day = db.Column(db.Integer, default=8)

    total_jobs = db.Column(db.Integer, default=0)
    sla_adherence_score = db.Column(db.Float, default=75.0)
    repair_quality_score = db.Column(db.Float, default=75.0)
    durability_score = db.Column(db.Float, default=75.0)
    reliability_score = db.Column(db.Float, default=75.0)
    fraud_flags = db.Column(db.Integer, default=0)
    blacklisted = db.Column(db.Boolean, default=False)

    avg_resolution_hours = db.Column(db.Float, default=24.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SRSAssetORM(db.Model):
    """Asset health registry for FR-12 and FR-13."""

    __tablename__ = 'srs_assets'

    asset_id = db.Column(db.String(40), primary_key=True)
    asset_type = db.Column(db.String(80), nullable=False)
    ward = db.Column(db.String(100), nullable=True)

    lat = db.Column(db.Float, nullable=True)
    lon = db.Column(db.Float, nullable=True)
    age_years = db.Column(db.Float, default=0.0)
    criticality = db.Column(db.String(20), default='MEDIUM')
    usage_index = db.Column(db.Float, default=50.0)

    health_score = db.Column(db.Float, default=80.0, index=True)
    predicted_failure_days = db.Column(db.Integer, default=180, index=True)
    degradation_rate = db.Column(db.Float, default=0.1)
    last_sensor_score = db.Column(db.Float, default=80.0)
    maintenance_status = db.Column(db.String(20), default='MONITOR')

    accessibility_compliant = db.Column(db.Boolean, default=True)
    last_inspection_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SRSUtilityMapORM(db.Model):
    """Underground utility records used for pre-dig verification."""

    __tablename__ = 'srs_utility_map'

    utility_id = db.Column(db.String(40), primary_key=True)
    utility_type = db.Column(db.String(40), nullable=False)
    ward = db.Column(db.String(100), nullable=True)
    geometry_json = db.Column(db.Text, default='[]')  # JSON array of points
    depth_m = db.Column(db.Float, default=1.5)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SRSBudgetEventORM(db.Model):
    """Budget events for planned vs actual spend analytics."""

    __tablename__ = 'srs_budget_events'

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.String(24), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False)
    planned_cost = db.Column(db.Float, nullable=False)
    actual_cost = db.Column(db.Float, nullable=False)
    variance_percent = db.Column(db.Float, nullable=False)
    anomaly_flag = db.Column(db.Boolean, default=False, index=True)
    anomaly_reason = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class SRSAuditLogORM(db.Model):
    """Append-only governance audit chain."""

    __tablename__ = 'srs_audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(80), nullable=False, index=True)
    actor_role = db.Column(db.String(50), nullable=False)
    actor_id = db.Column(db.String(80), nullable=True)
    entity_type = db.Column(db.String(60), nullable=False, index=True)
    entity_id = db.Column(db.String(80), nullable=False, index=True)
    before_state = db.Column(db.Text, default='{}')
    after_state = db.Column(db.Text, default='{}')
    reason = db.Column(db.String(250), nullable=True)
    previous_hash = db.Column(db.String(64), nullable=True)
    immutable_hash = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
