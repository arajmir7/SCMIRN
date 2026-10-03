"""MFA and assignment-scoped staff endpoints for restricted case evidence."""
from __future__ import annotations

import hashlib
import time
import uuid
from datetime import timedelta

from flask import Blueprint, current_app, g, jsonify, make_response, request, send_file, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.exc import SQLAlchemyError

from app.evidence_vault.providers import evidence_store, malware_scanner
from app.evidence_vault.scanning import MalwareDetected, ScannerUnavailable
from app.evidence_vault.service import EvidenceTooLarge, EvidenceVault, InvalidEvidence
from app.evidence_vault.storage import EvidenceStoreError
from app.extensions import db
from app.staff_auth.authorization import PolicyAttributes, StaffPrincipal, authorize
from app.staff_auth.models import EvidenceObject, StaffCase
from app.staff_auth.security import normalize_db_time, now_utc, record_audit, staff_required


bp = Blueprint("staff_evidence", __name__)


def _principal():
    return StaffPrincipal(
        user_id=g.staff_user.id,
        tenant_id=g.staff_tenant_id,
        roles=frozenset(g.staff_roles),
        active=bool(g.staff_user.active),
        mfa_verified=bool(g.staff_session.mfa_verified_at),
    )


def _case_attributes(case):
    return PolicyAttributes(
        tenant_id=case.tenant_id,
        purpose="CASE_OPERATIONS",
        sensitivity="INTERNAL",
        created_by_id=case.created_by,
        owner_id=case.created_by,
        assigned_user_id=case.assigned_user_id,
    )


def _evidence_attributes(case, evidence=None):
    return PolicyAttributes(
        tenant_id=case.tenant_id,
        purpose="CASE_EVIDENCE",
        sensitivity="RESTRICTED",
        created_by_id=case.created_by,
        owner_id=case.created_by,
        assigned_user_id=case.assigned_user_id,
        case_id=case.id,
        legal_hold=bool(evidence and evidence.legal_hold),
    )


def _find_case(case_id):
    case = StaffCase.query.filter_by(id=case_id, tenant_id=g.staff_tenant_id).first()
    if case is None or not authorize(_principal(), "case:read", _case_attributes(case)):
        return None
    return case


def _find_evidence(evidence_id):
    evidence = EvidenceObject.query.filter_by(
        id=evidence_id, tenant_id=g.staff_tenant_id,
    ).first()
    if evidence is None:
        return None, None
    case = _find_case(evidence.case_id)
    if case is None:
        return None, None
    return evidence, case


def _metadata(evidence):
    return {
        "id": evidence.id,
        "case_id": evidence.case_id,
        "content_type": evidence.content_type,
        "size_bytes": evidence.size_bytes,
        "checksum_sha256": evidence.checksum_sha256,
        "scan_status": evidence.scan_status,
        "scanner_version": evidence.scanner_version,
        "retention_policy_id": evidence.retention_policy_id,
        "retention_until": normalize_db_time(evidence.retention_until).isoformat(),
        "legal_hold": bool(evidence.legal_hold),
        "lifecycle_status": evidence.lifecycle_status,
        "created_at": evidence.created_at.isoformat(),
        "deleted_at": evidence.deleted_at.isoformat() if evidence.deleted_at else None,
        "deletion_verified_at": (
            evidence.deletion_verified_at.isoformat()
            if evidence.deletion_verified_at else None
        ),
    }


def _disabled():
    if not current_app.config.get("EVIDENCE_VAULT_ENABLED", False):
        return jsonify({
            "success": False,
            "error": "Evidence handling is unavailable until its approved storage, scanner, and retention policy are configured.",
            "code": "EVIDENCE_VAULT_DISABLED",
        }), 503
    return None


def _policy_unavailable():
    days = current_app.config.get("EVIDENCE_DEFAULT_RETENTION_DAYS")
    policy_id = current_app.config.get("EVIDENCE_RETENTION_POLICY_ID")
    if not isinstance(days, int) or days <= 0 or not isinstance(policy_id, str) or not policy_id.strip():
        return jsonify({
            "success": False,
            "error": "Evidence intake is unavailable because no approved retention policy is configured.",
            "code": "EVIDENCE_RETENTION_POLICY_UNAVAILABLE",
        }), 503
    return None


def _retrieval_ticket_serializer():
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"], salt="scmirn-evidence-retrieval-v1"
    )


def _ticket_matches(ticket, evidence):
    if not isinstance(ticket, str) or not ticket or len(ticket) > 4096:
        return False
    try:
        values = _retrieval_ticket_serializer().loads(ticket, max_age=300)
    except (BadSignature, SignatureExpired, TypeError, ValueError):
        return False
    return (
        values.get("evidence_id") == evidence.id
        and values.get("tenant_id") == evidence.tenant_id
        and values.get("case_id") == evidence.case_id
        and values.get("user_id") == g.staff_user.id
        and values.get("session_hash") == g.staff_session.session_hash
        and values.get("key") == evidence.object_key
        and isinstance(values.get("expires_at"), int)
        and values["expires_at"] > int(time.time())
    )


def _not_found():
    return jsonify({"success": False, "error": "Evidence not found.", "code": "NOT_FOUND"}), 404


def _retrieval_url(evidence, ttl: int) -> str:
    ticket = _retrieval_ticket_serializer().dumps({
        "key": evidence.object_key,
        "evidence_id": evidence.id,
        "tenant_id": evidence.tenant_id,
        "case_id": evidence.case_id,
        "user_id": g.staff_user.id,
        "session_hash": g.staff_session.session_hash,
        "expires_at": int(time.time()) + ttl,
    })
    return url_for(
        "staff_evidence.read_evidence_content",
        evidence_id=evidence.id,
        ticket=ticket,
        _external=False,
    )


@bp.post("/cases/<case_id>/evidence")
@staff_required("CASE_OFFICER")
def upload_case_evidence(case_id):
    disabled = _disabled()
    if disabled:
        return disabled
    retention_unavailable = _policy_unavailable()
    if retention_unavailable:
        return retention_unavailable
    case = _find_case(case_id)
    if case is None or not authorize(
        _principal(), "evidence:upload", _evidence_attributes(case)
    ):
        return _not_found()
    maximum = int(current_app.config.get("EVIDENCE_MAX_BYTES", 15 * 1024 * 1024))
    if request.content_length is not None and request.content_length > maximum + 1024 * 1024:
        return jsonify({"success": False, "error": "Evidence exceeds the configured size limit.", "code": "EVIDENCE_TOO_LARGE"}), 413
    upload = request.files.get("file")
    if upload is None:
        return jsonify({"success": False, "error": "Evidence file is required.", "code": "EVIDENCE_REQUIRED"}), 400
    try:
        store = evidence_store()
        result = EvidenceVault(
            store, malware_scanner(), max_bytes=maximum,
        ).upload(upload.stream, filename=upload.filename or "", content_type=upload.mimetype or "")
    except EvidenceTooLarge:
        return jsonify({"success": False, "error": "Evidence exceeds the configured size limit.", "code": "EVIDENCE_TOO_LARGE"}), 413
    except InvalidEvidence:
        return jsonify({"success": False, "error": "Evidence type or file signature is not permitted.", "code": "EVIDENCE_TYPE_REJECTED"}), 400
    except MalwareDetected:
        return jsonify({"success": False, "error": "Evidence was rejected by malware scanning.", "code": "EVIDENCE_SCAN_REJECTED"}), 422
    except (ScannerUnavailable, EvidenceStoreError, RuntimeError, ValueError):
        return jsonify({"success": False, "error": "Evidence storage or malware scanning is unavailable.", "code": "EVIDENCE_DEPENDENCY_UNAVAILABLE"}), 503

    now = now_utc()
    evidence = EvidenceObject(
        id=str(uuid.uuid4()),
        tenant_id=case.tenant_id,
        case_id=case.id,
        created_by=g.staff_user.id,
        object_key=result.object_key,
        content_type=result.content_type,
        size_bytes=result.size_bytes,
        checksum_sha256=result.checksum_sha256,
        scan_status="CLEAN",
        scanner_version=result.scanner_version,
        retention_policy_id=current_app.config["EVIDENCE_RETENTION_POLICY_ID"],
        retention_until=now + timedelta(days=int(current_app.config["EVIDENCE_DEFAULT_RETENTION_DAYS"])),
        legal_hold=False,
        lifecycle_status="ACTIVE",
        deletion_attempts=0,
        created_at=now,
    )
    db.session.add(evidence)
    record_audit("STAFF_EVIDENCE_UPLOADED", "evidence_object", evidence.id, g.staff_user.id)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        try:
            store.delete(result.object_key)
        except Exception:
            object_key_digest = hashlib.sha256(result.object_key.encode("utf-8")).hexdigest()
            current_app.logger.error(
                "evidence_orphan_cleanup_failed object_key_sha256=%s",
                object_key_digest,
            )
        return jsonify({"success": False, "error": "Evidence metadata could not be stored.", "code": "EVIDENCE_METADATA_UNAVAILABLE"}), 503
    response = make_response(jsonify({"success": True, "evidence": _metadata(evidence)}), 201)
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/cases/<case_id>/evidence")
@staff_required("CASE_OFFICER")
def list_case_evidence(case_id):
    disabled = _disabled()
    if disabled:
        return disabled
    case = _find_case(case_id)
    if case is None or not authorize(
        _principal(), "evidence:read", _evidence_attributes(case)
    ):
        return _not_found()
    rows = EvidenceObject.query.filter_by(
        tenant_id=g.staff_tenant_id, case_id=case.id,
    ).order_by(EvidenceObject.created_at.desc()).limit(100).all()
    return jsonify({"success": True, "evidence": [_metadata(row) for row in rows]})


@bp.get("/evidence/<evidence_id>")
@staff_required("CASE_OFFICER")
def get_case_evidence(evidence_id):
    disabled = _disabled()
    if disabled:
        return disabled
    evidence, case = _find_evidence(evidence_id)
    if evidence is None or case is None or not authorize(
        _principal(), "evidence:read", _evidence_attributes(case, evidence)
    ):
        return _not_found()
    return jsonify({"success": True, "evidence": _metadata(evidence)})


@bp.get("/evidence/<evidence_id>/retrieval")
@staff_required("CASE_OFFICER")
def get_evidence_retrieval_url(evidence_id):
    disabled = _disabled()
    if disabled:
        return disabled
    evidence, case = _find_evidence(evidence_id)
    if evidence is None or case is None or evidence.lifecycle_status == "DELETED":
        return _not_found()
    if not authorize(_principal(), "evidence:read", _evidence_attributes(case, evidence)):
        return _not_found()
    if now_utc() >= normalize_db_time(evidence.retention_until) and not evidence.legal_hold:
        return _not_found()
    ttl = min(max(int(current_app.config.get("EVIDENCE_RETRIEVAL_URL_TTL_SECONDS", 60)), 1), 300)
    try:
        # Downloads always return through this API so the current MFA session,
        # case assignment, authorization, and access audit are checked again.
        evidence_store()
        url = _retrieval_url(evidence, ttl)
    except Exception:
        return jsonify({"success": False, "error": "Evidence retrieval is unavailable.", "code": "EVIDENCE_RETRIEVAL_UNAVAILABLE"}), 503
    record_audit("STAFF_EVIDENCE_RETRIEVAL_ISSUED", "evidence_object", evidence.id, g.staff_user.id)
    db.session.commit()
    response = make_response(jsonify({"success": True, "url": url, "expires_in": ttl}))
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@bp.get("/evidence/<evidence_id>/content")
@staff_required("CASE_OFFICER")
def read_evidence_content(evidence_id):
    disabled = _disabled()
    if disabled:
        return disabled
    evidence, case = _find_evidence(evidence_id)
    if evidence is None or case is None or evidence.lifecycle_status == "DELETED":
        return _not_found()
    if not authorize(_principal(), "evidence:read", _evidence_attributes(case, evidence)):
        return _not_found()
    if now_utc() >= normalize_db_time(evidence.retention_until) and not evidence.legal_hold:
        return _not_found()
    if not _ticket_matches(request.args.get("ticket", ""), evidence):
        return _not_found()
    try:
        content = evidence_store().open(evidence.object_key)
    except Exception:
        return jsonify({"success": False, "error": "Evidence retrieval is unavailable.", "code": "EVIDENCE_RETRIEVAL_UNAVAILABLE"}), 503
    record_audit("STAFF_EVIDENCE_ACCESSED", "evidence_object", evidence.id, g.staff_user.id)
    response = make_response(send_file(
        content,
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name="evidence",
    ))
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@bp.delete("/evidence/<evidence_id>")
@staff_required("CASE_OFFICER")
def delete_expired_evidence(evidence_id):
    disabled = _disabled()
    if disabled:
        return disabled
    evidence, case = _find_evidence(evidence_id)
    if evidence is None or case is None:
        return _not_found()
    if evidence.lifecycle_status == "DELETED":
        return jsonify({"success": True, "evidence": _metadata(evidence)})
    attributes = _evidence_attributes(case, evidence)
    if not authorize(_principal(), "evidence:delete", attributes):
        if evidence.legal_hold:
            return jsonify({"success": False, "error": "Evidence is under legal hold.", "code": "EVIDENCE_LEGAL_HOLD"}), 409
        return _not_found()
    if now_utc() < normalize_db_time(evidence.retention_until):
        return jsonify({"success": False, "error": "Evidence retention has not expired.", "code": "EVIDENCE_RETENTION_ACTIVE"}), 409
    evidence.deletion_attempts += 1
    try:
        verified = evidence_store().delete(evidence.object_key)
    except Exception:
        verified = False
    if not verified:
        evidence.lifecycle_status = "DELETE_FAILED"
        evidence.deletion_last_error = "OBJECT_STORE_UNVERIFIED"
        record_audit("STAFF_EVIDENCE_DELETION_FAILED", "evidence_object", evidence.id, g.staff_user.id)
        db.session.commit()
        return jsonify({"success": False, "error": "Evidence deletion could not be verified and will require retry.", "code": "EVIDENCE_DELETION_UNVERIFIED"}), 503
    evidence.lifecycle_status = "DELETED"
    evidence.deletion_last_error = None
    evidence.deleted_at = now_utc()
    evidence.deletion_verified_at = evidence.deleted_at
    record_audit("STAFF_EVIDENCE_DELETED", "evidence_object", evidence.id, g.staff_user.id)
    db.session.commit()
    return jsonify({"success": True, "evidence": _metadata(evidence)})
