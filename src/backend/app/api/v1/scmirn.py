"""
SCMIRN SRS API

Concrete, production-focused endpoints implementing FR-01..FR-24.
"""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from marshmallow import Schema, ValidationError, fields, validate

from app.extensions import limiter
from app.core.services.scmirn_srs_service import SCMIRNSRSService


bp = Blueprint("api_v1_scmirn", __name__, url_prefix="/api/v1/scmirn")
service = SCMIRNSRSService()


class ReporterSchema(Schema):
    id = fields.Str(allow_none=True)
    language = fields.Str(load_default="en")
    reputation = fields.Float(load_default=0.5, validate=validate.Range(min=0.0, max=1.0))


class ReportIssueSchema(Schema):
    source = fields.Str(load_default="citizen")
    title = fields.Str(required=True, validate=validate.Length(min=5, max=500))
    description = fields.Str(required=True, validate=validate.Length(min=10, max=5000))
    category = fields.Str(required=True, validate=validate.Length(min=2, max=60))
    ward = fields.Str(load_default="")
    lat = fields.Float(allow_none=True)
    lon = fields.Float(allow_none=True)
    evidence_urls = fields.List(fields.Str(), load_default=list)
    reporter = fields.Nested(ReporterSchema(), load_default=dict)
    captured_offline = fields.Bool(load_default=False)
    captured_at = fields.Str(allow_none=True)


class MultiSourceDetectSchema(Schema):
    source_type = fields.Str(required=True)
    title = fields.Str(load_default="")
    description = fields.Str(load_default="")
    category = fields.Str(load_default="")
    ward = fields.Str(load_default="")
    lat = fields.Float(allow_none=True)
    lon = fields.Float(allow_none=True)
    evidence_urls = fields.List(fields.Str(), load_default=list)


class TransitionSchema(Schema):
    to_status = fields.Str(required=True)
    notes = fields.Str(load_default="")
    manual_override = fields.Bool(load_default=False)


class FeedbackSchema(Schema):
    confirmed = fields.Bool(required=True)
    rating = fields.Int(allow_none=True, validate=validate.Range(min=1, max=5))
    comment = fields.Str(load_default="")


class WorkOrderGenerateSchema(Schema):
    issue_id = fields.Str(required=True)
    estimated_cost = fields.Float(load_default=0.0, validate=validate.Range(min=0))
    warranty_days = fields.Int(load_default=90, validate=validate.Range(min=30, max=3650))


class WorkOrderAssignSchema(Schema):
    contractor_id = fields.Str(allow_none=True)
    assigned_team = fields.Str(load_default="")
    sla_hours = fields.Int(allow_none=True, validate=validate.Range(min=1, max=720))


class WorkOrderVerifySchema(Schema):
    ai_quality_score = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    sensor_health_delta = fields.Float(load_default=0.0)
    inspector_validated = fields.Bool(required=True)
    citizen_validated = fields.Bool(load_default=False)
    actual_cost = fields.Float(allow_none=True, validate=validate.Range(min=0))


class AssetHealthSchema(Schema):
    asset_id = fields.Str(required=True)
    asset_type = fields.Str(required=True)
    ward = fields.Str(load_default="")
    lat = fields.Float(allow_none=True)
    lon = fields.Float(allow_none=True)
    age_years = fields.Float(load_default=0.0)
    degradation_rate = fields.Float(load_default=0.1)
    usage_index = fields.Float(load_default=50.0)
    sensor_score = fields.Float(load_default=80.0)
    criticality = fields.Str(load_default="MEDIUM")
    accessibility_compliant = fields.Bool(load_default=True)
    last_inspection_at = fields.Str(allow_none=True)


class FloodPredictSchema(Schema):
    rainfall_mm = fields.Float(required=True)
    drain_capacity_pct = fields.Float(required=True)
    blockage_index = fields.Float(required=True)
    soil_saturation = fields.Float(load_default=0.5)


class TrafficImpactSchema(Schema):
    baseline_vehicles_per_hour = fields.Float(required=True)
    lane_closure_pct = fields.Float(required=True)
    work_duration_hours = fields.Float(required=True)
    peak_hour = fields.Bool(load_default=True)


class UtilityRegisterSchema(Schema):
    utility_id = fields.Str(required=True)
    utility_type = fields.Str(required=True)
    ward = fields.Str(load_default="")
    depth_m = fields.Float(load_default=1.5)
    active = fields.Bool(load_default=True)
    geometry = fields.List(fields.Dict(), load_default=list)


class PreDigSchema(Schema):
    lat = fields.Float(required=True)
    lon = fields.Float(required=True)
    radius_m = fields.Float(load_default=5.0)


class AccessibilitySchema(Schema):
    barrier_type = fields.Str(required=True)


class BudgetEventSchema(Schema):
    work_order_id = fields.Str(required=True)
    category = fields.Str(load_default="general")
    planned_cost = fields.Float(required=True)
    actual_cost = fields.Float(required=True)


class OfflineSyncSchema(Schema):
    issues = fields.List(fields.Nested(ReportIssueSchema()), required=True)


class ManualOverrideSchema(Schema):
    target_type = fields.Str(required=True, validate=validate.OneOf(["ISSUE", "WORK_ORDER"]))
    target_id = fields.Str(required=True)
    field = fields.Str(required=True)
    value = fields.Raw(required=True)
    reason = fields.Str(load_default="Manual override")


def _actor_role() -> str:
    return str(request.headers.get("X-Actor-Role") or "system").strip().lower()


def _actor_id() -> str | None:
    actor_id = request.headers.get("X-Actor-Id")
    return str(actor_id).strip() if actor_id else None


def _ok(payload: dict, status: int = 200):
    return jsonify(payload), status


def _error(message: str, status: int = 400, details=None):
    body = {"success": False, "error": message}
    if details is not None:
        body["details"] = details
    return jsonify(body), status


@bp.route("/issues/report", methods=["POST"])
@limiter.limit("40 per minute")
def report_issue():
    try:
        payload = ReportIssueSchema().load(request.get_json(silent=True) or {})
        return _ok({"success": True, **service.report_issue(payload)}, 201)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn report_issue error: {exc}")
        return _error("Failed to report issue", 500)


@bp.route("/issues/detect", methods=["POST"])
@limiter.limit("120 per minute")
def detect_issue():
    try:
        payload = MultiSourceDetectSchema().load(request.get_json(silent=True) or {})
        return _ok({"success": True, **service.detect_multisource_issue(payload)}, 201)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn detect_issue error: {exc}")
        return _error("Failed to detect issue", 500)


@bp.route("/issues/<issue_id>/lifecycle", methods=["GET"])
@limiter.limit("120 per minute")
def issue_lifecycle(issue_id: str):
    try:
        return _ok({"success": True, **service.get_issue_lifecycle(issue_id)}, 200)
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn issue_lifecycle error: {exc}")
        return _error("Failed to fetch issue lifecycle", 500)


@bp.route("/issues/<issue_id>/transition", methods=["POST"])
@limiter.limit("120 per minute")
def issue_transition(issue_id: str):
    try:
        payload = TransitionSchema().load(request.get_json(silent=True) or {})
        result = service.transition_issue(
            issue_public_id=issue_id,
            to_status=payload["to_status"],
            actor_role=_actor_role(),
            actor_id=_actor_id(),
            notes=payload.get("notes", ""),
            manual_override=bool(payload.get("manual_override", False)),
        )
        return _ok({"success": True, **result}, 200)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn issue_transition error: {exc}")
        return _error("Failed to transition issue", 500)


@bp.route("/issues/<issue_id>/feedback", methods=["POST"])
@limiter.limit("60 per minute")
def issue_feedback(issue_id: str):
    try:
        payload = FeedbackSchema().load(request.get_json(silent=True) or {})
        result = service.citizen_feedback(
            issue_public_id=issue_id,
            confirmed=bool(payload["confirmed"]),
            rating=payload.get("rating"),
            comment=payload.get("comment"),
            actor_id=_actor_id(),
        )
        return _ok({"success": True, **result}, 200)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn issue_feedback error: {exc}")
        return _error("Failed to capture feedback", 500)


@bp.route("/work-orders/generate", methods=["POST"])
@limiter.limit("60 per minute")
def generate_work_order():
    try:
        payload = WorkOrderGenerateSchema().load(request.get_json(silent=True) or {})
        result = service.generate_work_order(
            issue_public_id=payload["issue_id"],
            estimated_cost=payload["estimated_cost"],
            warranty_days=payload["warranty_days"],
            actor_role=_actor_role(),
            actor_id=_actor_id(),
        )
        return _ok({"success": True, **result}, 201)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn generate_work_order error: {exc}")
        return _error("Failed to generate work order", 500)


@bp.route("/work-orders/<work_order_id>/assign", methods=["POST"])
@limiter.limit("60 per minute")
def assign_work_order(work_order_id: str):
    try:
        payload = WorkOrderAssignSchema().load(request.get_json(silent=True) or {})
        result = service.assign_work_order(
            work_order_id=work_order_id,
            contractor_id=payload.get("contractor_id"),
            assigned_team=payload.get("assigned_team"),
            sla_hours=payload.get("sla_hours"),
            actor_role=_actor_role(),
            actor_id=_actor_id(),
        )
        return _ok({"success": True, **result}, 200)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn assign_work_order error: {exc}")
        return _error("Failed to assign work order", 500)


@bp.route("/work-orders/<work_order_id>/verify", methods=["POST"])
@limiter.limit("60 per minute")
def verify_work_order(work_order_id: str):
    try:
        payload = WorkOrderVerifySchema().load(request.get_json(silent=True) or {})
        result = service.verify_repair(
            work_order_id=work_order_id,
            ai_quality_score=payload["ai_quality_score"],
            sensor_health_delta=payload["sensor_health_delta"],
            inspector_validated=payload["inspector_validated"],
            citizen_validated=payload.get("citizen_validated", False),
            actual_cost=payload.get("actual_cost"),
            actor_role=_actor_role(),
            actor_id=_actor_id(),
        )
        return _ok({"success": True, **result}, 200)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn verify_work_order error: {exc}")
        return _error("Failed to verify repair", 500)


@bp.route("/contractors/<contractor_id>/performance", methods=["GET"])
@limiter.limit("120 per minute")
def contractor_performance(contractor_id: str):
    try:
        return _ok({"success": True, **service.get_contractor_performance(contractor_id)}, 200)
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn contractor_performance error: {exc}")
        return _error("Failed to fetch contractor performance", 500)


@bp.route("/assets/health", methods=["POST"])
@limiter.limit("120 per minute")
def asset_health():
    try:
        payload = AssetHealthSchema().load(request.get_json(silent=True) or {})
        return _ok({"success": True, **service.upsert_asset_health(payload)}, 200)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn asset_health error: {exc}")
        return _error("Failed to update asset health", 500)


@bp.route("/assets/maintenance-schedule", methods=["GET"])
@limiter.limit("120 per minute")
def maintenance_schedule():
    try:
        horizon = request.args.get("horizon_days", default=90, type=int)
        return _ok({"success": True, **service.maintenance_schedule(horizon)}, 200)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn maintenance_schedule error: {exc}")
        return _error("Failed to generate maintenance schedule", 500)


@bp.route("/risk/flood-predict", methods=["POST"])
@limiter.limit("120 per minute")
def flood_predict():
    try:
        payload = FloodPredictSchema().load(request.get_json(silent=True) or {})
        return _ok({"success": True, **service.flood_prediction(payload)}, 200)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn flood_predict error: {exc}")
        return _error("Failed to predict flood risk", 500)


@bp.route("/traffic/impact-simulate", methods=["POST"])
@limiter.limit("120 per minute")
def traffic_impact():
    try:
        payload = TrafficImpactSchema().load(request.get_json(silent=True) or {})
        return _ok({"success": True, **service.traffic_impact(payload)}, 200)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn traffic_impact error: {exc}")
        return _error("Failed to simulate traffic impact", 500)


@bp.route("/utilities/register", methods=["POST"])
@limiter.limit("60 per minute")
def register_utility():
    try:
        payload = UtilityRegisterSchema().load(request.get_json(silent=True) or {})
        return _ok({"success": True, **service.register_utility(payload)}, 201)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn register_utility error: {exc}")
        return _error("Failed to register utility", 500)


@bp.route("/utilities/pre-dig-verify", methods=["POST"])
@limiter.limit("120 per minute")
def pre_dig_verify():
    try:
        payload = PreDigSchema().load(request.get_json(silent=True) or {})
        return _ok({"success": True, **service.pre_dig_verify(payload)}, 200)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn pre_dig_verify error: {exc}")
        return _error("Failed pre-dig verification", 500)


@bp.route("/issues/<issue_id>/accessibility", methods=["POST"])
@limiter.limit("120 per minute")
def accessibility_tag(issue_id: str):
    try:
        payload = AccessibilitySchema().load(request.get_json(silent=True) or {})
        return _ok(
            {
                "success": True,
                **service.tag_accessibility_issue(
                    issue_public_id=issue_id,
                    barrier_type=payload["barrier_type"],
                    actor_role=_actor_role(),
                ),
            },
            200,
        )
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except ValueError as exc:
        return _error(str(exc), 404)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn accessibility_tag error: {exc}")
        return _error("Failed to tag accessibility issue", 500)


@bp.route("/digital-twin/overview", methods=["GET"])
@limiter.limit("120 per minute")
def digital_twin_overview():
    try:
        return _ok({"success": True, **service.digital_twin_overview()}, 200)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn digital_twin_overview error: {exc}")
        return _error("Failed to fetch digital twin overview", 500)


@bp.route("/dashboards/public", methods=["GET"])
@limiter.limit("120 per minute")
def public_dashboard():
    try:
        return _ok({"success": True, **service.public_dashboard()}, 200)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn public_dashboard error: {exc}")
        return _error("Failed to fetch public dashboard", 500)


@bp.route("/governance/audit-logs", methods=["GET"])
@limiter.limit("120 per minute")
def audit_logs():
    try:
        limit = request.args.get("limit", default=100, type=int)
        return _ok({"success": True, **service.list_audit_logs(limit=limit)}, 200)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn audit_logs error: {exc}")
        return _error("Failed to fetch audit logs", 500)


@bp.route("/finance/budget-event", methods=["POST"])
@limiter.limit("120 per minute")
def budget_event():
    try:
        payload = BudgetEventSchema().load(request.get_json(silent=True) or {})
        return _ok({"success": True, **service.budget_event(payload, _actor_role(), _actor_id())}, 201)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn budget_event error: {exc}")
        return _error("Failed to record budget event", 500)


@bp.route("/finance/budget-summary", methods=["GET"])
@limiter.limit("120 per minute")
def budget_summary():
    try:
        return _ok({"success": True, **service.budget_summary()}, 200)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn budget_summary error: {exc}")
        return _error("Failed to fetch budget summary", 500)


@bp.route("/sync/offline-issues", methods=["POST"])
@limiter.limit("120 per minute")
def sync_offline():
    try:
        payload = OfflineSyncSchema().load(request.get_json(silent=True) or {})
        return _ok({"success": True, **service.sync_offline_issues(payload)}, 200)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn sync_offline error: {exc}")
        return _error("Failed to sync offline issues", 500)


@bp.route("/governance/manual-override", methods=["POST"])
@limiter.limit("60 per minute")
def manual_override():
    try:
        role = _actor_role()
        if role not in {"commissioner", "incident_commander", "admin"}:
            return _error("Unauthorized role for manual override", 403)
        payload = ManualOverrideSchema().load(request.get_json(silent=True) or {})
        return _ok({"success": True, **service.manual_override(payload, role, _actor_id())}, 200)
    except ValidationError as exc:
        return _error("Validation failed", 400, exc.messages)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:  # pragma: no cover
        current_app.logger.error(f"scmirn manual_override error: {exc}")
        return _error("Failed manual override", 500)


@bp.route("/traceability", methods=["GET"])
@limiter.limit("120 per minute")
def traceability():
    """
    FR/NFR traceability endpoint for implementation evidence.
    """
    return _ok(
        {
            "success": True,
            "functional_requirements": {
                "FR-01": "/api/v1/scmirn/issues/report",
                "FR-02": "/api/v1/scmirn/issues/detect",
                "FR-03": "embedded in /issues/report duplicate_detection + fraud_detection",
                "FR-04": "embedded in /issues/report classification",
                "FR-05": "embedded in /issues/report escalation",
                "FR-06": "/issues/<id>/transition and /issues/<id>/lifecycle",
                "FR-07": "/issues/<id>/feedback",
                "FR-08": "/work-orders/generate",
                "FR-09": "/work-orders/<id>/assign",
                "FR-10": "/work-orders/<id>/verify",
                "FR-11": "/contractors/<id>/performance",
                "FR-12": "/assets/health",
                "FR-13": "/assets/maintenance-schedule",
                "FR-14": "/risk/flood-predict",
                "FR-15": "/traffic/impact-simulate",
                "FR-16": "/utilities/register + /utilities/pre-dig-verify",
                "FR-17": "/issues/<id>/accessibility",
                "FR-18": "/digital-twin/overview",
                "FR-19": "/dashboards/public",
                "FR-20": "/governance/audit-logs",
                "FR-21": "/finance/budget-event + /finance/budget-summary",
                "FR-22": "multilingual notifications in issue intake",
                "FR-23": "/sync/offline-issues",
                "FR-24": "/governance/manual-override",
            },
            "non_functional_controls": {
                "NFR-05-security": "role guard on manual override, existing Flask security stack",
                "NFR-08-explainability": "classification explainability field in intake response",
                "NFR-12-auditability": "immutable hash-chained audit logs",
                "NFR-13-resilience": "offline capture + delayed sync workflow",
                "NFR-15-localization": "language-aware citizen update templates",
            },
        },
        200,
    )
