"""
Digital Twin Simulation (v1).

Implements:
 - POST /api/v1/twin/simulate

Runs a lightweight Monte Carlo simulation and returns scenario KPIs with
confidence intervals. This is intended as a functional baseline.
"""

from __future__ import annotations

from datetime import datetime, timezone
import random
import statistics
import uuid
from typing import Any, Dict, List, Tuple

from flask import Blueprint, jsonify, request, current_app
from marshmallow import Schema, fields, validate, ValidationError

from app.extensions import limiter


bp = Blueprint("api_v1_twin", __name__, url_prefix="/api/v1/twin")


class SimulationRequestSchema(Schema):
    twin_id = fields.Str(required=True)
    scenario_type = fields.Str(required=True, validate=validate.OneOf([
        "EXTREME_WEATHER",
        "POPULATION_GROWTH",
        "INFRASTRUCTURE_FAILURE",
        "POLICY_CHANGE",
    ]))
    parameters = fields.Dict(load_default=dict)
    kpis = fields.List(fields.Str(), load_default=list)


class SimulateSchema(Schema):
    simulation_request = fields.Nested(SimulationRequestSchema(), required=True)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


@bp.route("/simulate", methods=["POST"])
@limiter.limit("30 per minute")
def simulate():
    """
    POST /api/v1/twin/simulate
    """
    try:
        schema = SimulateSchema()
        body = schema.load(request.get_json() or {})
        req = body["simulation_request"]

        scenario = req["scenario_type"]
        params = req.get("parameters") or {}
        iterations = int(params.get("iterations") or 2000)
        iterations = max(500, min(iterations, 10000))

        duration_hours = float(params.get("duration_hours") or 24)
        affected_area_percent = float(params.get("affected_area_percent") or 25.0)
        magnitude = str(params.get("event_magnitude") or "MEDIUM").upper()

        # Baselines
        base_service_continuity = 92.0
        base_recovery_hours = 18.0
        base_cost_inr = 2_500_000.0
        base_population_affected = int(20000 * (affected_area_percent / 100.0))

        # Scenario multipliers
        mag_factor = {"LOW": 0.8, "MEDIUM": 1.0, "HIGH": 1.25, "EXTREME": 1.6}.get(magnitude, 1.0)
        scenario_factor = {
            "EXTREME_WEATHER": 1.35,
            "POPULATION_GROWTH": 1.10,
            "INFRASTRUCTURE_FAILURE": 1.25,
            "POLICY_CHANGE": 0.95,
        }.get(scenario, 1.0)

        cont_vals = []
        cost_vals = []
        pop_vals = []
        rec_vals = []
        res_vals = []

        for _ in range(iterations):
            # Random uncertainty terms
            u1 = random.uniform(-1.0, 1.0)
            u2 = random.uniform(-1.0, 1.0)
            u3 = random.uniform(-1.0, 1.0)

            impact = mag_factor * scenario_factor * (1.0 + 0.12 * u1)
            duration_factor = (duration_hours / 24.0) ** 0.35

            service_continuity = max(15.0, min(99.5, base_service_continuity - (impact * 18.0 * duration_factor) + (u2 * 2.0)))
            recovery_time = max(1.0, base_recovery_hours * impact * duration_factor + (u3 * 3.0))
            cost = max(50_000.0, base_cost_inr * impact * duration_factor * (1.0 + 0.18 * u2))
            population = int(max(0, base_population_affected * impact * (1.0 + 0.15 * u3)))

            # Resilience score out of 100 (higher is better)
            resilience = max(0.0, min(100.0, (service_continuity * 0.7) + (max(0.0, 100 - recovery_time) * 0.3)))

            cont_vals.append(service_continuity)
            cost_vals.append(cost)
            pop_vals.append(population)
            rec_vals.append(recovery_time)
            res_vals.append(resilience)

        cont_exp = float(round(statistics.mean(cont_vals), 2))
        cost_exp = float(round(statistics.mean(cost_vals), 2))
        pop_exp = int(round(statistics.mean(pop_vals)))
        rec_exp = float(round(statistics.mean(rec_vals), 2))
        res_exp = float(round(statistics.mean(res_vals), 2))

        res_ci = {"lower": float(round(_percentile(res_vals, 0.1), 2)), "upper": float(round(_percentile(res_vals, 0.9), 2))}
        cost_ci = {"min": float(round(_percentile(cost_vals, 0.1), 2)), "expected": cost_exp, "max": float(round(_percentile(cost_vals, 0.9), 2))}
        rec_ci = {"min": float(round(_percentile(rec_vals, 0.1), 2)), "expected": rec_exp, "max": float(round(_percentile(rec_vals, 0.9), 2))}

        moments = [
            {"time_hours": 2.0, "event": "Early disruptions", "consequence": "Localized service drops", "preventive_action": "Activate field monitoring + prioritize critical assets"},
            {"time_hours": duration_hours / 2.0, "event": "Peak impact window", "consequence": "Highest load + failure probability", "preventive_action": "Load shedding + emergency repairs"},
            {"time_hours": duration_hours, "event": "Stabilization", "consequence": "Recovery operations start", "preventive_action": "Mutual aid + spare parts dispatch"},
        ]

        return jsonify({
            "simulation_id": str(uuid.uuid4()),
            "status": "COMPLETED",
            "results": {
                "summary": {
                    "scenario_name": scenario,
                    "probability_of_occurrence": float(round(0.08 * scenario_factor * mag_factor, 3)),
                    "overall_resilience_score": float(round(res_exp, 2)),
                    "confidence_interval": res_ci,
                },
                "kpis": {
                    "service_continuity_percent": cont_exp,
                    "estimated_cost_inr": cost_ci,
                    "population_affected": pop_exp,
                    "recovery_time_hours": rec_ci,
                },
                "critical_moments": moments,
                "resource_requirements": {
                    "emergency_personnel": int(max(10, round(pop_exp / 2000))),
                    "equipment": ["portable_pumps", "generators", "medical_kits"],
                    "budget_reserve_inr": float(round(cost_ci["expected"] * 0.12, 2)),
                },
                "mitigation_strategies": [
                    {"intervention": "Pre-position spare parts in high-risk wards", "cost_inr": 250000.0, "effectiveness_percent": 18.0, "implementation_time_months": 2, "priority": "HIGH"},
                    {"intervention": "Upgrade monitoring + alerts for transformers and pumps", "cost_inr": 420000.0, "effectiveness_percent": 12.0, "implementation_time_months": 3, "priority": "MEDIUM"},
                ],
            },
            "visualization_data": {
                "time_series": [{"hour": int(h), "metric": float(round(max(0.0, cont_exp - h * 0.2), 2))} for h in range(0, int(min(48, duration_hours)) + 1, 4)],
                "heatmaps": [],
                "network_stress": {"nodes": [], "edges": []},
            },
            "recommendations": {
                "immediate_actions": ["Activate resilience hubs", "Prioritize critical loads", "Dispatch crews to hotspot clusters"],
                "short_term_planning": ["Run weekly drills", "Improve spare parts inventory", "Improve citizen communication channels"],
                "long_term_investments": ["Grid hardening", "Drainage upgrades", "Sensor coverage expansion"],
                "policy_changes": ["Define service continuity SLAs", "Mandate audit logs for emergency procurement"],
            },
        }), 200

    except ValidationError as e:
        return jsonify({"success": False, "error": "Validation failed", "details": e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"twin simulate error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to run simulation"}), 500

