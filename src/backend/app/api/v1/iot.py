"""
IoT Predictive Maintenance Network (v1).

Implements:
 - POST /api/v1/iot/ingest
 - GET  /api/v1/iot/predictions
 - GET  /api/v1/iot/health-map
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
import uuid
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, request, current_app
from marshmallow import Schema, fields, validate, ValidationError

from app.extensions import db, limiter, cache
from app.infrastructure.database.models import IoTAssetORM, IoTReadingORM
from app.utils.crypto import sha256_of_json


bp = Blueprint("api_v1_iot", __name__, url_prefix="/api/v1/iot")


ASSET_TYPES = [
    "STREETLIGHT",
    "WATER_PUMP",
    "WASTE_BIN",
    "ELECTRICAL_TRANSFORMER",
    "SOLAR_MICROGRID",
    "STRUCTURAL_SENSOR",
]


class LocationSchema(Schema):
    lat = fields.Float(required=True)
    lng = fields.Float(required=True)
    ward = fields.Str(load_default="")


class SensorReadingsSchema(Schema):
    vibration_rms = fields.Float(allow_none=True)
    temperature_celsius = fields.Float(allow_none=True)
    pressure_kpa = fields.Float(allow_none=True)
    energy_consumption_kwh = fields.Float(allow_none=True)
    fill_level_percent = fields.Float(allow_none=True)
    voltage = fields.Float(allow_none=True)
    current = fields.Float(allow_none=True)
    power_factor = fields.Float(allow_none=True)
    operational_hours = fields.Int(allow_none=True)
    anomaly_score = fields.Float(allow_none=True, validate=validate.Range(min=0, max=1))


class EnvironmentalContextSchema(Schema):
    weather = fields.Str(allow_none=True)
    temperature_ambient = fields.Float(allow_none=True)
    humidity_percent = fields.Float(allow_none=True)


class SensorPayloadSchema(Schema):
    asset_id = fields.Str(required=True, validate=validate.Length(min=4, max=80))
    asset_type = fields.Str(required=True, validate=validate.OneOf(ASSET_TYPES))
    location = fields.Nested(LocationSchema(), required=True)
    timestamp = fields.Str(required=True)
    sensor_readings = fields.Nested(SensorReadingsSchema(), required=True)
    environmental_context = fields.Nested(EnvironmentalContextSchema(), load_default=dict)


class IngestSchema(Schema):
    sensor_payload = fields.Nested(SensorPayloadSchema(), required=True)


def _parse_iso8601_utc(ts: str) -> datetime:
    ts = (ts or "").strip()
    # Accept trailing Z
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _status_from_health(health: int) -> str:
    if health >= 80:
        return "OPTIMAL" if health >= 95 else "GOOD"
    if health >= 60:
        return "FAIR"
    if health >= 40:
        return "POOR"
    return "CRITICAL"


def _baseline_rules(asset_type: str) -> Dict[str, Dict[str, float]]:
    """
    Returns per-metric warning/critical thresholds.
    For "lower-is-bad" metrics (e.g., pressure), critical is a lower number.
    """
    rules: Dict[str, Dict[str, float]] = {
        "STREETLIGHT": {"vibration_rms_warn": 4.0, "vibration_rms_crit": 6.0, "temp_warn": 65.0, "temp_crit": 80.0},
        "WATER_PUMP": {"vibration_rms_warn": 5.5, "vibration_rms_crit": 8.0, "pressure_warn_low": 150.0, "pressure_crit_low": 100.0},
        "WASTE_BIN": {"fill_warn": 80.0, "fill_crit": 95.0},
        "ELECTRICAL_TRANSFORMER": {"temp_warn": 70.0, "temp_crit": 85.0, "voltage_dev_warn_pct": 10.0},
        "SOLAR_MICROGRID": {"eff_warn_low": 60.0, "eff_crit_low": 40.0, "battery_soc_crit_low": 20.0},
        "STRUCTURAL_SENSOR": {"vibration_rms_warn": 10.0, "vibration_rms_crit": 15.0},
    }
    return rules.get(asset_type, {})


def _compute_deviation_pct(actual: Optional[float], baseline: float) -> Optional[float]:
    if actual is None:
        return None
    if baseline == 0:
        return None
    return ((actual - baseline) / baseline) * 100.0


def _anomaly_and_health(asset_type: str, readings: Dict[str, Any]) -> Tuple[int, Dict[str, Any], Dict[str, Any]]:
    """
    Returns (health_score, anomaly_detection_obj, failure_prediction_seed)
    """
    rules = _baseline_rules(asset_type)
    vib = readings.get("vibration_rms")
    temp = readings.get("temperature_celsius")
    pressure = readings.get("pressure_kpa")
    fill = readings.get("fill_level_percent")
    voltage = readings.get("voltage")
    pf = readings.get("power_factor")
    anomaly_score = readings.get("anomaly_score")

    deviations: Dict[str, float] = {}
    severity = "LOW"
    anomaly_type: Optional[str] = None
    confidence = 0.6

    penalty = 0.0

    # Vibration
    if "vibration_rms_warn" in rules and vib is not None:
        warn, crit = rules["vibration_rms_warn"], rules["vibration_rms_crit"]
        deviations["vibration_rms"] = _compute_deviation_pct(vib, warn) or 0.0
        if vib > crit:
            penalty += 55
            severity = "CRITICAL"
            anomaly_type = anomaly_type or "VIBRATION_CRITICAL"
            confidence = 0.9
        elif vib > warn:
            penalty += 20
            severity = max(severity, "MEDIUM", key=["LOW", "MEDIUM", "HIGH", "CRITICAL"].index)
            anomaly_type = anomaly_type or "VIBRATION_WARNING"
            confidence = max(confidence, 0.75)

    # Temperature
    if "temp_warn" in rules and temp is not None:
        warn, crit = rules["temp_warn"], rules["temp_crit"]
        deviations["temperature_celsius"] = _compute_deviation_pct(temp, warn) or 0.0
        if temp > crit:
            penalty += 45
            severity = "CRITICAL"
            anomaly_type = anomaly_type or "TEMPERATURE_CRITICAL"
            confidence = max(confidence, 0.88)
        elif temp > warn:
            penalty += 15
            severity = max(severity, "MEDIUM", key=["LOW", "MEDIUM", "HIGH", "CRITICAL"].index)
            anomaly_type = anomaly_type or "TEMPERATURE_WARNING"
            confidence = max(confidence, 0.7)

    # Pressure (lower is bad)
    if "pressure_warn_low" in rules and pressure is not None:
        warn_low, crit_low = rules["pressure_warn_low"], rules["pressure_crit_low"]
        if pressure < crit_low:
            penalty += 45
            severity = "CRITICAL"
            anomaly_type = anomaly_type or "PRESSURE_CRITICAL_LOW"
            deviations["pressure_kpa"] = _compute_deviation_pct(pressure, warn_low) or 0.0
            confidence = max(confidence, 0.88)
        elif pressure < warn_low:
            penalty += 18
            severity = max(severity, "HIGH", key=["LOW", "MEDIUM", "HIGH", "CRITICAL"].index)
            anomaly_type = anomaly_type or "PRESSURE_WARNING_LOW"
            deviations["pressure_kpa"] = _compute_deviation_pct(pressure, warn_low) or 0.0
            confidence = max(confidence, 0.78)

    # Fill level
    if "fill_warn" in rules and fill is not None:
        warn, crit = rules["fill_warn"], rules["fill_crit"]
        deviations["fill_level_percent"] = _compute_deviation_pct(fill, warn) or 0.0
        if fill > crit:
            penalty += 50
            severity = "CRITICAL"
            anomaly_type = anomaly_type or "OVERFLOW_RISK"
            confidence = max(confidence, 0.9)
        elif fill > warn:
            penalty += 22
            severity = max(severity, "HIGH", key=["LOW", "MEDIUM", "HIGH", "CRITICAL"].index)
            anomaly_type = anomaly_type or "FILL_LEVEL_HIGH"
            confidence = max(confidence, 0.8)

    # Transformer voltage deviation heuristic (no baseline voltage known -> use 230V)
    if asset_type == "ELECTRICAL_TRANSFORMER" and voltage is not None:
        baseline_v = 230.0
        dev_pct = abs((voltage - baseline_v) / baseline_v) * 100.0
        deviations["voltage"] = dev_pct
        if dev_pct > float(rules.get("voltage_dev_warn_pct", 10.0)):
            penalty += 20 if dev_pct < 18 else 35
            severity = max(severity, "HIGH", key=["LOW", "MEDIUM", "HIGH", "CRITICAL"].index)
            anomaly_type = anomaly_type or "VOLTAGE_DEVIATION"
            confidence = max(confidence, 0.75)

    # Power factor drop (insulation/efficiency proxy)
    if pf is not None and pf < 0.75:
        deviations["power_factor"] = (0.75 - pf) / 0.75 * 100.0
        penalty += 10 if pf > 0.65 else 22
        severity = max(severity, "MEDIUM", key=["LOW", "MEDIUM", "HIGH", "CRITICAL"].index)
        anomaly_type = anomaly_type or "POWER_FACTOR_LOW"
        confidence = max(confidence, 0.7)

    # External anomaly_score signal
    if anomaly_score is not None:
        if anomaly_score > 0.9:
            penalty += 35
            severity = "CRITICAL"
            anomaly_type = anomaly_type or "MODEL_ANOMALY_SCORE_HIGH"
            confidence = max(confidence, 0.9)
        elif anomaly_score > 0.7:
            penalty += 18
            severity = max(severity, "HIGH", key=["LOW", "MEDIUM", "HIGH", "CRITICAL"].index)
            anomaly_type = anomaly_type or "MODEL_ANOMALY_SCORE_ELEVATED"
            confidence = max(confidence, 0.8)

    # Base health score
    health = int(max(0, min(100, round(100 - penalty))))

    failure_modes: List[str] = []
    primary_failure_mode: Optional[str] = None

    # Pattern matching for failure modes
    if vib is not None and temp is not None and vib > 0 and temp > 0:
        if (vib > 6.0 and temp > 75.0) or (vib > 8.0 and temp > 70.0):
            primary_failure_mode = "BEARING_FAILURE"
            failure_modes.append("BEARING_FAILURE")

    if asset_type == "WATER_PUMP" and pressure is not None and vib is not None:
        if pressure < 150 and vib > 5.5:
            primary_failure_mode = primary_failure_mode or "CAVITATION"
            failure_modes.append("CAVITATION")

    if asset_type in {"ELECTRICAL_TRANSFORMER", "SOLAR_MICROGRID"} and temp is not None and pf is not None:
        if temp > 70 and pf < 0.8:
            primary_failure_mode = primary_failure_mode or "INSULATION_DEGRADATION"
            failure_modes.append("INSULATION_DEGRADATION")

    if asset_type == "WASTE_BIN" and fill is not None:
        if fill > 95:
            primary_failure_mode = primary_failure_mode or "OVERFLOW"
            failure_modes.append("OVERFLOW")

    if asset_type == "STRUCTURAL_SENSOR" and vib is not None:
        if vib > 15:
            primary_failure_mode = primary_failure_mode or "STRUCTURAL_FATIGUE"
            failure_modes.append("STRUCTURAL_FATIGUE")

    anomaly_obj = {
        "is_anomaly": bool(anomaly_type),
        "anomaly_type": anomaly_type,
        "severity": severity,
        "confidence": float(round(confidence, 2)),
        "deviation_from_baseline": {k: float(round(v, 2)) for k, v in deviations.items()},
    }

    pred_seed = {
        "primary_failure_mode": primary_failure_mode,
        "secondary_failure_modes": list(dict.fromkeys([m for m in failure_modes if m != primary_failure_mode])),
    }

    return health, anomaly_obj, pred_seed


def _estimate_rul_days(asset_id: str, now_utc: datetime) -> Tuple[int, Optional[datetime], float, float]:
    """
    Heuristic RUL estimate based on 30-day health trend.
    Returns: (rul_days, predicted_failure_date, p7d, p30d)
    """
    since = now_utc - timedelta(days=30)
    rows = (
        IoTReadingORM.query
        .filter(IoTReadingORM.asset_id == asset_id)
        .filter(IoTReadingORM.timestamp_utc >= since)
        .order_by(IoTReadingORM.timestamp_utc.asc())
        .all()
    )

    if len(rows) < 3:
        # Fallback: map latest health to coarse RUL
        latest = rows[-1].health_score if rows else 90
        rul = int(max(1, min(365, round((latest / 100.0) * 180 + 30))))
    else:
        t0 = rows[0].timestamp_utc
        # slope in health points per day
        xs = [(r.timestamp_utc - t0).total_seconds() / 86400.0 for r in rows]
        ys = [float(r.health_score) for r in rows]
        x_mean = sum(xs) / len(xs)
        y_mean = sum(ys) / len(ys)
        num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
        den = sum((x - x_mean) ** 2 for x in xs) or 1.0
        slope = num / den  # points/day (negative means degrading)

        latest = ys[-1]
        if slope >= -0.05:
            rul = 365
        else:
            # estimate days until health reaches 20
            rul = int(max(1, min(3650, math.ceil((latest - 20.0) / abs(slope)))))

    predicted_failure_date = (now_utc + timedelta(days=rul)) if rul <= 3650 else None

    # Convert RUL into failure probabilities
    # Use an exponential CDF: P(T <= t) = 1 - exp(-t/rul)
    p7 = 1.0 - math.exp(-7.0 / max(1.0, float(rul)))
    p30 = 1.0 - math.exp(-30.0 / max(1.0, float(rul)))
    return int(rul), predicted_failure_date, float(round(p7, 3)), float(round(p30, 3))


def _maintenance_from_rul_and_status(status: str, rul_days: int, p30: float) -> Dict[str, Any]:
    triggered = status in {"POOR", "CRITICAL"} or rul_days < 30 or p30 > 0.6
    if status == "CRITICAL" or rul_days < 7:
        pr = "P1"
        action = "Immediate dispatch: isolate asset, perform safety inspection, replace failing components."
        downtime = 4.0
        skill = "SPECIALIST"
    elif rul_days < 30 or status == "POOR":
        pr = "P2"
        action = "Short-term maintenance: schedule service, replace wear parts, verify calibration."
        downtime = 2.0
        skill = "SENIOR"
    elif rul_days < 90 or status == "FAIR":
        pr = "P3"
        action = "Scheduled maintenance: plan within next maintenance cycle; monitor weekly."
        downtime = 1.0
        skill = "MID"
    else:
        pr = "P4"
        action = "Monitor: no immediate intervention required; continue telemetry."
        downtime = 0.5
        skill = "JUNIOR"

    return {
        "triggered": bool(triggered),
        "priority": pr,
        "recommended_action": action,
        "estimated_downtime_hours": downtime,
        "spare_parts_required": [],
        "skill_level": skill,
    }


@bp.route("/ingest", methods=["POST"])
@limiter.limit("60 per minute")
def ingest_sensor_payload():
    """
    POST /api/v1/iot/ingest
    Ingest a real-time sensor payload, compute health/anomaly/RUL, persist, return strict JSON output.
    """
    try:
        schema = IngestSchema()
        body = schema.load(request.get_json() or {})
        payload = body["sensor_payload"]

        asset_id = payload["asset_id"]
        asset_type = payload["asset_type"]
        loc = payload["location"]
        ts_utc = _parse_iso8601_utc(payload["timestamp"])

        readings = payload["sensor_readings"] or {}
        env = payload.get("environmental_context") or {}

        health, anomaly_obj, pred_seed = _anomaly_and_health(asset_type, readings)
        status = _status_from_health(health)

        ingestion_id = str(uuid.uuid4())
        processed_at = datetime.now(timezone.utc)

        # Compute audit hash over raw data for tamper-evidence
        raw_for_hash = {"sensor_payload": payload}
        blockchain_hash = sha256_of_json(raw_for_hash)

        # Upsert asset snapshot
        asset = IoTAssetORM.query.get(asset_id)
        if not asset:
            asset = IoTAssetORM(
                id=asset_id,
                asset_type=asset_type,
                lat=float(loc["lat"]),
                lng=float(loc["lng"]),
                ward=loc.get("ward") or "",
            )
            db.session.add(asset)
        asset.health_score = int(health)
        asset.status = status
        asset.set_last_reading({"timestamp": payload["timestamp"], "sensor_readings": readings, "environmental_context": env})

        # Persist reading
        rul_days, predicted_failure_date, p7, p30 = _estimate_rul_days(asset_id, processed_at)
        maint = _maintenance_from_rul_and_status(status, rul_days, p30)

        # Failure probabilities (cap and smooth with status)
        status_boost = {"OPTIMAL": 0.0, "GOOD": 0.05, "FAIR": 0.12, "POOR": 0.22, "CRITICAL": 0.35}.get(status, 0.1)
        p7 = float(round(min(1.0, p7 + status_boost), 3))
        p30 = float(round(min(1.0, p30 + status_boost), 3))

        reading_row = IoTReadingORM(
            ingestion_id=ingestion_id,
            processed_at=processed_at.replace(tzinfo=None),
            asset_id=asset_id,
            asset_type=asset_type,
            ward=loc.get("ward") or "",
            lat=float(loc["lat"]),
            lng=float(loc["lng"]),
            timestamp_utc=ts_utc.replace(tzinfo=None),
            sensor_readings=json_dumps(readings),
            environmental_context=json_dumps(env),
            health_score=int(health),
            status=status,
            is_anomaly=bool(anomaly_obj["is_anomaly"]),
            anomaly_type=anomaly_obj["anomaly_type"],
            severity=anomaly_obj["severity"],
            confidence=float(anomaly_obj["confidence"]),
            deviation_from_baseline=json_dumps(anomaly_obj["deviation_from_baseline"]),
            predicted_failure_date=predicted_failure_date.replace(tzinfo=None) if predicted_failure_date else None,
            remaining_useful_life_days=int(rul_days),
            failure_probability_7d=float(p7),
            failure_probability_30d=float(p30),
            primary_failure_mode=pred_seed.get("primary_failure_mode"),
            secondary_failure_modes=json_dumps(pred_seed.get("secondary_failure_modes") or []),
            maintenance_triggered=bool(maint["triggered"]),
            maintenance_priority=str(maint["priority"]),
            recommended_action=str(maint["recommended_action"]),
            estimated_downtime_hours=float(maint["estimated_downtime_hours"]),
            spare_parts_required=json_dumps(maint["spare_parts_required"] or []),
            skill_level=str(maint["skill_level"]),
            blockchain_hash=blockchain_hash,
        )

        db.session.add(reading_row)
        db.session.commit()

        # Response shape aligned to the provided template
        resp = {
            "ingestion_id": ingestion_id,
            "processed_at": processed_at.isoformat().replace("+00:00", "Z"),
            "asset": {
                "id": asset_id,
                "type": asset_type,
                "location": {"lat": float(loc["lat"]), "lng": float(loc["lng"]), "ward": loc.get("ward") or ""},
                "health_score": int(health),
                "status": status,
            },
            "anomaly_detection": anomaly_obj,
            "failure_prediction": {
                "predicted_failure_date": predicted_failure_date.isoformat().replace("+00:00", "Z") if predicted_failure_date else None,
                "remaining_useful_life_days": int(rul_days),
                "failure_probability_7d": float(p7),
                "failure_probability_30d": float(p30),
                "primary_failure_mode": pred_seed.get("primary_failure_mode"),
                "secondary_failure_modes": pred_seed.get("secondary_failure_modes") or [],
            },
            "maintenance_trigger": maint,
            "alerts": _default_alerts(status=status, priority=maint["priority"], ward=loc.get("ward") or ""),
            "blockchain_hash": blockchain_hash,
        }
        return jsonify(resp), 200

    except ValidationError as e:
        return jsonify({"success": False, "error": "Validation failed", "details": e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"IoT ingest error: {str(e)}")
        return jsonify({"success": False, "error": "IoT ingestion failed"}), 500


@bp.route("/predictions", methods=["GET"])
@limiter.limit("120 per minute")
def get_predictions():
    """
    GET /api/v1/iot/predictions?asset_id=...
    Returns a prediction payload for a specific asset (or latest assets if omitted).
    """
    try:
        asset_id = request.args.get("asset_id")
        limit = int(request.args.get("limit", 10))
        limit = max(1, min(limit, 50))

        if asset_id:
            rows = (
                IoTReadingORM.query
                .filter(IoTReadingORM.asset_id == asset_id)
                .order_by(IoTReadingORM.timestamp_utc.desc())
                .limit(1)
                .all()
            )
        else:
            rows = (
                IoTReadingORM.query
                .order_by(IoTReadingORM.timestamp_utc.desc())
                .limit(limit)
                .all()
            )

        if not rows:
            return jsonify({"success": True, "predictions": []}), 200

        out = []
        for r in rows:
            out.append(_prediction_response_from_row(r))
        return jsonify({"success": True, "predictions": out}), 200
    except Exception as e:
        current_app.logger.error(f"IoT predictions error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to compute predictions"}), 500


@bp.route("/health-map", methods=["GET"])
@limiter.limit("120 per minute")
@cache.cached(timeout=300, query_string=True)
def health_map():
    """
    GET /api/v1/iot/health-map
    bbox[north,south,east,west], zoom_level, asset_types, time_range
    """
    try:
        north = request.args.get("north", type=float)
        south = request.args.get("south", type=float)
        east = request.args.get("east", type=float)
        west = request.args.get("west", type=float)
        zoom = request.args.get("zoom_level", 12, type=int)
        time_range = request.args.get("time_range", "REALTIME")
        asset_types = request.args.getlist("asset_types") or []
        if not asset_types:
            asset_types = ["STREETLIGHT", "WATER_PUMP", "WASTE_BIN"]

        if None in {north, south, east, west}:
            return jsonify({"success": False, "error": "bbox north/south/east/west are required"}), 400

        # Fetch assets in bbox
        assets = (
            IoTAssetORM.query
            .filter(IoTAssetORM.lat <= north)
            .filter(IoTAssetORM.lat >= south)
            .filter(IoTAssetORM.lng <= east)
            .filter(IoTAssetORM.lng >= west)
            .filter(IoTAssetORM.asset_type.in_(asset_types))
            .all()
        )

        # Attach latest reading for popups and prediction overlay
        assets_out = []
        heat_points = []
        critical_count = 0
        avg_health_vals = []

        for a in assets:
            latest = (
                IoTReadingORM.query
                .filter(IoTReadingORM.asset_id == a.id)
                .order_by(IoTReadingORM.timestamp_utc.desc())
                .first()
            )
            if latest:
                hs = int(latest.health_score)
                st = latest.status
                p30 = float(latest.failure_probability_30d or 0.0)
                last_updated = latest.timestamp_utc.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
            else:
                hs = int(a.health_score or 100)
                st = a.status or "OPTIMAL"
                p30 = 0.05
                last_updated = (a.updated_at or datetime.utcnow()).replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

            avg_health_vals.append(hs)
            if st == "CRITICAL":
                critical_count += 1

            assets_out.append({
                "id": a.id,
                "type": a.asset_type,
                "location": {"lat": float(a.lat), "lng": float(a.lng)},
                "health_score": hs,
                "status": st,
                "last_updated": last_updated,
                "popup_data": {
                    "address": a.ward or "",
                    "issue_count_30d": 0,
                    "next_maintenance": a.predictive_maintenance_due.isoformat().replace("+00:00", "Z") if a.predictive_maintenance_due else None,
                    "citizen_reports": 0,
                }
            })

            heat_points.append({"lat": float(a.lat), "lng": float(a.lng), "weight": float(round(max(0.05, p30), 3))})

        clusters = _cluster_assets(assets_out, zoom)
        total_assets = len(assets_out)
        healthy_percent = 0.0 if total_assets == 0 else round(sum(1 for x in assets_out if x["status"] in {"OPTIMAL", "GOOD"}) / total_assets * 100.0, 1)
        predicted_failures_30d = sum(1 for x in assets_out if x["health_score"] < 60)
        maintenance_due = sum(1 for x in assets_out if x["status"] in {"POOR", "CRITICAL"})

        tile_id = f"bbox:{south:.4f},{west:.4f}-{north:.4f},{east:.4f}|z:{zoom}|tr:{time_range}|types:{','.join(asset_types)}"
        resp = {
            "map_data": {
                "tile_id": tile_id,
                "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "ttl_seconds": 300,
                "assets": assets_out if zoom >= 12 else [],
                "clusters": clusters,
                "heatmap": {"max_intensity": 1.0, "points": heat_points},
            },
            "statistics": {
                "total_assets": total_assets,
                "healthy_percent": healthy_percent,
                "critical_assets": int(critical_count),
                "predicted_failures_30d": int(predicted_failures_30d),
                "maintenance_due": int(maintenance_due),
            },
            "alerts": _map_alerts_from_assets(assets_out),
        }
        return jsonify(resp), 200

    except Exception as e:
        current_app.logger.error(f"IoT health-map error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to build health map"}), 500


def json_dumps(obj: Any) -> str:
    import json
    return json.dumps(obj or {}, ensure_ascii=False)


def _default_alerts(status: str, priority: str, ward: str) -> List[dict]:
    base = {
        "channel": "DASHBOARD",
        "recipient_type": "FIELD_CREW" if priority in {"P1", "P2"} else "SUPERVISOR",
        "message_template": f"[{priority}] {status} asset in ward {ward}. Review telemetry and schedule action.",
        "escalation_timeout_minutes": 30 if priority == "P1" else 120,
    }
    alerts = [base]
    if status == "CRITICAL":
        alerts.append({
            "channel": "SMS",
            "recipient_type": "SUPERVISOR",
            "message_template": f"CRITICAL alert: immediate action required in ward {ward}.",
            "escalation_timeout_minutes": 15,
        })
    return alerts


def _prediction_response_from_row(r: IoTReadingORM) -> Dict[str, Any]:
    pred_id = str(uuid.uuid4())
    model_version = "heuristic-ensemble-v1"

    # Provide a 7/30/60/90 mapping using 7d/30d + extrapolation
    p7 = float(r.failure_probability_7d or 0.05)
    p30 = float(r.failure_probability_30d or 0.10)
    p60 = float(round(min(1.0, p30 * 1.35), 3))
    p90 = float(round(min(1.0, p30 * 1.65), 3))

    expected_failure_date = r.predicted_failure_date.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if r.predicted_failure_date else None

    top_risk_factors = []
    try:
        import json
        dev = json.loads(r.deviation_from_baseline or "{}")
        for k, v in sorted(dev.items(), key=lambda kv: abs(float(kv[1])), reverse=True)[:3]:
            top_risk_factors.append({"factor": k, "contribution_percent": float(round(min(100.0, abs(float(v))), 1)), "trend": "INCREASING"})
    except Exception:
        top_risk_factors = [{"factor": "telemetry", "contribution_percent": 50.0, "trend": "STABLE"}]

    # Maintenance recommendation
    priority_score = int(max(0, min(100, round((p90 * 100) + (100 - int(r.health_score)) * 0.4))))

    return {
        "prediction_id": pred_id,
        "model_version": model_version,
        "asset_id": r.asset_id,
        "predictions": {
            "failure_probability": {"7d": p7, "30d": p30, "60d": p60, "90d": p90},
            "confidence_intervals": {"lower_bound": float(round(max(0.0, p30 - 0.08), 3)), "upper_bound": float(round(min(1.0, p30 + 0.12), 3))},
            "expected_failure_date": expected_failure_date,
            "top_risk_factors": top_risk_factors,
        },
        "maintenance_recommendation": {
            "optimal_date": (datetime.now(timezone.utc) + timedelta(days=max(1, min(30, int(r.remaining_useful_life_days or 30) // 2)))).isoformat().replace("+00:00", "Z"),
            "priority_score": priority_score,
            "recommended_actions": [r.recommended_action],
            "estimated_cost_inr": float(round(1500 + (p90 * 20000), 2)),
            "cost_savings_vs_reactive": float(round(5000 + (p90 * 35000), 2)),
            "downtime_required_hours": float(r.estimated_downtime_hours or 1.0),
            "service_impact": "HIGH" if p90 > 0.75 else ("MEDIUM" if p90 > 0.45 else "LOW"),
        },
        "work_order_details": {
            "crew_assignment": _crew_from_type(r.asset_type),
            "tools_required": ["multimeter", "thermal_camera"] if r.asset_type in {"ELECTRICAL_TRANSFORMER", "SOLAR_MICROGRID"} else ["wrench_set", "vibration_meter"],
            "spare_parts": [{"part_id": p, "quantity": 1, "availability": "ORDER_REQUIRED"} for p in _parts_from_failure_mode(r.primary_failure_mode)],
            "permits_required": [],
            "traffic_control_needed": bool(r.asset_type in {"ELECTRICAL_TRANSFORMER"} and (r.status in {"POOR", "CRITICAL"})),
        },
        "model_explanation": {
            "shap_values": {"health_score_trend": float(round(p30 * 0.6, 3)), "anomaly_severity": float(round(p30 * 0.4, 3))},
            "analogous_cases": [],
        },
    }


def _crew_from_type(asset_type: str) -> str:
    return {
        "STREETLIGHT": "ELECTRICAL",
        "ELECTRICAL_TRANSFORMER": "ELECTRICAL",
        "SOLAR_MICROGRID": "ELECTRICAL",
        "WATER_PUMP": "PLUMBING",
        "STRUCTURAL_SENSOR": "STRUCTURAL",
        "WASTE_BIN": "GENERAL",
    }.get(asset_type, "GENERAL")


def _parts_from_failure_mode(mode: Optional[str]) -> List[str]:
    if not mode:
        return []
    return {
        "BEARING_FAILURE": ["bearing_kit", "lubricant"],
        "CAVITATION": ["impeller", "seal_kit"],
        "INSULATION_DEGRADATION": ["insulation_sleeve", "gasket_set"],
        "OVERFLOW": ["lid_hinge", "sensor_module"],
        "STRUCTURAL_FATIGUE": ["strain_gauge", "mounting_bracket"],
    }.get(mode, [])


def _cluster_assets(assets: List[dict], zoom: int) -> List[dict]:
    if not assets:
        return []
    # Simple grid clustering (approx) driven by zoom
    # Higher zoom => smaller bins
    step = 0.002 if zoom >= 15 else (0.006 if zoom >= 12 else 0.02)
    bins: Dict[Tuple[int, int], List[dict]] = {}
    for a in assets:
        lat = a["location"]["lat"]
        lng = a["location"]["lng"]
        key = (int(lat / step), int(lng / step))
        bins.setdefault(key, []).append(a)

    clusters = []
    for _, items in bins.items():
        lat_mean = sum(i["location"]["lat"] for i in items) / len(items)
        lng_mean = sum(i["location"]["lng"] for i in items) / len(items)
        avg_health = sum(i["health_score"] for i in items) / len(items)
        critical = sum(1 for i in items if i["status"] == "CRITICAL")
        priority_score = int(max(0, min(100, round((100 - avg_health) + (critical * 10)))))
        clusters.append({
            "center": {"lat": float(round(lat_mean, 6)), "lng": float(round(lng_mean, 6))},
            "radius_meters": float(120 if zoom >= 15 else (350 if zoom >= 12 else 1200)),
            "asset_count": int(len(items)),
            "avg_health": int(round(avg_health)),
            "critical_count": int(critical),
            "priority_score": int(priority_score),
        })
    return clusters


def _map_alerts_from_assets(assets: List[dict]) -> List[dict]:
    alerts = []
    for a in assets:
        if a["status"] == "CRITICAL":
            alerts.append({
                "type": "INDIVIDUAL_FAILURE",
                "location": a["location"],
                "message": f"Critical asset detected: {a['type']} {a['id']}",
                "severity": "CRITICAL",
            })
    # Cluster-level alert
    if len(alerts) >= 3:
        alerts.append({
            "type": "CLUSTER_CRITICAL",
            "location": assets[0]["location"],
            "message": "Multiple critical assets detected in this area.",
            "severity": "HIGH",
        })
    return alerts[:25]

