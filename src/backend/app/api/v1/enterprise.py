"""
Enterprise command-center APIs for SCMIRN.

This module adds enterprise-grade simulation endpoints for:
 - Executive war room (health score, risk radar, crisis sandbox, ROI, sentiment)
 - Connector framework (20-suite catalog + OAuth/SSO bootstrap)
 - Advanced AI and automation
 - Blockchain trust and cyber-physical kill switch
 - Citizen experience, data intelligence, operations, multi-tenant scaling
 - Revenue model APIs
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import hashlib
import math
import os
from pathlib import Path
import uuid
from typing import Any, Dict, List

from flask import Blueprint, current_app, jsonify, request
from marshmallow import Schema, ValidationError, fields, validate

from app.extensions import limiter
from app.infrastructure.external.email_delivery import (
    resolve_email_provider,
    send_briefing_email,
)
from app.infrastructure.database.models import (
    IoTAssetORM,
    IssueORM,
    ResilienceHubORM,
    UserGamificationORM,
    UserORM,
)


bp = Blueprint("api_v1_enterprise", __name__, url_prefix="/api/v1/enterprise")


TWELVE_LAYERS = [
    "SENSING",
    "CONNECTIVITY",
    "UTILITIES",
    "MOBILITY",
    "PUBLIC_SAFETY",
    "HEALTHCARE",
    "SUPPLY_CHAIN",
    "GOVERNANCE",
    "CITIZEN_EXPERIENCE",
    "ECONOMIC_ACTIVITY",
    "LEGAL_COMPLIANCE",
    "TRUST_AND_AUDIT",
]


CONNECTOR_CATALOG = [
    {
        "id": "sap_erp",
        "suite": "SAP",
        "product": "S/4HANA",
        "capabilities": ["procurement_sync", "budget_sync", "vendor_lifecycle"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "oracle_erp",
        "suite": "Oracle",
        "product": "Fusion ERP",
        "capabilities": ["procurement_sync", "budget_sync", "vendor_lifecycle"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "salesforce",
        "suite": "Salesforce",
        "product": "Service Cloud",
        "capabilities": ["citizen_crm", "case_tracking", "service_workflows"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "hubspot",
        "suite": "HubSpot",
        "product": "Service Hub",
        "capabilities": ["citizen_crm", "case_tracking"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "arcgis",
        "suite": "Esri",
        "product": "ArcGIS",
        "capabilities": ["gis_import_export", "spatial_layers", "digital_twin_feeds"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "autocad",
        "suite": "Autodesk",
        "product": "AutoCAD",
        "capabilities": ["cad_import_export", "infrastructure_design_sync"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "slack",
        "suite": "Slack",
        "product": "Enterprise Grid",
        "capabilities": ["department_alerts", "incident_channels", "workflow_commands"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "teams",
        "suite": "Microsoft",
        "product": "Teams",
        "capabilities": ["department_alerts", "incident_channels", "approval_cards"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "powerbi",
        "suite": "Microsoft",
        "product": "Power BI",
        "capabilities": ["bi_export", "streaming_dashboards", "semantic_model_sync"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "tableau",
        "suite": "Tableau",
        "product": "Cloud",
        "capabilities": ["bi_export", "semantic_model_sync"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "twilio",
        "suite": "Twilio",
        "product": "Messaging",
        "capabilities": ["sms_notifications", "voice_outreach", "otp_delivery"],
        "auth": {"oauth2": True, "saml": False, "oidc": True},
    },
    {
        "id": "sendgrid",
        "suite": "Twilio",
        "product": "SendGrid",
        "capabilities": ["email_campaigns", "citizen_updates", "service_announcements"],
        "auth": {"oauth2": True, "saml": False, "oidc": True},
    },
    {
        "id": "servicenow",
        "suite": "ServiceNow",
        "product": "ITSM",
        "capabilities": ["ticket_sync", "incident_workflows", "asset_registry_sync"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "workday",
        "suite": "Workday",
        "product": "HCM",
        "capabilities": ["workforce_sync", "shift_capacity_planning"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "docusign",
        "suite": "DocuSign",
        "product": "eSignature",
        "capabilities": ["contract_signing", "mou_approval_flows"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "okta",
        "suite": "Okta",
        "product": "Workforce Identity",
        "capabilities": ["sso_broker", "mfa_policy_enforcement"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "aws",
        "suite": "AWS",
        "product": "Cloud",
        "capabilities": ["iac_deployment", "managed_datastores", "event_bus"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "azure",
        "suite": "Microsoft",
        "product": "Azure",
        "capabilities": ["iac_deployment", "managed_datastores", "event_bus"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "gcp",
        "suite": "Google",
        "product": "Google Cloud",
        "capabilities": ["iac_deployment", "managed_datastores", "event_bus"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
    {
        "id": "snowflake",
        "suite": "Snowflake",
        "product": "Data Cloud",
        "capabilities": ["warehouse_export", "secure_data_sharing", "policy_analytics"],
        "auth": {"oauth2": True, "saml": True, "oidc": True},
    },
]


DISTRICT_COORDS = [
    {"district": "Central", "lat": 28.6139, "lng": 77.2090},
    {"district": "North", "lat": 28.7041, "lng": 77.1025},
    {"district": "South", "lat": 28.5355, "lng": 77.3910},
    {"district": "East", "lat": 28.6280, "lng": 77.2789},
    {"district": "West", "lat": 28.6692, "lng": 77.0910},
]


def _now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _today_seed(city_id: str) -> int:
    raw = f"{city_id}:{date.today().isoformat()}"
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12], 16)


def _noise(seed: int, idx: int, low: float, high: float) -> float:
    if high <= low:
        return low
    mixed = (seed ^ (idx * 0x45D9F3B)) & 0xFFFFFFFFFFFF
    ratio = mixed / float(0xFFFFFFFFFFFF)
    return low + (high - low) * ratio


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _band(score: float) -> str:
    if score >= 85:
        return "EXCELLENT"
    if score >= 70:
        return "STRONG"
    if score >= 55:
        return "WATCH"
    return "CRITICAL"


def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def _collect_city_metrics(city_id: str) -> Dict[str, Any]:
    seed = _today_seed(city_id)

    assets = IoTAssetORM.query.all()
    avg_asset_health = (
        sum(float(a.health_score or 0) for a in assets) / len(assets) if assets else _noise(seed, 1, 72.0, 90.0)
    )
    critical_assets = sum(1 for a in assets if (a.status or "").upper() == "CRITICAL")

    issues = IssueORM.query.all()
    total_issues = len(issues)
    resolved_issues = sum(
        1
        for issue in issues
        if (issue.status or "").lower() in {"resolved", "closed", "completed", "verified"}
    )
    funding_target = sum(float(i.fund_target or 0) for i in issues)
    funding_collected = sum(float(i.fund_collected or 0) for i in issues)

    users = UserORM.query.count()
    engaged = UserGamificationORM.query.filter(UserGamificationORM.civic_score >= 350).count()
    engagement = _safe_div(float(engaged), float(users), default=_noise(seed, 4, 0.45, 0.72))

    hubs = ResilienceHubORM.query.all()
    if hubs:
        avg_soc = sum(float(h.battery_soc_percent or 0.0) for h in hubs) / len(hubs)
        emergency_hubs = sum(1 for h in hubs if (h.operational_mode or "").upper() == "EMERGENCY")
    else:
        avg_soc = _noise(seed, 5, 54.0, 83.0)
        emergency_hubs = int(round(_noise(seed, 6, 0.0, 2.0)))

    issue_resolution_rate = _safe_div(float(resolved_issues), float(total_issues), default=_noise(seed, 7, 0.58, 0.84))
    funding_ratio = _safe_div(float(funding_collected), float(funding_target), default=_noise(seed, 8, 0.42, 0.78))

    infrastructure = (
        avg_asset_health * 0.62
        + (issue_resolution_rate * 100.0) * 0.28
        - min(15.0, float(critical_assets) * 1.8)
        + _noise(seed, 9, -2.0, 2.0)
    )
    citizen_satisfaction = (
        (issue_resolution_rate * 100.0) * 0.4
        + (engagement * 100.0) * 0.3
        + (funding_ratio * 100.0) * 0.2
        + _noise(seed, 10, 2.0, 9.0)
    )
    emergency_readiness = (
        (avg_soc * 0.64)
        + ((100.0 - (emergency_hubs * 18.0)) * 0.32)
        + _noise(seed, 11, -3.0, 6.0)
    )
    economic_impact = (
        (funding_ratio * 100.0) * 0.42
        + (avg_asset_health * 0.36)
        + ((1.0 - min(1.0, _safe_div(float(total_issues - resolved_issues), float(max(1, total_issues))))) * 100.0 * 0.22)
        + _noise(seed, 12, 1.0, 8.0)
    )

    components = {
        "infrastructure": int(round(_clamp(infrastructure))),
        "citizen_satisfaction": int(round(_clamp(citizen_satisfaction))),
        "emergency_readiness": int(round(_clamp(emergency_readiness))),
        "economic_impact": int(round(_clamp(economic_impact))),
    }

    weighted = (
        components["infrastructure"] * 0.35
        + components["citizen_satisfaction"] * 0.25
        + components["emergency_readiness"] * 0.25
        + components["economic_impact"] * 0.15
    )
    score = int(round(_clamp(weighted)))
    prior_score = int(round(_clamp(score - _noise(seed, 13, -4.0, 5.0))))
    delta = score - prior_score

    return {
        "score": score,
        "prior_score": prior_score,
        "delta": delta,
        "components": components,
        "facts": {
            "critical_assets": int(critical_assets),
            "total_assets": int(len(assets)),
            "issue_resolution_rate": round(issue_resolution_rate, 3),
            "engagement_rate": round(engagement, 3),
            "funding_ratio": round(funding_ratio, 3),
            "resilience_hubs": int(len(hubs)),
        },
    }


def _risk_nodes(city_id: str) -> List[Dict[str, Any]]:
    seed = _today_seed(city_id)
    risk_types = ["FINANCIAL", "CLIMATE", "SOCIAL", "CYBER", "INFRASTRUCTURE"]
    nodes: List[Dict[str, Any]] = []
    idx = 0
    for district in DISTRICT_COORDS:
        for risk_type in risk_types:
            idx += 1
            base = _noise(seed, idx, 0.18, 0.76)
            score7 = int(round(_clamp(base * 100.0)))
            score30 = int(round(_clamp((base + _noise(seed, idx + 50, 0.03, 0.14)) * 100.0)))
            score90 = int(round(_clamp((base + _noise(seed, idx + 120, 0.06, 0.22)) * 100.0)))
            nodes.append(
                {
                    "node_id": f"{district['district'].lower()}_{risk_type.lower()}",
                    "district": district["district"],
                    "coordinates": {
                        "lat": district["lat"] + _noise(seed, idx + 200, -0.03, 0.03),
                        "lng": district["lng"] + _noise(seed, idx + 300, -0.03, 0.03),
                        "altitude_m": round(_noise(seed, idx + 400, 180.0, 2400.0), 1),
                    },
                    "risk_type": risk_type,
                    "forecasts": {"7d": score7, "30d": score30, "90d": score90},
                    "priority": "HIGH" if score30 >= 70 else ("MEDIUM" if score30 >= 50 else "LOW"),
                }
            )
    nodes.sort(key=lambda n: n["forecasts"]["30d"], reverse=True)
    return nodes


def _compose_briefing_lines(city_id: str) -> List[str]:
    metrics = _collect_city_metrics(city_id)
    nodes = _risk_nodes(city_id)[:5]
    top_risk = nodes[0] if nodes else None

    lines = [
        "SCMIRN Executive Daily Briefing",
        f"City: {city_id}",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"City Health Score: {metrics['score']} ({_band(metrics['score'])})",
        f"Delta vs prior period: {metrics['delta']:+d}",
        (
            f"Infrastructure: {metrics['components']['infrastructure']} | "
            f"Citizen: {metrics['components']['citizen_satisfaction']} | "
            f"Emergency: {metrics['components']['emergency_readiness']} | "
            f"Economic: {metrics['components']['economic_impact']}"
        ),
        "",
        "Top Emerging Risks:",
    ]

    for risk in nodes:
        lines.append(
            f"- {risk['district']} {risk['risk_type']} "
            f"(7d/30d/90d: {risk['forecasts']['7d']}/{risk['forecasts']['30d']}/{risk['forecasts']['90d']})"
        )

    lines.extend(
        [
            "",
            "Recommended Actions:",
            "- Prioritize maintenance dispatch to high-risk districts.",
            "- Trigger cross-department tabletop drill for compound disruptions.",
            "- Expand citizen communication campaigns for top concerns.",
        ]
    )

    if top_risk:
        lines.append(f"- Escalate {top_risk['risk_type']} risk committee in {top_risk['district']}.")
    return lines[:55]


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_minimal_pdf(lines: List[str]) -> bytes:
    command_lines = ["BT", "/F1 11 Tf", "48 800 Td", "14 TL"]
    for index, line in enumerate(lines[:55]):
        if index > 0:
            command_lines.append("T*")
        command_lines.append(f"({_pdf_escape(line[:115])}) Tj")
    command_lines.append("ET")
    stream = "\n".join(command_lines).encode("latin-1", errors="replace")

    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] "
        "/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream.decode('latin-1')}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    parts: List[bytes] = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    cursor = len(parts[0])
    for index, obj in enumerate(objects, start=1):
        payload = f"{index} 0 obj\n{obj}\nendobj\n".encode("latin-1")
        offsets.append(cursor)
        parts.append(payload)
        cursor += len(payload)

    xref_offset = cursor
    xref_header = f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("latin-1")
    parts.append(xref_header)
    for offset in offsets[1:]:
        parts.append(f"{offset:010d} 00000 n \n".encode("latin-1"))

    trailer = (
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("latin-1")
    parts.append(trailer)
    return b"".join(parts)


class CrisisEventSchema(Schema):
    event_type = fields.Str(required=True, validate=validate.Length(min=3, max=64))
    intensity = fields.Float(load_default=0.7, validate=validate.Range(min=0.05, max=1.0))
    duration_hours = fields.Int(load_default=24, validate=validate.Range(min=1, max=336))


class CrisisSimulationSchema(Schema):
    city_id = fields.Str(load_default="metro-demo")
    events = fields.List(fields.Nested(CrisisEventSchema()), required=True, validate=validate.Length(min=1, max=6))
    population_exposed = fields.Int(load_default=250000, validate=validate.Range(min=100, max=50000000))


class InvestmentSchema(Schema):
    initiative = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    capex = fields.Float(required=True, validate=validate.Range(min=0))
    opex_annual = fields.Float(load_default=0.0, validate=validate.Range(min=0))
    expected_loss_reduction_percent = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    implementation_months = fields.Int(load_default=6, validate=validate.Range(min=1, max=60))


class ROICalculatorSchema(Schema):
    horizon_years = fields.Int(load_default=5, validate=validate.Range(min=1, max=20))
    discount_rate = fields.Float(load_default=0.08, validate=validate.Range(min=0, max=0.3))
    baseline_losses = fields.Dict(required=True)
    investments = fields.List(fields.Nested(InvestmentSchema()), required=True, validate=validate.Length(min=1, max=25))


class BriefingRequestSchema(Schema):
    city_id = fields.Str(load_default="metro-demo")
    recipients = fields.List(fields.Email(), required=True, validate=validate.Length(min=1, max=100))
    include_pdf = fields.Bool(load_default=True)
    include_recommendations = fields.Bool(load_default=True)


class ConnectorAuthSchema(Schema):
    tenant_id = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    redirect_uri = fields.Url(required=True)
    scopes = fields.List(fields.Str(validate=validate.Length(min=1, max=60)), load_default=list)


class WorkflowRouteSchema(Schema):
    issue_id = fields.Str(load_default="")
    title = fields.Str(required=True, validate=validate.Length(min=3, max=300))
    category = fields.Str(required=True, validate=validate.Length(min=2, max=80))
    district = fields.Str(load_default="Central")
    severity = fields.Str(load_default="MEDIUM")
    affected_citizens = fields.Int(load_default=50, validate=validate.Range(min=1, max=10000000))
    legal_keywords = fields.List(fields.Str(), load_default=list)


class LegalAnalysisSchema(Schema):
    legal_domain = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    case_facts = fields.Str(required=True, validate=validate.Length(min=20, max=4000))
    judge_name = fields.Str(load_default="Unknown")
    jurisdiction = fields.Str(load_default="IN")


class KillSwitchSchema(Schema):
    node_ids = fields.List(fields.Str(validate=validate.Length(min=2, max=120)), required=True, validate=validate.Length(min=1, max=200))
    compromise_type = fields.Str(load_default="UNKNOWN")
    preserve_services = fields.List(fields.Str(), load_default=lambda: ["EMERGENCY_DISPATCH", "PUBLIC_ALERTING", "HOSPITAL_POWER"])


class PolicyPlaygroundSchema(Schema):
    policy_name = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    target_districts = fields.List(fields.Str(), required=True, validate=validate.Length(min=1, max=20))
    horizon_months = fields.Int(load_default=24, validate=validate.Range(min=1, max=240))
    variant_a = fields.Dict(load_default=dict)
    variant_b = fields.Dict(load_default=dict)


@bp.route("/executive/city-health-score", methods=["GET"])
@limiter.limit("120 per minute")
def city_health_score():
    try:
        city_id = request.args.get("city_id", "metro-demo")
        data = _collect_city_metrics(city_id)
        return jsonify(
            {
                "city_id": city_id,
                "generated_at": _now_z(),
                "city_health_score": data["score"],
                "health_band": _band(data["score"]),
                "delta_vs_prior_period": data["delta"],
                "components": data["components"],
                "drivers": data["facts"],
                "targets": {"quarter_target": 84, "year_target": 88},
            }
        ), 200
    except Exception as exc:
        current_app.logger.error(f"city_health_score error: {exc}")
        return jsonify({"success": False, "error": "Failed to compute city health score"}), 500


@bp.route("/executive/risk-radar", methods=["GET"])
@limiter.limit("120 per minute")
def risk_radar():
    try:
        city_id = request.args.get("city_id", "metro-demo")
        nodes = _risk_nodes(city_id)
        top = nodes[:10]
        return jsonify(
            {
                "city_id": city_id,
                "generated_at": _now_z(),
                "visualization": {"mode": "3D_GLOBE", "projection": "EPSG:4326", "horizons_days": [7, 30, 90]},
                "nodes": nodes,
                "summary": {
                    "critical_nodes_30d": int(sum(1 for n in nodes if n["forecasts"]["30d"] >= 75)),
                    "highest_30d_risk": top[0] if top else None,
                    "top_10": top,
                },
            }
        ), 200
    except Exception as exc:
        current_app.logger.error(f"risk_radar error: {exc}")
        return jsonify({"success": False, "error": "Failed to compute risk radar"}), 500


@bp.route("/executive/crisis-sandbox/simulate", methods=["POST"])
@limiter.limit("30 per minute")
def crisis_sandbox_simulate():
    try:
        payload = CrisisSimulationSchema().load(request.get_json(silent=True) or {})
        city_id = payload["city_id"]
        events = payload["events"]
        population = int(payload["population_exposed"])

        event_weights = {
            "EARTHQUAKE": 1.0,
            "CYBERATTACK": 0.92,
            "FLOOD": 0.84,
            "HEATWAVE": 0.68,
            "POWER_OUTAGE": 0.73,
            "PANDEMIC": 0.81,
        }

        composite = 0.0
        for event in events:
            et = str(event["event_type"]).upper()
            weight = event_weights.get(et, 0.65)
            composite += float(event["intensity"]) * weight
        composite = min(1.0, composite)

        layer_criticality = {
            "SENSING": 0.85,
            "CONNECTIVITY": 0.92,
            "UTILITIES": 0.96,
            "MOBILITY": 0.78,
            "PUBLIC_SAFETY": 0.98,
            "HEALTHCARE": 0.94,
            "SUPPLY_CHAIN": 0.76,
            "GOVERNANCE": 0.71,
            "CITIZEN_EXPERIENCE": 0.64,
            "ECONOMIC_ACTIVITY": 0.81,
            "LEGAL_COMPLIANCE": 0.58,
            "TRUST_AND_AUDIT": 0.69,
        }

        cascade = []
        for index, layer in enumerate(TWELVE_LAYERS):
            stress = _clamp((composite * layer_criticality[layer] * 100.0) + (index * 0.8), 0.0, 100.0)
            cascade.append(
                {
                    "layer": layer,
                    "impact_score": int(round(stress)),
                    "status": "DEGRADED" if stress >= 45 else "STABLE",
                    "estimated_recovery_hours": int(round(4 + stress * 0.6)),
                    "dependent_layers": [TWELVE_LAYERS[(index + 1) % len(TWELVE_LAYERS)]],
                }
            )

        combined_duration = sum(int(event["duration_hours"]) for event in events)
        affected = int(round(population * min(0.95, 0.18 + composite * 0.72)))
        direct_loss = float(round((affected * 180.0) + (composite * 30_000_000.0), 2))
        indirect_loss = float(round(direct_loss * (0.42 + composite * 0.3), 2))

        return jsonify(
            {
                "simulation_id": str(uuid.uuid4()),
                "city_id": city_id,
                "generated_at": _now_z(),
                "scenario": {"events": events, "composite_stress_index": round(composite, 3), "duration_hours": combined_duration},
                "cascade_effects": cascade,
                "outcomes": {
                    "affected_citizens": affected,
                    "critical_service_disruptions": int(sum(1 for row in cascade if row["impact_score"] >= 70)),
                    "estimated_losses_inr": {"direct": direct_loss, "indirect": indirect_loss, "total": float(round(direct_loss + indirect_loss, 2))},
                    "resilience_score_after_response": int(round(_clamp(100.0 - composite * 58.0))),
                },
                "recommended_actions": [
                    "Activate cross-department incident command with unified SLA.",
                    "Isolate compromised digital nodes and preserve critical public services.",
                    "Deploy mutual-aid dispatch for healthcare and utility continuity.",
                ],
            }
        ), 200
    except ValidationError as exc:
        return jsonify({"success": False, "error": "Validation failed", "details": exc.messages}), 400
    except Exception as exc:
        current_app.logger.error(f"crisis_sandbox_simulate error: {exc}")
        return jsonify({"success": False, "error": "Failed to run crisis simulation"}), 500


@bp.route("/executive/roi-calculate", methods=["POST"])
@limiter.limit("60 per minute")
def roi_calculate():
    try:
        payload = ROICalculatorSchema().load(request.get_json(silent=True) or {})
        investments = payload["investments"]
        losses = payload["baseline_losses"]
        horizon = int(payload["horizon_years"])
        discount_rate = float(payload["discount_rate"])

        annual_loss = sum(float(v) for v in losses.values())
        capex_total = sum(float(item["capex"]) for item in investments)
        opex_total = sum(float(item["opex_annual"]) for item in investments)

        remaining_fraction = 1.0
        for item in investments:
            reduction = max(0.0, min(1.0, float(item["expected_loss_reduction_percent"]) / 100.0))
            remaining_fraction *= (1.0 - reduction)
        combined_reduction = 1.0 - remaining_fraction

        prevented_annual = annual_loss * combined_reduction
        annual_net = prevented_annual - opex_total
        payback_years = (capex_total / annual_net) if annual_net > 0 else None

        npv = -capex_total
        for year in range(1, horizon + 1):
            npv += annual_net / ((1.0 + discount_rate) ** year)
        roi_percent = ((annual_net * horizon - capex_total) / capex_total * 100.0) if capex_total > 0 else 0.0

        by_initiative = []
        for item in investments:
            reduction = float(item["expected_loss_reduction_percent"]) / 100.0
            by_initiative.append(
                {
                    "initiative": item["initiative"],
                    "capex": float(item["capex"]),
                    "opex_annual": float(item["opex_annual"]),
                    "loss_prevention_annual": round(annual_loss * reduction, 2),
                    "implementation_months": int(item["implementation_months"]),
                }
            )

        return jsonify(
            {
                "generated_at": _now_z(),
                "inputs": payload,
                "summary": {
                    "baseline_annual_losses_inr": round(annual_loss, 2),
                    "combined_loss_reduction_percent": round(combined_reduction * 100.0, 2),
                    "prevented_losses_annual_inr": round(prevented_annual, 2),
                    "net_benefit_annual_inr": round(annual_net, 2),
                    "payback_years": round(payback_years, 2) if payback_years is not None else None,
                    "roi_percent": round(roi_percent, 2),
                    "npv_inr": round(npv, 2),
                },
                "initiative_breakdown": by_initiative,
            }
        ), 200
    except ValidationError as exc:
        return jsonify({"success": False, "error": "Validation failed", "details": exc.messages}), 400
    except Exception as exc:
        current_app.logger.error(f"roi_calculate error: {exc}")
        return jsonify({"success": False, "error": "Failed to calculate ROI"}), 500


@bp.route("/executive/sentiment-pulse", methods=["GET"])
@limiter.limit("120 per minute")
def sentiment_pulse():
    try:
        city_id = request.args.get("city_id", "metro-demo")
        district_filter = request.args.get("district")
        seed = _today_seed(city_id)

        districts = []
        concerns = ["water_supply", "traffic", "public_safety", "waste_management", "permit_delays"]
        for index, district in enumerate(DISTRICT_COORDS, start=1):
            if district_filter and district["district"].lower() != district_filter.lower():
                continue

            social = _noise(seed, index + 20, -0.35, 0.65)
            call_center = _noise(seed, index + 40, -0.25, 0.55)
            surveys = _noise(seed, index + 60, -0.18, 0.72)
            weighted = (social * 0.45) + (call_center * 0.25) + (surveys * 0.30)
            districts.append(
                {
                    "district": district["district"],
                    "sources": {"social_media": round(social, 3), "call_center": round(call_center, 3), "surveys": round(surveys, 3)},
                    "sentiment_score": round(weighted, 3),
                    "trend_7d": round(weighted + _noise(seed, index + 80, -0.08, 0.08), 3),
                    "top_concern": concerns[(index + int(seed % len(concerns))) % len(concerns)],
                }
            )

        aggregate = sum(float(item["sentiment_score"]) for item in districts) / max(1, len(districts))
        return jsonify(
            {
                "city_id": city_id,
                "generated_at": _now_z(),
                "aggregate_sentiment": round(aggregate, 3),
                "pulse_band": "POSITIVE" if aggregate >= 0.25 else ("NEUTRAL" if aggregate >= -0.05 else "NEGATIVE"),
                "districts": districts,
            }
        ), 200
    except Exception as exc:
        current_app.logger.error(f"sentiment_pulse error: {exc}")
        return jsonify({"success": False, "error": "Failed to compute sentiment pulse"}), 500


@bp.route("/executive/briefings/generate", methods=["POST"])
@limiter.limit("30 per minute")
def generate_briefing():
    try:
        payload = BriefingRequestSchema().load(request.get_json(silent=True) or {})
        city_id = payload["city_id"]
        briefing_id = str(uuid.uuid4())
        lines = _compose_briefing_lines(city_id)
        subject = f"[SCMIRN] Daily Executive Briefing - {city_id}"
        body_text = "\n".join(lines)
        pdf_bytes: bytes | None = None
        pdf_filename: str | None = None

        report_info = None
        if payload["include_pdf"]:
            pdf_bytes = _build_minimal_pdf(lines)
            root = Path(current_app.config.get("UPLOAD_FOLDER", "app/infrastructure/uploads"))
            folder = root / "documents" / "executive_briefings"
            folder.mkdir(parents=True, exist_ok=True)
            filename = f"{date.today().isoformat()}_{briefing_id[:8]}.pdf"
            pdf_filename = filename
            path = folder / filename
            path.write_bytes(pdf_bytes)
            rel_path = os.path.relpath(path, root).replace("\\", "/")
            report_info = {
                "filename": filename,
                "size_bytes": len(pdf_bytes),
                "storage_path": str(path),
                "download_path": f"/uploads/{rel_path}",
            }

        provider = resolve_email_provider(current_app.config)
        dispatch = []
        sent_count = 0
        failed_count = 0
        for recipient in payload["recipients"]:
            delivery = send_briefing_email(
                config=current_app.config,
                recipient=recipient,
                subject=subject,
                body_text=body_text,
                attachment_bytes=pdf_bytes if payload["include_pdf"] else None,
                attachment_filename=pdf_filename,
            )
            dispatch.append({"email": recipient, **delivery})
            if delivery.get("status") == "SENT":
                sent_count += 1
            else:
                failed_count += 1

        overall_status = "SENT" if failed_count == 0 else ("PARTIAL" if sent_count > 0 else "FAILED")
        response = {
            "briefing_id": briefing_id,
            "generated_at": _now_z(),
            "subject": subject,
            "highlights": lines[4:10],
            "recommended_actions": lines[-4:] if payload["include_recommendations"] else [],
            "pdf_report": report_info,
            "email_dispatch": {
                "provider": provider,
                "status": overall_status,
                "sent_count": sent_count,
                "failed_count": failed_count,
                "recipients": dispatch,
            },
        }
        return jsonify(response), 200
    except ValidationError as exc:
        return jsonify({"success": False, "error": "Validation failed", "details": exc.messages}), 400
    except Exception as exc:
        current_app.logger.error(f"generate_briefing error: {exc}")
        return jsonify({"success": False, "error": "Failed to generate executive briefing"}), 500


@bp.route("/integrations/connectors", methods=["GET"])
@limiter.limit("120 per minute")
def list_connectors():
    suite = request.args.get("suite")
    connectors = CONNECTOR_CATALOG
    if suite:
        connectors = [c for c in connectors if c["suite"].lower() == suite.lower()]

    return jsonify(
        {
            "generated_at": _now_z(),
            "count": len(connectors),
            "supports_oauth2": True,
            "supports_sso": {"saml": True, "oidc": True},
            "connectors": connectors,
        }
    ), 200


@bp.route("/integrations/connectors/<connector_id>/authorize", methods=["POST"])
@limiter.limit("60 per minute")
def authorize_connector(connector_id: str):
    try:
        payload = ConnectorAuthSchema().load(request.get_json(silent=True) or {})
        connector = next((item for item in CONNECTOR_CATALOG if item["id"] == connector_id), None)
        if not connector:
            return jsonify({"success": False, "error": "Connector not found"}), 404

        state = uuid.uuid4().hex
        scope = payload["scopes"] or ["read", "write", "admin:alerts"]
        return jsonify(
            {
                "connector_id": connector_id,
                "tenant_id": payload["tenant_id"],
                "authorization_url": (
                    f"https://auth.scmirn.local/{connector_id}/oauth/authorize"
                    f"?client_id=scmirn-enterprise&redirect_uri={payload['redirect_uri']}"
                    f"&state={state}"
                ),
                "state": state,
                "scope": scope,
                "sso_profiles": {"saml": connector["auth"]["saml"], "oidc": connector["auth"]["oidc"]},
            }
        ), 200
    except ValidationError as exc:
        return jsonify({"success": False, "error": "Validation failed", "details": exc.messages}), 400
    except Exception as exc:
        current_app.logger.error(f"authorize_connector error: {exc}")
        return jsonify({"success": False, "error": "Failed to authorize connector"}), 500


@bp.route("/ai/multimodal/capabilities", methods=["GET"])
@limiter.limit("120 per minute")
def multimodal_capabilities():
    return jsonify(
        {
            "generated_at": _now_z(),
            "document_intelligence": {
                "supported_inputs": ["handwritten_forms", "pdf", "images", "voice_memos"],
                "ocr": True,
                "nlp_entity_extraction": True,
            },
            "video_analytics": {
                "supported_use_cases": ["pothole_severity", "traffic_violations", "crowd_risk_estimation"],
                "real_time_inference": True,
            },
            "voice_ai": {
                "ivr_automation": True,
                "languages_supported": 50,
                "handoff_to_human": True,
            },
            "predictive_maintenance_vision": {
                "imagery_sources": ["drone", "satellite", "fixed_camera"],
                "decay_detection": True,
            },
            "workflow_engine": {
                "smart_routing": True,
                "escalation_prediction": True,
                "auto_resolution_target_percent": 40,
                "cross_department_orchestration": True,
            },
            "legal_ai": {
                "case_index_size": "10M+",
                "judge_analytics": True,
                "compliance_frameworks": 500,
                "contract_generator": True,
            },
        }
    ), 200


@bp.route("/automation/workflow/route-issue", methods=["POST"])
@limiter.limit("90 per minute")
def workflow_route_issue():
    try:
        payload = WorkflowRouteSchema().load(request.get_json(silent=True) or {})
        category = payload["category"].strip().lower()
        severity = payload["severity"].strip().upper()
        affected = int(payload["affected_citizens"])
        legal_keywords = [kw.lower() for kw in payload["legal_keywords"]]

        category_department = {
            "water": "WATER_WORKS",
            "water_leak": "WATER_WORKS",
            "power": "ELECTRIC_UTILITY",
            "road": "PUBLIC_WORKS",
            "sanitation": "SOLID_WASTE",
            "safety": "PUBLIC_SAFETY",
            "cyber": "CITY_CYBER_COMMAND",
            "permit": "URBAN_DEVELOPMENT",
        }
        department = category_department.get(category, "CITY_OPERATIONS")

        severity_score = {"LOW": 20, "MEDIUM": 45, "HIGH": 70, "CRITICAL": 88}.get(severity, 45)
        impact_score = min(100, int(round(math.log10(max(10, affected)) * 24)))
        legal_score = 18 if legal_keywords else 4
        escalation_probability = min(0.98, (severity_score * 0.006) + (impact_score * 0.004) + (legal_score * 0.008))

        priority_score = int(round(min(100.0, severity_score * 0.46 + impact_score * 0.34 + legal_score * 0.2)))
        auto_resolve = severity in {"LOW", "MEDIUM"} and escalation_probability < 0.45

        orchestration = [department]
        if category in {"water_leak", "road", "power"}:
            orchestration.extend(["PUBLIC_SAFETY", "TRAFFIC_CONTROL"])
        if escalation_probability >= 0.6:
            orchestration.append("LEGAL_AFFAIRS")

        return jsonify(
            {
                "issue_id": payload["issue_id"] or str(uuid.uuid4()),
                "assigned_department": department,
                "priority_score": priority_score,
                "sla_target_hours": 2 if priority_score >= 80 else (8 if priority_score >= 60 else 24),
                "escalation_prediction": {
                    "probability": round(escalation_probability, 3),
                    "risk_band": "HIGH" if escalation_probability >= 0.7 else ("MEDIUM" if escalation_probability >= 0.4 else "LOW"),
                },
                "auto_resolution": {
                    "eligible": auto_resolve,
                    "strategy": "chatbot_intake + automated_ticketing + citizen_status_updates" if auto_resolve else "human_triage_required",
                },
                "cross_department_orchestration": list(dict.fromkeys(orchestration)),
            }
        ), 200
    except ValidationError as exc:
        return jsonify({"success": False, "error": "Validation failed", "details": exc.messages}), 400
    except Exception as exc:
        current_app.logger.error(f"workflow_route_issue error: {exc}")
        return jsonify({"success": False, "error": "Failed to route issue"}), 500


@bp.route("/legal/precedent-analysis", methods=["POST"])
@limiter.limit("60 per minute")
def precedent_analysis():
    try:
        payload = LegalAnalysisSchema().load(request.get_json(silent=True) or {})
        facts = payload["case_facts"]
        seed = int(hashlib.sha256(facts.encode("utf-8")).hexdigest()[:10], 16)

        winning_probability = round(_clamp(_noise(seed, 1, 0.35, 0.84), 0.05, 0.95), 3)
        frameworks_checked = int(round(_noise(seed, 2, 510.0, 640.0)))
        top_cases = []
        for index in range(1, 4):
            top_cases.append(
                {
                    "citation": f"{payload['jurisdiction']}-HC-{2015 + index}-{seed % 9999}",
                    "similarity": round(_noise(seed, index + 10, 0.62, 0.94), 3),
                    "outcome": "PETITION_ALLOWED" if index % 2 == 1 else "PARTIAL_RELIEF",
                }
            )

        return jsonify(
            {
                "generated_at": _now_z(),
                "legal_domain": payload["legal_domain"],
                "precedent_index_scanned": "10M+",
                "top_precedents": top_cases,
                "judge_analytics": {
                    "judge_name": payload["judge_name"],
                    "estimated_petitioner_success_probability": winning_probability,
                    "confidence": round(_noise(seed, 4, 0.58, 0.89), 3),
                },
                "compliance_monitor": {
                    "frameworks_checked": frameworks_checked,
                    "violations_detected": int(round(_noise(seed, 5, 0.0, 6.0))),
                    "regimes": ["SOC2_TYPE_II", "ISO_27001", "GDPR", "CCPA"],
                },
                "contract_generator": {
                    "supported_templates": ["MOU", "VENDOR_CONTRACT", "INTER_DEPARTMENTAL_AGREEMENT"],
                    "draft_id": str(uuid.uuid4()),
                },
            }
        ), 200
    except ValidationError as exc:
        return jsonify({"success": False, "error": "Validation failed", "details": exc.messages}), 400
    except Exception as exc:
        current_app.logger.error(f"precedent_analysis error: {exc}")
        return jsonify({"success": False, "error": "Failed to analyze legal precedents"}), 500


@bp.route("/blockchain/trust-layer/status", methods=["GET"])
@limiter.limit("120 per minute")
def trust_layer_status():
    seed = _today_seed(request.args.get("city_id", "metro-demo"))
    audited_events = int(round(_noise(seed, 90, 120_000.0, 850_000.0)))
    smart_contracts = int(round(_noise(seed, 91, 40.0, 560.0)))
    return jsonify(
        {
            "generated_at": _now_z(),
            "immutable_audit_trail": {
                "network": "Hyperledger Fabric",
                "events_logged": audited_events,
                "tamper_detection": True,
            },
            "smart_contract_marketplace": {
                "active_templates": smart_contracts,
                "categories": ["procurement", "hiring", "permits", "service-level"],
            },
            "zero_knowledge_proofs": {"credential_verification_enabled": True, "privacy_preserving_attestations": True},
            "tokenized_incentives": {"municipal_bond_tokens_enabled": True, "citizen_rewards_enabled": True},
            "supply_chain_transparency": {"tracking_coverage_percent": round(_noise(seed, 92, 72.0, 97.0), 2)},
            "compliance_reporting": {"soc2_type_ii": "ALIGNED", "iso_27001": "ALIGNED", "gdpr": "ALIGNED", "ccpa": "ALIGNED"},
        }
    ), 200


@bp.route("/security/kill-switch", methods=["POST"])
@limiter.limit("30 per minute")
def kill_switch():
    try:
        payload = KillSwitchSchema().load(request.get_json(silent=True) or {})
        isolated = []
        for node_id in payload["node_ids"]:
            isolated.append(
                {
                    "node_id": node_id,
                    "status": "ISOLATED",
                    "network_segment": f"quarantine-{hash(node_id) % 1000}",
                    "forensics_snapshot_id": str(uuid.uuid4()),
                }
            )

        return jsonify(
            {
                "activation_id": str(uuid.uuid4()),
                "triggered_at": _now_z(),
                "compromise_type": payload["compromise_type"],
                "isolated_nodes": isolated,
                "preserved_services": payload["preserve_services"],
                "containment": {
                    "zero_trust_reauth_enforced": True,
                    "air_gapped_backup_checkpointed": True,
                    "evidence_chain_of_custody": "ACTIVE",
                },
                "incident_response": {"next_actions": ["Run forensic triage", "Notify SOC command", "Patch vulnerable segment"]},
            }
        ), 200
    except ValidationError as exc:
        return jsonify({"success": False, "error": "Validation failed", "details": exc.messages}), 400
    except Exception as exc:
        current_app.logger.error(f"kill_switch error: {exc}")
        return jsonify({"success": False, "error": "Failed to activate kill switch"}), 500


@bp.route("/citizen-experience/super-app", methods=["GET"])
@limiter.limit("120 per minute")
def citizen_super_app():
    return jsonify(
        {
            "generated_at": _now_z(),
            "super_app": {
                "services_unified": True,
                "voice_first": {"wake_phrase": "Hey City", "languages_supported": 50},
                "ar_civic_layer": {"enabled": True, "overlays": ["permits", "violations", "service_history"]},
                "ai_concierge": {"personalized_recommendations": True, "proactive_alerts": True},
                "offline_first": True,
                "accessibility": {"wcag_level": "2.1 AAA", "screen_reader_optimized": True, "cognitive_support": True},
            },
            "gamification": {
                "civic_streaks": True,
                "neighborhood_leaderboards": True,
                "skill_based_volunteering": True,
            },
        }
    ), 200


@bp.route("/insights/policy-playground/simulate", methods=["POST"])
@limiter.limit("60 per minute")
def policy_playground_simulate():
    try:
        payload = PolicyPlaygroundSchema().load(request.get_json(silent=True) or {})
        districts = payload["target_districts"]
        horizon = int(payload["horizon_months"])
        size_factor = max(1.0, math.log2(1 + len(districts)))

        base_response_time = 42.0 / size_factor
        variant_a_gain = 1.0 + _clamp(len(payload["variant_a"]) * 0.04, 0.02, 0.24)
        variant_b_gain = 1.0 + _clamp(len(payload["variant_b"]) * 0.04, 0.03, 0.3)

        return jsonify(
            {
                "simulation_id": str(uuid.uuid4()),
                "policy_name": payload["policy_name"],
                "horizon_months": horizon,
                "digital_twin_scope": districts,
                "ab_test_results": {
                    "variant_a": {
                        "predicted_resolution_time_hours": round(base_response_time / variant_a_gain, 2),
                        "predicted_operating_cost_savings_percent": round(8.0 * variant_a_gain, 2),
                        "citizen_satisfaction_delta_percent": round(4.2 * variant_a_gain, 2),
                    },
                    "variant_b": {
                        "predicted_resolution_time_hours": round(base_response_time / variant_b_gain, 2),
                        "predicted_operating_cost_savings_percent": round(8.4 * variant_b_gain, 2),
                        "citizen_satisfaction_delta_percent": round(4.6 * variant_b_gain, 2),
                    },
                },
                "causal_insights": [
                    "Cross-department orchestration reduces duplicate field dispatch.",
                    "Proactive communication drives lower escalation volume.",
                    "Preventive maintenance spend lowers emergency response cost variance.",
                ],
            }
        ), 200
    except ValidationError as exc:
        return jsonify({"success": False, "error": "Validation failed", "details": exc.messages}), 400
    except Exception as exc:
        current_app.logger.error(f"policy_playground_simulate error: {exc}")
        return jsonify({"success": False, "error": "Failed to run policy playground simulation"}), 500


@bp.route("/operations/sla", methods=["GET"])
@limiter.limit("120 per minute")
def operations_sla():
    return jsonify(
        {
            "generated_at": _now_z(),
            "slo": {"uptime_target_percent": 99.999, "active_active_regions": 3},
            "autoscaling": {"spike_capacity_multiplier": 10, "status": "READY"},
            "chaos_engineering": {"enabled": True, "last_drill_at": (datetime.now(timezone.utc) - timedelta(days=8)).isoformat().replace("+00:00", "Z")},
            "feature_flags": {"canary_rollout_percent": 1, "instant_rollback": True},
            "aiops": {"self_healing_enabled": True, "mean_time_to_detect_minutes": 1.8, "mean_time_to_recover_minutes": 4.2},
        }
    ), 200


@bp.route("/multi-tenant/templates", methods=["GET"])
@limiter.limit("120 per minute")
def multi_tenant_templates():
    return jsonify(
        {
            "generated_at": _now_z(),
            "city_as_template": {"provisioning_time_hours": 48, "template_count": 12},
            "white_label_branding": {"logo_theme_overrides": True, "terminology_overrides": True},
            "federated_network": {"enabled": True, "anonymized_benchmarking": True, "leaderboards": True},
            "inter_city_coordination": {"regional_incident_rooms": True, "shared_mutual_aid_protocols": True},
            "templates": [
                {"template_id": "metro_enterprise_v1", "target_population": "1M-10M", "compliance_pack": ["SOC2", "ISO27001"]},
                {"template_id": "state_capital_v1", "target_population": "500k-3M", "compliance_pack": ["SOC2", "GDPR", "CCPA"]},
                {"template_id": "rural_cluster_v1", "target_population": "100k-800k", "compliance_pack": ["ISO27001"]},
            ],
        }
    ), 200


@bp.route("/revenue/model", methods=["GET"])
@limiter.limit("120 per minute")
def revenue_model():
    citizens = request.args.get("citizens", default=2_500_000, type=int)
    cities = request.args.get("cities", default=25, type=int)

    saas = round(cities * 1_800_000.0, 2)
    tx_fees = round(citizens * 120.0 * 0.005, 2)
    data_insights = round(cities * 620_000.0, 2)
    consulting = round(cities * 430_000.0, 2)
    marketplace = round(cities * 180_000.0, 2)
    grants = round(cities * 300_000.0, 2)
    total = round(saas + tx_fees + data_insights + consulting + marketplace + grants, 2)

    return jsonify(
        {
            "generated_at": _now_z(),
            "assumptions": {"citizens": citizens, "cities": cities},
            "revenue_streams_inr_year": {
                "saas_subscriptions": saas,
                "transaction_fees": tx_fees,
                "data_insights": data_insights,
                "consulting_services": consulting,
                "marketplace_commission": marketplace,
                "grants_and_impact_bonds": grants,
                "total": total,
            },
            "unit_economics": {
                "gross_margin_percent": 68.5,
                "payback_months_enterprise_client": 14,
                "net_revenue_retention_percent": 124,
            },
        }
    ), 200
