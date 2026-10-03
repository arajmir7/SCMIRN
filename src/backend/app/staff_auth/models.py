"""Tenant-scoped staff identity, case workflow, and metadata audit models."""
from datetime import datetime, timezone
import uuid

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class Tenant(db.Model):
    __tablename__ = "tenants"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = db.Column(db.String(80), nullable=False, unique=True)
    display_name = db.Column(db.String(160), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class StaffUser(db.Model):
    __tablename__ = "staff_users"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "email", name="uq_staff_user_tenant_email"),
        db.UniqueConstraint("tenant_id", "id", name="uq_staff_user_tenant_id"),
        db.CheckConstraint("failed_login_count >= 0", name="ck_staff_failed_login_count"),
    )
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True)
    email = db.Column(db.String(254), nullable=False)
    display_name = db.Column(db.String(160), nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    failed_login_count = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    password_changed_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class StaffMfaFactor(db.Model):
    __tablename__ = "staff_mfa_factors"
    __table_args__ = (
        db.CheckConstraint("failed_attempts >= 0", name="ck_staff_mfa_failed_attempts"),
        db.ForeignKeyConstraint(
            ["tenant_id", "user_id"], ["staff_users.tenant_id", "staff_users.id"],
            name="fk_staff_mfa_factor_tenant_user", ondelete="CASCADE",
        ),
    )
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id = db.Column(db.String(36), nullable=False, unique=True)
    secret_ciphertext = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=False)
    enrollment_token_hash = db.Column(db.String(64))
    enrollment_expires_at = db.Column(db.DateTime(timezone=True))
    last_totp_step = db.Column(db.BigInteger, nullable=False, default=-1)
    failed_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    activated_at = db.Column(db.DateTime(timezone=True))


class StaffMfaChallenge(db.Model):
    __tablename__ = "staff_mfa_challenges"
    __table_args__ = (
        db.ForeignKeyConstraint(
            ["tenant_id", "user_id"], ["staff_users.tenant_id", "staff_users.id"],
            name="fk_staff_mfa_challenge_tenant_user", ondelete="CASCADE",
        ),
    )
    token_hash = db.Column(db.String(64), primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.String(36), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    consumed_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class StaffRoleGrant(db.Model):
    __tablename__ = "staff_role_grants"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "user_id", "role", name="uq_staff_role_grant"),
        db.CheckConstraint("role IN ('TENANT_ADMIN', 'CASE_OFFICER', 'SOURCE_REVIEWER', 'AUDITOR')", name="ck_staff_role_name"),
        db.ForeignKeyConstraint(
            ["tenant_id", "user_id"], ["staff_users.tenant_id", "staff_users.id"],
            name="fk_staff_role_grant_tenant_user", ondelete="CASCADE",
        ),
    )
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.String(36), nullable=False, index=True)
    role = db.Column(db.String(32), nullable=False)
    granted_by = db.Column(db.String(36), db.ForeignKey("staff_users.id", ondelete="SET NULL"))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class StaffSession(db.Model):
    __tablename__ = "staff_sessions"
    __table_args__ = (
        db.ForeignKeyConstraint(
            ["tenant_id", "user_id"], ["staff_users.tenant_id", "staff_users.id"],
            name="fk_staff_session_tenant_user", ondelete="CASCADE",
        ),
    )
    session_hash = db.Column(db.String(64), primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.String(36), nullable=False, index=True)
    csrf_hash = db.Column(db.String(64), nullable=False)
    mfa_verified_at = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    idle_expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    absolute_expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True))


class StaffCase(db.Model):
    __tablename__ = "staff_cases"
    __table_args__ = (
        db.UniqueConstraint("tenant_id", "case_ref", name="uq_staff_case_tenant_ref"),
        db.UniqueConstraint("tenant_id", "id", name="uq_staff_case_tenant_id"),
        db.CheckConstraint("status IN ('OPEN', 'UNDER_REVIEW', 'ACTION_REQUIRED', 'RESOLVED', 'CLOSED')", name="ck_staff_case_status"),
        db.CheckConstraint("priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')", name="ck_staff_case_priority"),
        db.ForeignKeyConstraint(
            ["tenant_id", "created_by"], ["staff_users.tenant_id", "staff_users.id"],
            name="fk_staff_case_creator_tenant_user", ondelete="RESTRICT",
        ),
    )
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True)
    case_ref = db.Column(db.String(24), nullable=False)
    case_type = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="OPEN")
    priority = db.Column(db.String(16), nullable=False, default="NORMAL")
    assigned_user_id = db.Column(db.String(36), db.ForeignKey("staff_users.id", ondelete="SET NULL"), index=True)
    created_by = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class StaffCaseEvent(db.Model):
    __tablename__ = "staff_case_events"
    __table_args__ = (
        db.ForeignKeyConstraint(
            ["tenant_id", "case_id"], ["staff_cases.tenant_id", "staff_cases.id"],
            name="fk_staff_case_event_tenant_case", ondelete="CASCADE",
        ),
        db.ForeignKeyConstraint(
            ["tenant_id", "actor_id"], ["staff_users.tenant_id", "staff_users.id"],
            name="fk_staff_case_event_tenant_actor", ondelete="RESTRICT",
        ),
    )
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = db.Column(db.String(36), nullable=False, index=True)
    actor_id = db.Column(db.String(36), nullable=False)
    event_type = db.Column(db.String(40), nullable=False)
    from_status = db.Column(db.String(32))
    to_status = db.Column(db.String(32))
    metadata_json = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class StaffAuditEvent(db.Model):
    __tablename__ = "staff_audit_events"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = db.Column(db.String(36), db.ForeignKey("staff_users.id", ondelete="SET NULL"))
    action = db.Column(db.String(64), nullable=False)
    object_type = db.Column(db.String(48), nullable=False)
    object_id = db.Column(db.String(64), nullable=False)
    request_id = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class EvidenceObject(db.Model):
    """Private file metadata; bytes live only in the evidence object store."""
    __tablename__ = "evidence_objects"
    __table_args__ = (
        db.ForeignKeyConstraint(
            ["tenant_id", "case_id"], ["staff_cases.tenant_id", "staff_cases.id"],
            name="fk_evidence_tenant_case", ondelete="RESTRICT",
        ),
        db.ForeignKeyConstraint(
            ["tenant_id", "created_by"], ["staff_users.tenant_id", "staff_users.id"],
            name="fk_evidence_tenant_creator", ondelete="RESTRICT",
        ),
        db.UniqueConstraint("object_key", name="uq_evidence_object_key"),
        db.CheckConstraint("size_bytes > 0", name="ck_evidence_size_positive"),
        db.CheckConstraint("length(object_key) = 64", name="ck_evidence_object_key_length"),
        db.CheckConstraint("length(checksum_sha256) = 64", name="ck_evidence_checksum_length"),
        db.CheckConstraint(
            "length(trim(retention_policy_id)) > 0",
            name="ck_evidence_retention_policy_id",
        ),
        db.CheckConstraint(
            "content_type IN ('application/pdf', 'image/png', 'image/jpeg')",
            name="ck_evidence_content_type",
        ),
        db.CheckConstraint("scan_status = 'CLEAN'", name="ck_evidence_only_clean_rows"),
        db.CheckConstraint(
            "lifecycle_status IN ('ACTIVE', 'DELETE_FAILED', 'DELETED')",
            name="ck_evidence_lifecycle_status",
        ),
        db.CheckConstraint("deletion_attempts >= 0", name="ck_evidence_deletion_attempts"),
        db.Index("ix_evidence_tenant_case_created", "tenant_id", "case_id", "created_at"),
        db.Index("ix_evidence_retention", "retention_until", "legal_hold", "lifecycle_status"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True)
    case_id = db.Column(db.String(36), nullable=False, index=True)
    created_by = db.Column(db.String(36), nullable=False)
    object_key = db.Column(db.String(64), nullable=False)
    content_type = db.Column(db.String(64), nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=False)
    checksum_sha256 = db.Column(db.String(64), nullable=False)
    scan_status = db.Column(db.String(16), nullable=False, default="CLEAN")
    scanner_version = db.Column(db.String(120), nullable=False)
    retention_policy_id = db.Column(db.String(120), nullable=False)
    retention_until = db.Column(db.DateTime(timezone=True), nullable=False)
    legal_hold = db.Column(db.Boolean, nullable=False, default=False)
    lifecycle_status = db.Column(db.String(24), nullable=False, default="ACTIVE")
    deletion_attempts = db.Column(db.Integer, nullable=False, default=0)
    deletion_last_error = db.Column(db.String(64))
    deleted_at = db.Column(db.DateTime(timezone=True))
    deletion_verified_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
