"""
Resilience Hub Network (v1).

Implements:
 - GET  /api/v1/resilience/hub-status
 - POST /api/v1/resilience/request-aid
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math
import uuid
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request, current_app
from marshmallow import Schema, fields, validate, ValidationError

from app.extensions import db, limiter
from app.infrastructure.database.models import ResilienceHubORM


bp = Blueprint("api_v1_resilience", __name__, url_prefix="/api/v1/resilience")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class HubStatusSchema(Schema):
    hub_id = fields.Str(allow_none=True)


@bp.route("/hub-status", methods=["GET"])
@limiter.limit("120 per minute")
def hub_status():
    """
    GET /api/v1/resilience/hub-status?hub_id=...
    Returns the current resilience hub operational decision output.
    """
    try:
        hub_id = request.args.get("hub_id")

        hub = ResilienceHubORM.query.get(hub_id) if hub_id else ResilienceHubORM.query.first()
        if not hub:
            # Create a demo hub so the UI is immediately functional
            hub = ResilienceHubORM(
                id=str(uuid.uuid4()),
                lat=28.6139,
                lng=77.2090,
                address="Demo Community Hub, Central Ward",
                solar_generation_kw=18.5,
                battery_soc_percent=72.0,
                grid_connection="CONNECTED",
                connected_loads=json.dumps(["MEDICAL_DEVICES", "COMMUNICATIONS", "LIGHTING", "COOLING"]),
                occupancy=42,
                supplies=json.dumps({"water_liters": 1200, "food_kits": 90, "medical": "ADEQUATE"}),
                operational_mode="NORMAL",
            )
            db.session.add(hub)
            db.session.commit()

        # Determine operational mode (baseline)
        mode = hub.operational_mode or "NORMAL"
        if hub.grid_connection in {"FAILED", "ISLANDED"}:
            mode = "ISLANDED"
        if float(hub.battery_soc_percent or 100) < 25.0:
            mode = "EMERGENCY"

        power_autonomy_hours = max(1.0, float(hub.battery_soc_percent or 50) / 5.0)  # heuristic
        supplies = json.loads(hub.supplies or "{}")
        water_days = float(supplies.get("water_liters", 0)) / max(1.0, float(hub.occupancy or 1)) / 3.0
        food_days = float(supplies.get("food_kits", 0)) / max(1.0, float(hub.occupancy or 1)) / 1.0

        can_accept = mode != "EMERGENCY" and power_autonomy_hours > 6.0 and water_days > 1.0 and food_days > 1.0
        max_occ = int(max(hub.occupancy or 0, 50 if can_accept else (hub.occupancy or 0)))
        capacity = int(max(0, min(100, round((power_autonomy_hours / 24.0) * 60 + (water_days / 3.0) * 20 + (food_days / 3.0) * 20))))

        return jsonify({
            "hub_status_update": {
                "hub_id": hub.id,
                "mode": mode,
                "operational_capacity": capacity,
                "can_accept_evacuees": bool(can_accept),
                "max_occupancy": max_occ,
                "current_resources": {
                    "power_autonomy_hours": float(round(power_autonomy_hours, 1)),
                    "water_supply_days": float(round(water_days, 1)),
                    "food_supply_days": float(round(food_days, 1)),
                    "medical_kit_availability": str(supplies.get("medical", "ADEQUATE")),
                },
            },
            "public_guidance": {
                "shelter_open": bool(can_accept),
                "directions": f"Navigate to: {hub.address}",
                "what_to_bring": ["ID proof", "Essential medicines", "Water bottle", "Phone charger"],
                "restrictions": ["No open flames", "Follow on-site safety instructions"],
                "estimated_wait": "10-20 minutes",
            },
            "mutual_aid_coordination": {
                "can_provide": {
                    "power_to_grid_kw": float(round(max(0.0, float(hub.solar_generation_kw or 0) - 5.0), 1)),
                    "surplus_supplies": {"water_liters": max(0, int(supplies.get("water_liters", 0) - 600)), "food_kits": max(0, int(supplies.get("food_kits", 0) - 40))},
                    "volunteers_available": 6,
                },
                "needs_from_network": {
                    "medical_supplies": bool(str(supplies.get("medical", "ADEQUATE")).upper() in {"LOW", "CRITICAL"}),
                    "fuel": False,
                    "additional_volunteers": 0 if can_accept else 4,
                },
            },
            "volunteer_dispatch": [
                {"skill": "MEDICAL", "count_needed": 1, "location": {"lat": hub.lat, "lng": hub.lng}, "urgency": "STANDBY"},
            ],
            "iot_commands": [
                {"device": "LOAD_CONTROLLER", "action": "MODULATE", "target_value": 0.85 if mode == "EMERGENCY" else 1.0, "duration_minutes": 60},
            ],
        }), 200

    except Exception as e:
        current_app.logger.error(f"hub-status error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to compute hub status"}), 500


class AidLocationSchema(Schema):
    lat = fields.Float(required=True)
    lng = fields.Float(required=True)


class AidRequestSchema(Schema):
    requester_id = fields.Str(required=True)
    location = fields.Nested(AidLocationSchema(), required=True)
    need_category = fields.Str(required=True)
    description = fields.Str(required=True)
    urgency = fields.Str(required=True)
    time_window = fields.Str(required=True)


class VolunteerSchema(Schema):
    volunteer_id = fields.Str(required=True)
    location = fields.Nested(AidLocationSchema(), required=True)
    skills = fields.List(fields.Str(), load_default=list)
    availability = fields.Str(load_default="FLEXIBLE")
    verification_status = fields.Str(load_default="UNVERIFIED")
    rating = fields.Float(load_default=4.0)


class AidMatchSchema(Schema):
    aid_request = fields.Nested(AidRequestSchema(), required=True)
    volunteer_pool = fields.List(fields.Nested(VolunteerSchema()), required=True)


@bp.route("/request-aid", methods=["POST"])
@limiter.limit("60 per minute")
def request_aid():
    """
    POST /api/v1/resilience/request-aid
    Returns ranked volunteers with safety features and backup plan.
    """
    try:
        schema = AidMatchSchema()
        data = schema.load(request.get_json() or {})
        req = data["aid_request"]
        pool = data["volunteer_pool"]

        rlat = float(req["location"]["lat"])
        rlng = float(req["location"]["lng"])
        need = (req["need_category"] or "").upper()

        ranked = []
        for v in pool:
            vlat = float(v["location"]["lat"])
            vlng = float(v["location"]["lng"])
            dist_km = _haversine_km(rlat, rlng, vlat, vlng)

            # Distance score
            if dist_km < 0.5:
                dscore = 40
            elif dist_km < 1:
                dscore = 30
            elif dist_km < 2:
                dscore = 20
            elif dist_km < 5:
                dscore = 10
            else:
                dscore = 2

            # Skill score
            skills = [s.lower() for s in (v.get("skills") or [])]
            skill_map = {
                "MEDICAL": ["medic", "nurse", "doctor", "first aid"],
                "TRANSPORT": ["driver", "vehicle", "transport"],
                "TECHNICAL": ["electrician", "plumber", "technician", "it"],
                "FOOD": ["cook", "food"],
                "SHELTER": ["host", "shelter"],
                "EMOTIONAL": ["counsel", "psych", "support"],
            }
            desired = [x.lower() for x in skill_map.get(need, [])]
            exact = any(any(d in s for d in desired) for s in skills) if desired else False
            sscore = 30 if exact else (15 if skills else 5)

            # Availability score (baseline: flexible = 15)
            av = (v.get("availability") or "").lower()
            ascore = 20 if "exact" in av else (10 if "partial" in av else 15)

            # Trust score
            verified = (v.get("verification_status") or "UNVERIFIED").upper() == "VERIFIED"
            rating = float(v.get("rating") or 4.0)
            if verified and rating >= 4.5:
                tscore = 10
            elif verified:
                tscore = 7
            elif rating >= 4.5:
                tscore = 5
            else:
                tscore = 3

            total = int(min(100, dscore + sscore + ascore + tscore))

            travel_mode = "WALK" if dist_km < 1 else ("CYCLE" if dist_km < 3 else "VEHICLE")
            eta_min = 10 if travel_mode == "WALK" else (20 if travel_mode == "CYCLE" else 35)

            ranked.append({
                "volunteer_id": v["volunteer_id"],
                "match_score": total,
                "score_breakdown": {"distance": dscore, "skill": sscore, "availability": ascore, "trust": tscore},
                "estimated_arrival": (_now() + timedelta(minutes=eta_min)).isoformat().replace("+00:00", "Z"),
                "travel_mode": travel_mode,
                "contact_method": "MASKED_PHONE",
                "safety_features": {
                    "live_location_sharing": True,
                    "emergency_button": True,
                    "check_in_required": True,
                },
            })

        ranked.sort(key=lambda x: x["match_score"], reverse=True)
        results = []
        for i, item in enumerate(ranked[:10], start=1):
            item["rank"] = i
            results.append(item)

        status = "MATCHED" if results else "PENDING"
        return jsonify({
            "match_results": results,
            "request_status": status,
            "escalation_reason": None if results else "No volunteers available in the provided pool.",
            "backup_plan": {
                "professional_service": "Municipal helpline / accredited NGO partner",
                "estimated_cost": 0.0,
                "subsidy_available": True,
            },
        }), 200

    except ValidationError as e:
        return jsonify({"success": False, "error": "Validation failed", "details": e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"request-aid error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to match aid request"}), 500

