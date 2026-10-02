"""Versioned, source-gated resolution API."""
import re

from flask import Blueprint, jsonify, request
from app.extensions import limiter

from app.source_routing.models import OfficialSource
from app.source_routing.service import (
    IdempotencyConflict,
    RoutingInputError,
    check_evidence,
    list_services,
    resolve,
)

bp = Blueprint("source_routing", __name__)


def _error(message, status, error_code="VALIDATION_FAILED"):
    if status == 404:
        error_code = "NOT_FOUND"
    elif status == 409:
        error_code = "IDEMPOTENCY_CONFLICT"
    return jsonify({
        "error": {"message": message},
        "error_code": error_code,
        "message": message,
        "request_id": request.environ.get("scmirn.request_id"),
        "safe_details": {},
    }), status


@bp.route("/triage", methods=["POST"])
@bp.route("/jurisdiction/resolve", methods=["POST"])
@limiter.limit("10 per minute")
def resolve_jurisdiction():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("A JSON object is required.", 400)
    try:
        result = resolve(
            data.get("description"),
            state=data.get("state"),
            district=data.get("district"),
            consent=data.get("consent_to_process") is True,
            idempotency_key=request.headers.get("Idempotency-Key"),
        )
    except RoutingInputError as exc:
        return _error(str(exc), 400)
    except IdempotencyConflict as exc:
        return _error(str(exc), 409)
    response = jsonify(result)
    response.headers["Cache-Control"] = "no-store"
    return response, 200


@bp.route("/services", methods=["GET"])
@limiter.limit("60 per minute")
def get_services():
    items = list_services()
    return jsonify({"items": items, "count": len(items)})


@bp.route("/services/<service_id>", methods=["GET"])
@limiter.limit("60 per minute")
def get_service(service_id):
    service = next((item for item in list_services() if item["service_id"] == service_id), None)
    if service is None:
        return _error("Service not found in the active, source-verified registry.", 404)
    return jsonify(service)


@bp.route("/evidence/check", methods=["POST"])
@limiter.limit("30 per minute")
def evidence_check():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("service_id"), str):
        return _error("service_id is required.", 400)
    try:
        result = check_evidence(data["service_id"], data.get("provided_evidence_ids", []))
    except RoutingInputError as exc:
        return _error(str(exc), 400)
    return jsonify(result)


@bp.route("/sources/<source_key>", methods=["GET"])
@limiter.limit("60 per minute")
def get_source(source_key):
    source = OfficialSource.query.filter_by(source_key=source_key).order_by(OfficialSource.version.desc()).first()
    if source is None:
        return _error("Source not found.", 404)
    return jsonify({
        "source_id": source.source_key,
        "version": source.version,
        "authority": source.authority,
        "title": source.title,
        "source_type": source.source_type,
        "jurisdiction": source.jurisdiction,
        "canonical_url": source.canonical_url,
        "document_hash": source.document_hash,
        "review_state": (
            "REVIEW_REQUIRED_MISSING_HASH"
            if source.verification_status == "VERIFIED" and not source.document_hash
            else "REVIEW_REQUIRED_INVALID_HASH"
            if source.verification_status == "VERIFIED" and not re.fullmatch(r"[0-9a-f]{64}", source.document_hash or "")
            else source.verification_status
        ),
        "effective_from": source.effective_from.isoformat() if source.effective_from else None,
        "effective_until": source.effective_until.isoformat() if source.effective_until else None,
        "retrieved_at": source.retrieved_at.isoformat() if source.retrieved_at else None,
        "verified_at": source.verified_at.isoformat() if source.verified_at else None,
        "verification_status": source.verification_status,
        "supersedes": source.supersedes_id,
        "superseded_by": source.superseded_by_id,
        "reviewer": source.reviewer,
        "parser_version": source.parser_version,
    })
