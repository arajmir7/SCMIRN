"""
City-brain endpoints that operationalize the full SCMIRN vision as executable
simulation APIs for the website.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import math
import uuid

from flask import Blueprint, current_app, jsonify, request

from app.extensions import limiter


bp = Blueprint("api_v1_city_brain", __name__, url_prefix="/api/v1/city-brain")


def _now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _body() -> dict:
    return request.get_json(silent=True) or {}


def _text(value: object, default: str) -> str:
    txt = str(value).strip() if value is not None else default
    return txt or default


def _num(value: object, default: float, low: float | None = None, high: float | None = None) -> float:
    try:
        out = float(value)
    except Exception:
        out = float(default)
    if low is not None:
        out = max(low, out)
    if high is not None:
        out = min(high, out)
    return out


def _int(value: object, default: int, low: int | None = None, high: int | None = None) -> int:
    try:
        out = int(value)
    except Exception:
        out = int(default)
    if low is not None:
        out = max(low, out)
    if high is not None:
        out = min(high, out)
    return out


def _u(seed: str) -> float:
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    n = int(h[:12], 16)
    return n / float(16**12 - 1)


def _sf(seed: str, low: float, high: float, digits: int = 2) -> float:
    return round(low + _u(seed) * (high - low), digits)


def _si(seed: str, low: int, high: int) -> int:
    return int(low + math.floor(_u(seed) * (high - low + 1)))


def _band(score: float) -> str:
    if score >= 0.8:
        return "CRITICAL"
    if score >= 0.6:
        return "HIGH"
    if score >= 0.35:
        return "MEDIUM"
    return "LOW"


@bp.route("/sensing/quantum-mesh/status", methods=["GET"])
@limiter.limit("120 per minute")
def quantum_mesh_status():
    try:
        zone = _text(request.args.get("zone"), "WARD-11").upper()
        detections = []
        for idx in range(1, 4):
            seed = f"{zone}:{idx}"
            risk = _sf(f"{seed}:risk", 0.12, 0.95)
            hrs = _si(f"{seed}:hrs", 12, 72) if risk >= 0.75 else _si(f"{seed}:hrs", 72, 360)
            detections.append(
                {
                    "asset_id": f"{zone}-QNM-{idx:02d}",
                    "risk_score": risk,
                    "risk_band": _band(risk),
                    "predicted_failure_window_hours": hrs,
                    "micro_strain": _sf(f"{seed}:strain", 0.03, 0.65, 3),
                }
            )
        return jsonify(
            {
                "zone": zone,
                "quantum_neural_mesh": {
                    "sensed_points": _si(f"{zone}:pts", 2500, 22000),
                    "fiber_backbone_km": _sf(f"{zone}:fiber", 25.0, 240.0, 1),
                    "modalities": ["temperature", "strain", "vibration", "em_field"],
                    "quantum_ghost_imaging": {
                        "enabled": True,
                        "subsurface_resolution_mm": _sf(f"{zone}:ghost", 0.02, 0.35, 3),
                    },
                    "self_calibration": {"enabled": True, "last_compensation": _now_z()},
                },
                "predictive_failure_signatures": detections,
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"quantum_mesh_status error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to compute quantum mesh status"}), 500


@bp.route("/sensing/ambient-intelligence/simulate", methods=["POST"])
@limiter.limit("60 per minute")
def ambient_intelligence_simulate():
    try:
        body = _body()
        signals = body.get("signals") or {}
        hr = _num(signals.get("avg_heart_rate_bpm"), 82, 40, 200)
        noise = _num(signals.get("acoustic_stress_db"), 58, 20, 130)
        footfall = _num(signals.get("footfall_density_per_min"), 24, 0, 300)
        rain = _num(signals.get("rain_risk"), 0.2, 0, 1)
        hour = _int(signals.get("current_hour_local"), 12, 0, 23)
        anxiety = max(0.0, min(100.0, ((hr - 60) * 0.52) + ((noise - 40) * 0.68) + (footfall * 0.42)))
        return jsonify(
            {
                "neighborhood_id": _text(body.get("neighborhood_id"), "WARD-11").upper(),
                "ambient_state": {
                    "anxiety_index": round(anxiety, 1),
                    "streetlight_response": {
                        "target_lux": int(round(max(25.0, min(100.0, 95.0 - anxiety * 0.55)))),
                        "mode": "CALMING" if anxiety >= 55 else "STANDARD",
                    },
                    "collective_memory": {
                        "reinforcement_priority": _band(min(0.95, anxiety / 100.0 + footfall / 250.0)),
                        "surface_texture": "GRIPPY" if rain >= 0.55 else ("SMOOTH" if anxiety <= 35 else "BALANCED"),
                    },
                    "dream_mode": {
                        "active": 2 <= hour < 4,
                        "window_local": "02:00-04:00",
                    },
                },
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"ambient_intelligence_simulate error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to simulate ambient intelligence"}), 500


@bp.route("/autonomy/robotic-swarms/dispatch", methods=["POST"])
@limiter.limit("60 per minute")
def robotic_swarms_dispatch():
    try:
        body = _body()
        incident = _text(body.get("incident_type"), "POTHOLE").upper()
        crack = _num(body.get("crack_width_mm"), 0.2, 0, 50)
        pressure = _num(body.get("pressure_drop_percent"), 0, 0, 100)
        water = _num(body.get("water_level_cm"), 0, 0, 500)
        catalog = {
            "POTHOLE": [("ARRES Ultra", "Rapid asphalt repair", 8), ("Aerial Sentinel", "Vision verification", 6)],
            "PIPE_LEAK": [("Subterranean Worm", "Pipe inspection + seal", 14), ("Bio-Synthesizer", "Micro-concrete print", 18)],
            "BRIDGE_CRACK": [("Aerial Sentinel", "Crack mapping", 7), ("Bio-Synthesizer", "Precision deposition", 16)],
            "FLOODING": [("Aerial Sentinel", "Flood contour mapping", 5), ("Vertiport Custodian", "Emergency corridor setup", 12)],
            "GRID_FAULT": [("Vertiport Custodian", "Power relay stabilization", 10), ("ARRES Ultra", "Surface isolation support", 12)],
        }
        robots = catalog.get(incident, catalog["POTHOLE"])
        severity = max(0.0, min(100.0, crack * 140.0 + pressure * 0.65 + water * 0.18))
        return jsonify(
            {
                "dispatch_id": str(uuid.uuid4()),
                "incident_type": incident,
                "severity_score": round(severity, 1),
                "swarm_plan": [
                    {
                        "robot_type": r[0],
                        "task": r[1],
                        "eta_minutes": int(max(3, round(r[2] - min(3.0, severity / 30.0)))),
                    }
                    for r in robots
                ],
                "human_robot_teaming": {
                    "exoskeleton_support_required": severity >= 52.0,
                    "global_learn_latency_seconds": 90,
                },
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"robotic_swarms_dispatch error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to dispatch robotic swarm"}), 500


@bp.route("/autonomy/self-healing-materials/plan", methods=["POST"])
@limiter.limit("60 per minute")
def self_healing_materials_plan():
    try:
        body = _body()
        mtype = _text(body.get("material_type"), "BACTERIAL_BIOCONCRETE").upper()
        crack = _num(body.get("crack_width_mm"), 0.25, 0, 20)
        water = bool(body.get("water_intrusion", False))
        if mtype == "BACTERIAL_BIOCONCRETE":
            days = int(round(max(5.0, min(30.0, 7 + crack * 10 + (0 if water else 2)))))
            agent = "Bacillus + Ca-lactate nutrient capsule"
        elif mtype == "VASCULAR_NETWORK":
            days = int(round(max(3.0, min(21.0, 4 + crack * 6))))
            agent = "Two-part polymer through vascular channels"
        else:
            days = int(round(max(1.0, min(14.0, 2 + crack * 4))))
            agent = "Programmable micro-actuator reconfiguration"
        return jsonify(
            {
                "plan_id": str(uuid.uuid4()),
                "material_type": mtype,
                "healing_strategy": {
                    "primary_agent": agent,
                    "estimated_healing_days": days,
                    "expected_strength_recovery_percent": round(max(55.0, min(98.0, 76 + (1.0 - crack) * 18)), 1),
                },
                "adaptive_surface": {"texture_mode": "GRIPPY" if water else "SMOOTH"},
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"self_healing_materials_plan error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to create self-healing plan"}), 500


@bp.route("/immersive/metaverse/townhall", methods=["POST"])
@limiter.limit("30 per minute")
def metaverse_townhall():
    try:
        body = _body()
        title = _text(body.get("proposal_title"), "Flood-resilient bridge corridor")
        years = _int(body.get("horizon_years"), 10, 1, 30)
        base = _sf(title, 0.08, 0.4, 3)
        return jsonify(
            {
                "session_id": str(uuid.uuid4()),
                "proposal_title": title,
                "mirror_world": {
                    "policy_time_travel_horizon_years": years,
                    "traffic_flow_change_percent": round(-12.0 + base * 40.0, 1),
                    "accessibility_score": round(min(100.0, 62 + (20 if bool(body.get("accessibility_focus", True)) else 6)), 1),
                },
                "gamified_stewardship": {"resilience_raiders_points_pool": _si(title + ":tokens", 12000, 180000)},
                "spatial_command_center": {"gesture_commands_enabled": True},
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"metaverse_townhall error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to run metaverse townhall"}), 500


@bp.route("/immersive/generative-urban-design", methods=["POST"])
@limiter.limit("30 per minute")
def generative_urban_design():
    try:
        body = _body()
        prompt = _text(body.get("prompt"), "Design a flood-resilient public park with 50kW solar.")
        constraints = body.get("constraints") or {}
        did = str(uuid.uuid4())
        cap = _num(constraints.get("budget_cap_inr"), 30_000_000, 5_000_000, 500_000_000)
        return jsonify(
            {
                "design_id": did,
                "prompt": prompt,
                "proposal": {
                    "concept_name": f"Urban Concept {did[:8]}",
                    "cad_bundle": f"/mock/cad/{did}.zip",
                    "construction_timeline_days": _int(_sf(prompt + ":dur", 90, 420), 180, 45, 540),
                    "estimated_cost_inr": round(cap * _sf(prompt + ":cost", 0.72, 1.08, 3), 2),
                    "solar_generation_kw": _num(constraints.get("target_solar_kw"), 50, 5, 500),
                },
                "predictive_zoning": {"recommended_zone_change": "MIXED_USE_RESILIENCE", "confidence": _sf(prompt + ":zone", 0.62, 0.93)},
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"generative_urban_design error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to generate urban design"}), 500


@bp.route("/depin/tokenize-asset", methods=["POST"])
@limiter.limit("60 per minute")
def depin_tokenize_asset():
    try:
        body = _body()
        aid = _text(body.get("asset_id"), "asset-001")
        atype = _text(body.get("asset_type"), "STREETLIGHT")
        valuation = _num(body.get("valuation_inr"), 1_500_000, 1000)
        units = _int(body.get("fractional_units"), 1000, 10, 10_000_000)
        performance = _num(body.get("performance_score"), 78, 0, 100)
        return jsonify(
            {
                "tokenization": {
                    "nft_id": f"infra-{aid}",
                    "asset_type": atype,
                    "valuation_inr": valuation,
                    "fractional_units": units,
                    "unit_price_inr": round(valuation / max(1, units), 2),
                },
                "proof_of_resilience": {
                    "maintenance_mining_enabled": True,
                    "staking_slash_if_failure_percent": round(max(2.0, min(15.0, 12.0 - performance * 0.08)), 2),
                    "resilience_dividend_yield_percent": round(max(1.0, min(10.5, 1.2 + (performance / 100.0) * 7.5)), 2),
                },
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"depin_tokenize_asset error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to tokenize infrastructure asset"}), 500


@bp.route("/depin/governance/iip", methods=["POST"])
@limiter.limit("60 per minute")
def depin_governance_iip():
    try:
        body = _body()
        supporters = _int(body.get("supporters"), 100, 1, 1_000_000)
        avg = _num(body.get("avg_donation_inr"), 100, 1)
        cap = _num(body.get("city_match_cap_inr"), 5_000_000, 1000)
        budget = _num(body.get("requested_budget_inr"), 2_000_000, 1000)
        community = round(supporters * avg, 2)
        match = round(min(cap, (math.sqrt(max(1, supporters)) * avg * 8.0)), 2)
        pool = round(community + match, 2)
        return jsonify(
            {
                "proposal_id": str(uuid.uuid4()),
                "title": _text(body.get("title"), "Neighborhood resilience upgrade"),
                "governance": {
                    "voting_model": "LIQUID_DEMOCRACY",
                    "vote_window_days": 14,
                    "quadratic_funding": {"community_contribution_inr": community, "city_match_inr": match, "total_pool_inr": pool},
                    "funded_ratio": round(max(0.0, min(2.0, pool / max(1.0, budget))), 3),
                },
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"depin_governance_iip error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to evaluate governance proposal"}), 500


@bp.route("/energy/living-ecosystem/status", methods=["GET"])
@limiter.limit("120 per minute")
def living_energy_status():
    try:
        zone = _text(request.args.get("zone"), "WARD-11").upper()
        solar = _sf(zone + ":solar", 320.0, 1400.0, 1)
        algae = _sf(zone + ":algae", 40.0, 210.0, 1)
        kinetic = _sf(zone + ":kinetic", 12.0, 120.0, 1)
        total = round(solar + algae + kinetic, 1)
        demand = _sf(zone + ":demand", 420.0, 1550.0, 1)
        reserve = _sf(zone + ":reserve", 18.0, 92.0, 1)
        return jsonify(
            {
                "zone": zone,
                "generation_kw": {"photosynthetic_surfaces": solar, "algae_bioreactors": algae, "kinetic_tiles": kinetic, "total": total},
                "swarm_grid": {
                    "distributed_nodes": _si(zone + ":nodes", 600, 4800),
                    "islanding_mode": reserve < 30.0 or total < demand * 0.45,
                    "reserve_battery_percent": reserve,
                },
                "uam_micro_utilities": {"vertiports_active": _si(zone + ":vertiports", 1, 8), "rainwater_recovery_liters_day": _si(zone + ":rain", 1200, 14000)},
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"living_energy_status error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to compute living energy status"}), 500


@bp.route("/bio-integrated/assessment", methods=["POST"])
@limiter.limit("60 per minute")
def bio_integrated_assessment():
    try:
        body = _body()
        pollution = _num(body.get("soil_pollution_index"), 45, 0, 100)
        rain = _num(body.get("rainfall_mm"), 120, 0, 2000)
        slope = _num(body.get("slope_percent"), 4, 0, 80)
        return jsonify(
            {
                "site_type": _text(body.get("site_type"), "URBAN_CORE").upper(),
                "mycelium_networks": {
                    "bioremediation_priority_percent": round(max(5.0, min(95.0, pollution * 0.6 + slope * 0.8)), 1),
                    "predicted_sinkhole_risk_reduction_percent": round(max(5.0, min(65.0, 8.0 + slope * 0.6)), 1),
                },
                "bio_reactor_buildings": {
                    "oxygen_output_kg_day": round(max(40.0, min(680.0, 150.0 + rain * 1.4 - pollution * 0.9)), 1),
                    "carbon_negative_delta_tons_per_month": round(max(0.3, min(8.5, 1.8 + rain * 0.01 - pollution * 0.004)), 2),
                },
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"bio_integrated_assessment error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to assess bio-integrated infrastructure"}), 500


@bp.route("/resilience/antifragile-drill", methods=["POST"])
@limiter.limit("60 per minute")
def antifragile_drill():
    try:
        body = _body()
        zone = _text(body.get("target_zone"), "WARD-11").upper()
        mult = _num(body.get("stress_multiplier"), 1.0, 0.5, 3.0)
        baseline = _sf(zone + ":base", 58.0, 88.0, 1)
        post = round(max(0.0, min(99.0, baseline + max(8.0, min(66.0, mult * 22.0)) * 0.24)), 1)
        return jsonify(
            {
                "drill_id": str(uuid.uuid4()),
                "drill_type": _text(body.get("drill_type"), "FLOOD").upper(),
                "target_zone": zone,
                "stress_inoculation": {
                    "baseline_resilience_score": baseline,
                    "post_drill_resilience_score": post,
                    "improvement_percent": round(max(0.0, min(40.0, post - baseline)), 1),
                },
                "distributed_redundancy": {"single_point_failure_detected": False},
                "regenerative_capacity": {"temporary_bridge_print_ready": True, "mobile_microgrids_available": _si(zone + ":mg", 2, 18)},
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"antifragile_drill error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to run antifragile drill"}), 500


@bp.route("/interface/neuro-adaptive/respond", methods=["POST"])
@limiter.limit("60 per minute")
def neuro_adaptive_respond():
    try:
        body = _body()
        thought = _text(body.get("thought_intent"), "Need a bench nearby").lower()
        stress = _num(body.get("stress_index"), 45, 0, 100)
        if "emergency" in thought or "help" in thought:
            action = "DISPATCH_AID"
        elif "bench" in thought or "seat" in thought:
            action = "HIGHLIGHT_NEAREST_BENCH"
        elif "light" in thought or "dark" in thought:
            action = "ADJUST_LIGHTING"
        else:
            action = "OPEN_CIVIC_ASSIST"
        return jsonify(
            {
                "neighborhood_id": _text(body.get("neighborhood_id"), "WARD-11").upper(),
                "bci_interpretation": {"thought_intent": _text(body.get("thought_intent"), ""), "detected_action": action, "confidence": 0.86},
                "emotional_zoning": {
                    "stress_index": round(stress, 1),
                    "lighting_temp_kelvin": int(round(max(2700.0, min(5000.0, 4200 - stress * 12)))),
                },
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"neuro_adaptive_respond error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to process neuro-adaptive request"}), 500


@bp.route("/interface/universal-translation/translate", methods=["POST"])
@limiter.limit("90 per minute")
def universal_translation():
    try:
        body = _body()
        text = _text(body.get("human_text"), "")
        src = _text(body.get("from_language"), "en").lower()
        dst = _text(body.get("to_language"), "en").lower()
        species = body.get("species_signal")
        protocol = body.get("machine_protocol")
        translated = text if src == dst else f"[{dst}] {text}"
        eco = None
        if isinstance(species, str) and species.strip():
            ss = species.lower()
            eco = "Auto-plan pollinator strips." if ("bee" in ss or "pollinator" in ss) else "Log ecological signal for biodiversity planner."
        machine = None
        if isinstance(protocol, str) and protocol.strip():
            machine = {
                "from_protocol": protocol.upper(),
                "to_protocol": "CITYBUS-V1",
                "adapter_profile": "LEGACY_INTEROP_BRIDGE",
                "estimated_latency_ms": _si(protocol, 12, 95),
            }
        return jsonify(
            {
                "translation": {
                    "language": {"from": src, "to": dst, "output_text": translated},
                    "species": {"input_signal": species, "ecological_action": eco},
                    "machine": machine,
                    "time_bridge": {"legacy_sensor_retrosfit_supported": True},
                }
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"universal_translation error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to run universal translation"}), 500


@bp.route("/business-model/forecast", methods=["GET"])
@limiter.limit("120 per minute")
def business_model_forecast():
    try:
        households = _int(request.args.get("households"), 100_000, 1000, 20_000_000)
        raas = round(households * 420.0, 2)
        data_rev = round(households * 95.0, 2)
        carbon = round(households * 38.0, 2)
        token = round(households * 22.0, 2)
        insurance = round(households * 110.0, 2)
        licensing = round(12_000_000.0 + households * 18.0, 2)
        grants = round(25_000_000.0 + households * 30.0, 2)
        total = round(raas + data_rev + carbon + token + insurance + licensing + grants, 2)
        return jsonify(
            {
                "inputs": {"households": households},
                "revenue_streams_inr_year": {
                    "resilience_as_a_service": raas,
                    "data_monetization": data_rev,
                    "carbon_credits": carbon,
                    "token_transaction_fees": token,
                    "disaster_recovery_insurance": insurance,
                    "licensing": licensing,
                    "federal_grants": grants,
                    "total": total,
                },
                "cost_structure_effects_inr_year": {
                    "autonomous_labor_savings": round(total * 0.24, 2),
                    "predictive_maintenance_savings": round(total * 0.17, 2),
                    "community_ownership_capex_shift": round(total * 0.11, 2),
                },
            }
        ), 200
    except Exception as e:
        current_app.logger.error(f"business_model_forecast error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to compute business forecast"}), 500


@bp.route("/roadmap/status", methods=["GET"])
@limiter.limit("120 per minute")
def roadmap_status():
    try:
        start = _int(request.args.get("start_year"), 2026, 2000, 2100)
        year = _int(request.args.get("year"), datetime.now(timezone.utc).year, 2000, 2200)
        phases = [
            ("Awakening", start, start),
            ("Cognition", start + 1, start + 2),
            ("Symbiosis", start + 3, start + 5),
            ("Transcendence", start + 6, start + 9),
        ]
        items = []
        active = "UPCOMING"
        for name, lo, hi in phases:
            if year > hi:
                st = "COMPLETED"
            elif lo <= year <= hi:
                st = "ACTIVE"
                active = name
            else:
                st = "UPCOMING"
            items.append({"phase": name, "timeline": f"{lo}-{hi}", "status": st})
        return jsonify({"start_year": start, "current_year": year, "active_phase": active, "roadmap": items}), 200
    except Exception as e:
        current_app.logger.error(f"roadmap_status error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to compute roadmap status"}), 500


@bp.route("/value-proposition", methods=["GET"])
@limiter.limit("120 per minute")
def value_proposition():
    return jsonify(
        {
            "for_citizens": [
                "Near-zero infrastructure downtime",
                "Fractional ownership and resilience dividends",
                "Immersive democratic participation",
                "Safety-first proactive urban response",
            ],
            "for_governments": [
                "Lower lifecycle infrastructure cost",
                "Reduced failure and scandal risk",
                "Automated climate compliance pathways",
                "Higher investment attractiveness",
            ],
            "for_planet": [
                "Regenerative urban systems",
                "Circular water, energy, and material flows",
                "Net-negative carbon pathways",
            ],
        }
    ), 200

