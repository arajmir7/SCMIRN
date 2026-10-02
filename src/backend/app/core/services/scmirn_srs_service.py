"""
SCMIRN SRS implementation service.

Implements core operational behaviors mapped to FR-01..FR-24.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
import math
import uuid
from typing import Any, Dict, List, Optional, Tuple

from app.extensions import db
from app.infrastructure.database.models import (
    SRSAuditLogORM,
    SRSAssetORM,
    SRSBudgetEventORM,
    SRSContractorORM,
    SRSIssueEventORM,
    SRSIssueORM,
    SRSUtilityMapORM,
    SRSWorkOrderORM,
)


LIFECYCLE_ORDER = [
    "RECEIVED",
    "VERIFIED",
    "ASSIGNED",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
]

ALLOWED_TRANSITIONS = {
    "RECEIVED": {"VERIFIED", "REJECTED"},
    "VERIFIED": {"ASSIGNED", "IN_PROGRESS", "REJECTED"},
    "ASSIGNED": {"IN_PROGRESS", "REJECTED"},
    "IN_PROGRESS": {"RESOLVED", "REJECTED"},
    "RESOLVED": {"CLOSED", "IN_PROGRESS"},
    "CLOSED": set(),
    "REJECTED": set(),
}

SLA_HOURS_BY_TIER = {"CRITICAL": 1, "HIGH": 8, "MEDIUM": 24, "LOW": 72}

LANGUAGE_MESSAGES = {
    "en": {
        "received": "Issue received.",
        "verified": "Issue verified by civic operations.",
        "assigned": "Repair team assigned.",
        "in_progress": "Repair in progress.",
        "resolved": "Repair completed, awaiting confirmation.",
        "closed": "Issue closed.",
        "escalated": "Emergency escalation has been triggered.",
    },
    "hi": {
        "received": "समस्या प्राप्त हुई।",
        "verified": "समस्या सत्यापित की गई है।",
        "assigned": "मरम्मत टीम नियुक्त की गई है।",
        "in_progress": "मरम्मत कार्य जारी है।",
        "resolved": "मरम्मत पूरी हुई, पुष्टि लंबित है।",
        "closed": "समस्या बंद कर दी गई है।",
        "escalated": "आपातकालीन एस्केलेशन सक्रिय किया गया है।",
    },
}

DEFAULT_CONTRACTORS = [
    {
        "contractor_id": "CTR-ROAD-01",
        "name": "Metro RoadWorks",
        "specialization": "road",
    },
    {
        "contractor_id": "CTR-DRAIN-01",
        "name": "Urban Drain Services",
        "specialization": "water",
    },
    {
        "contractor_id": "CTR-UTIL-01",
        "name": "Grid and Utility Systems",
        "specialization": "electricity",
    },
]


class SCMIRNSRSService:
    """Business service for practical civic workflows."""

    def ensure_bootstrap(self) -> None:
        if SRSContractorORM.query.count() == 0:
            for row in DEFAULT_CONTRACTORS:
                db.session.add(SRSContractorORM(**row))
            db.session.commit()

    # ==========================
    # Issue Reporting & Triage
    # ==========================

    def report_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.ensure_bootstrap()
        now = datetime.utcnow()

        reporter = payload.get("reporter") or {}
        source = str(payload.get("source") or "citizen").strip().lower()
        title = str(payload.get("title") or "").strip()
        description = str(payload.get("description") or "").strip()
        category = str(payload.get("category") or "other").strip().lower()
        ward = str(payload.get("ward") or "").strip() or None

        lat = _to_float(payload.get("lat"))
        lon = _to_float(payload.get("lon"))
        evidence_urls = _to_list_str(payload.get("evidence_urls"))

        duplicate_of, duplicate_score = self._detect_duplicate(
            category=category,
            lat=lat,
            lon=lon,
            title=title,
            description=description,
            evidence_urls=evidence_urls,
        )
        fraud_score = self._fraud_score(
            reporter_id=reporter.get("id"),
            reporter_reputation=_to_float(reporter.get("reputation"), default=0.5),
            evidence_urls=evidence_urls,
            duplicate_score=duplicate_score,
            title=title,
            description=description,
            source=source,
            has_location=lat is not None and lon is not None,
        )

        severity, risk_level, priority_tier, priority_score, explainability = self._classify_and_prioritize(
            category=category,
            title=title,
            description=description,
            source=source,
            reporter_reputation=_to_float(reporter.get("reputation"), default=0.5),
            fraud_score=fraud_score,
        )
        emergency_flag, emergency_reason = self._detect_emergency(title, description, category, severity)
        safety_impact, usage_impact, cost_impact = self._impact_breakdown(priority_score, category, severity)

        issue = SRSIssueORM(
            public_id=_issue_id(),
            source=source,
            title=title,
            description=description,
            category=category,
            lat=lat,
            lon=lon,
            ward=ward,
            evidence_urls=json.dumps(evidence_urls),
            status="RECEIVED",
            severity=severity,
            risk_level=risk_level,
            priority_tier=priority_tier,
            priority_score=priority_score,
            explainability=json.dumps(explainability),
            safety_impact=safety_impact,
            usage_impact=usage_impact,
            cost_impact=cost_impact,
            duplicate_of_issue_id=duplicate_of,
            duplicate_score=duplicate_score,
            fraud_score=fraud_score,
            is_malicious=fraud_score >= 0.75,
            is_emergency=emergency_flag,
            emergency_reason=emergency_reason,
            reporter_id=str(reporter.get("id")) if reporter.get("id") is not None else None,
            reporter_reputation=_to_float(reporter.get("reputation"), default=0.5),
            reporter_language=str(reporter.get("language") or "en").lower(),
            captured_offline=bool(payload.get("captured_offline", False)),
            captured_at=_parse_timestamp(payload.get("captured_at")) or now,
            synced_at=now if not bool(payload.get("captured_offline", False)) else None,
            sla_deadline=now + timedelta(hours=SLA_HOURS_BY_TIER[priority_tier]),
        )
        db.session.add(issue)
        db.session.flush()

        self._append_issue_event(
            issue_public_id=issue.public_id,
            from_status=None,
            to_status="RECEIVED",
            actor_role="citizen" if source == "citizen" else "system",
            actor_id=issue.reporter_id,
            notes="Issue intake completed",
            metadata={
                "duplicate_score": round(duplicate_score, 3),
                "fraud_score": round(fraud_score, 3),
                "priority_score": round(priority_score, 2),
            },
        )
        self._append_audit(
            event_type="ISSUE_REPORTED",
            actor_role="citizen" if source == "citizen" else "system",
            actor_id=issue.reporter_id,
            entity_type="ISSUE",
            entity_id=issue.public_id,
            before_state={},
            after_state=self.serialize_issue(issue),
            reason="FR-01 intake",
        )

        notifications = [self._localized_message(issue.reporter_language, "received")]

        escalation = None
        if emergency_flag:
            issue.escalated_at = now
            notifications.append(self._localized_message(issue.reporter_language, "escalated"))
            escalation = {
                "severity": "P1",
                "target_teams": ["WARD_EMERGENCY", "TRAFFIC_POLICE", "DISASTER_CELL"],
                "mitigation_actions": ["Deploy barricades", "Send nearest field crew", "Issue public alert"],
            }
            self._append_audit(
                event_type="EMERGENCY_ESCALATED",
                actor_role="system",
                actor_id=None,
                entity_type="ISSUE",
                entity_id=issue.public_id,
                before_state={"is_emergency": False},
                after_state={"is_emergency": True, "reason": emergency_reason},
                reason="FR-05 emergency workflow",
            )

        db.session.commit()

        return {
            "issue": self.serialize_issue(issue),
            "duplicate_detection": {
                "is_duplicate": duplicate_of is not None,
                "duplicate_of_issue_id": duplicate_of,
                "confidence": round(duplicate_score, 3),
            },
            "fraud_detection": {
                "fraud_score": round(fraud_score, 3),
                "review_required": fraud_score >= 0.75,
            },
            "classification": {
                "severity": severity,
                "risk_level": risk_level,
                "priority_tier": priority_tier,
                "priority_score": round(priority_score, 2),
                "explainability": explainability,
            },
            "escalation": escalation,
            "notifications": notifications,
        }

    def detect_multisource_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        FR-02: Accept sensor/CCTV/smartphone event and convert to issue intake.
        """
        source_type = str(payload.get("source_type") or "sensor").strip().lower()
        title = str(payload.get("title") or f"Auto-detected {source_type} anomaly").strip()
        description = str(payload.get("description") or "Automated detection event.").strip()
        category = str(payload.get("category") or self._category_from_source(source_type)).strip().lower()

        issue_payload = {
            "source": source_type,
            "title": title,
            "description": description,
            "category": category,
            "lat": payload.get("lat"),
            "lon": payload.get("lon"),
            "ward": payload.get("ward"),
            "evidence_urls": _to_list_str(payload.get("evidence_urls")),
            "reporter": {"id": "SYSTEM", "language": "en", "reputation": 1.0},
        }
        result = self.report_issue(issue_payload)
        result["ingestion"] = {
            "source_type": source_type,
            "ingested_at": datetime.utcnow().isoformat() + "Z",
        }
        return result

    def get_issue_lifecycle(self, issue_public_id: str) -> Dict[str, Any]:
        issue = self._get_issue(issue_public_id)
        events = (
            SRSIssueEventORM.query
            .filter(SRSIssueEventORM.issue_public_id == issue_public_id)
            .order_by(SRSIssueEventORM.created_at.asc())
            .all()
        )
        return {
            "issue": self.serialize_issue(issue),
            "timeline": [self.serialize_issue_event(e) for e in events],
        }

    def transition_issue(
        self,
        issue_public_id: str,
        to_status: str,
        actor_role: str,
        actor_id: Optional[str] = None,
        notes: str = "",
        manual_override: bool = False,
    ) -> Dict[str, Any]:
        issue = self._get_issue(issue_public_id)
        to_status_norm = _normalize_status(to_status)
        from_status = _normalize_status(issue.status)

        if not manual_override and to_status_norm not in ALLOWED_TRANSITIONS.get(from_status, set()):
            raise ValueError(f"Invalid transition: {from_status} -> {to_status_norm}")

        before = self.serialize_issue(issue)
        issue.status = to_status_norm
        now = datetime.utcnow()
        if to_status_norm == "RESOLVED":
            issue.resolved_at = now
        if to_status_norm == "CLOSED":
            issue.closed_at = now

        self._append_issue_event(
            issue_public_id=issue.public_id,
            from_status=from_status,
            to_status=to_status_norm,
            actor_role=actor_role,
            actor_id=actor_id,
            notes=notes or "Status updated",
            metadata={"manual_override": manual_override},
        )
        self._append_audit(
            event_type="ISSUE_STATUS_CHANGED",
            actor_role=actor_role,
            actor_id=actor_id,
            entity_type="ISSUE",
            entity_id=issue.public_id,
            before_state=before,
            after_state=self.serialize_issue(issue),
            reason=notes or "FR-06 lifecycle update",
        )
        db.session.commit()

        return {
            "issue": self.serialize_issue(issue),
            "notification": self._localized_message(issue.reporter_language, to_status_norm.lower()),
        }

    def citizen_feedback(
        self,
        issue_public_id: str,
        confirmed: bool,
        rating: Optional[int],
        comment: Optional[str],
        actor_id: Optional[str],
    ) -> Dict[str, Any]:
        issue = self._get_issue(issue_public_id)
        before = self.serialize_issue(issue)

        issue.citizen_confirmed = bool(confirmed)
        issue.citizen_feedback_rating = int(rating) if rating is not None else None
        issue.citizen_feedback_comment = (comment or "").strip() or None

        if confirmed and _normalize_status(issue.status) == "RESOLVED":
            issue.status = "CLOSED"
            issue.closed_at = datetime.utcnow()
            self._append_issue_event(
                issue_public_id=issue.public_id,
                from_status="RESOLVED",
                to_status="CLOSED",
                actor_role="citizen",
                actor_id=actor_id,
                notes="Citizen confirmed resolution",
                metadata={"rating": rating},
            )

        self._append_audit(
            event_type="CITIZEN_FEEDBACK_CAPTURED",
            actor_role="citizen",
            actor_id=actor_id,
            entity_type="ISSUE",
            entity_id=issue.public_id,
            before_state=before,
            after_state=self.serialize_issue(issue),
            reason="FR-07 citizen confirmation",
        )
        db.session.commit()
        return {"issue": self.serialize_issue(issue)}

    # ==========================
    # Work Orders & Contractors
    # ==========================

    def generate_work_order(
        self,
        issue_public_id: str,
        estimated_cost: float,
        warranty_days: int,
        actor_role: str,
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        issue = self._get_issue(issue_public_id)
        if issue.work_order_id:
            existing = self._get_work_order(issue.work_order_id)
            return {"work_order": self.serialize_work_order(existing), "reused": True}

        now = datetime.utcnow()
        work_order = SRSWorkOrderORM(
            work_order_id=_work_order_id(),
            issue_public_id=issue.public_id,
            status="CREATED",
            estimated_cost=max(0.0, float(estimated_cost)),
            warranty_days=max(30, int(warranty_days)),
            warranty_expiry=now + timedelta(days=max(30, int(warranty_days))),
            due_at=issue.sla_deadline,
            payment_status="HOLD",
        )
        db.session.add(work_order)

        before = self.serialize_issue(issue)
        issue.work_order_id = work_order.work_order_id
        self._append_audit(
            event_type="WORK_ORDER_CREATED",
            actor_role=actor_role,
            actor_id=actor_id,
            entity_type="WORK_ORDER",
            entity_id=work_order.work_order_id,
            before_state={},
            after_state=self.serialize_work_order(work_order),
            reason="FR-08 digital work order generation",
        )
        self._append_audit(
            event_type="ISSUE_LINKED_TO_WORK_ORDER",
            actor_role=actor_role,
            actor_id=actor_id,
            entity_type="ISSUE",
            entity_id=issue.public_id,
            before_state=before,
            after_state=self.serialize_issue(issue),
            reason="FR-08 linkage",
        )
        db.session.commit()
        return {"work_order": self.serialize_work_order(work_order), "reused": False}

    def assign_work_order(
        self,
        work_order_id: str,
        contractor_id: Optional[str],
        assigned_team: Optional[str],
        sla_hours: Optional[int],
        actor_role: str,
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.ensure_bootstrap()
        work_order = self._get_work_order(work_order_id)
        issue = self._get_issue(work_order.issue_public_id)

        contractor = self._select_contractor(contractor_id, issue.category)
        if contractor is None:
            raise ValueError("No available contractor found")

        now = datetime.utcnow()
        before_wo = self.serialize_work_order(work_order)

        work_order.contractor_id = contractor.contractor_id
        work_order.assigned_team = assigned_team or contractor.name
        work_order.status = "ASSIGNED"
        work_order.sla_hours = int(sla_hours) if sla_hours is not None else int(work_order.sla_hours or 24)
        work_order.due_at = now + timedelta(hours=work_order.sla_hours)

        before_issue = self.serialize_issue(issue)
        issue.assigned_contractor_id = contractor.contractor_id
        issue.assigned_team = work_order.assigned_team
        issue.status = "ASSIGNED"

        self._append_issue_event(
            issue_public_id=issue.public_id,
            from_status=_normalize_status(before_issue["status"]),
            to_status="ASSIGNED",
            actor_role=actor_role,
            actor_id=actor_id,
            notes=f"Assigned to {contractor.contractor_id}",
            metadata={"work_order_id": work_order.work_order_id},
        )
        self._append_audit(
            event_type="WORK_ORDER_ASSIGNED",
            actor_role=actor_role,
            actor_id=actor_id,
            entity_type="WORK_ORDER",
            entity_id=work_order.work_order_id,
            before_state=before_wo,
            after_state=self.serialize_work_order(work_order),
            reason="FR-09 assignment and SLA tracking",
        )
        self._append_audit(
            event_type="ISSUE_ASSIGNED",
            actor_role=actor_role,
            actor_id=actor_id,
            entity_type="ISSUE",
            entity_id=issue.public_id,
            before_state=before_issue,
            after_state=self.serialize_issue(issue),
            reason="FR-09 assignment update",
        )
        db.session.commit()

        return {
            "work_order": self.serialize_work_order(work_order),
            "contractor": self.serialize_contractor(contractor),
        }

    def verify_repair(
        self,
        work_order_id: str,
        ai_quality_score: float,
        sensor_health_delta: float,
        inspector_validated: bool,
        citizen_validated: bool,
        actual_cost: Optional[float],
        actor_role: str,
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        work_order = self._get_work_order(work_order_id)
        issue = self._get_issue(work_order.issue_public_id)
        contractor = self._get_contractor(work_order.contractor_id) if work_order.contractor_id else None

        ai = _clamp(_to_float(ai_quality_score, default=0.0), 0.0, 100.0)
        sensor = _clamp((_to_float(sensor_health_delta, default=0.0) + 100.0) / 2.0, 0.0, 100.0)
        inspector_component = 100.0 if inspector_validated else 20.0
        citizen_component = 100.0 if citizen_validated else 35.0

        quality_score = round((ai * 0.45) + (sensor * 0.2) + (inspector_component * 0.2) + (citizen_component * 0.15), 2)
        passed = inspector_validated and quality_score >= 70.0

        now = datetime.utcnow()
        before_wo = self.serialize_work_order(work_order)
        before_issue = self.serialize_issue(issue)

        work_order.ai_quality_score = ai
        work_order.sensor_health_delta = _to_float(sensor_health_delta, default=0.0)
        work_order.quality_score = quality_score
        work_order.inspector_validated = bool(inspector_validated)
        work_order.citizen_validated = bool(citizen_validated)
        work_order.actual_cost = max(0.0, _to_float(actual_cost, default=work_order.actual_cost or 0.0))
        work_order.completed_at = now

        if passed:
            work_order.status = "VERIFIED"
            work_order.payment_status = "READY_FOR_RELEASE"
            issue.status = "RESOLVED" if not citizen_validated else "CLOSED"
            issue.resolved_at = now
            if citizen_validated:
                issue.closed_at = now
            self._append_issue_event(
                issue_public_id=issue.public_id,
                from_status=_normalize_status(before_issue["status"]),
                to_status=issue.status,
                actor_role=actor_role,
                actor_id=actor_id,
                notes="Repair validated",
                metadata={"quality_score": quality_score},
            )
        else:
            work_order.status = "REWORK_REQUIRED"
            work_order.payment_status = "HOLD"
            work_order.repeat_failure_count = int(work_order.repeat_failure_count or 0) + 1
            issue.status = "IN_PROGRESS"
            self._append_issue_event(
                issue_public_id=issue.public_id,
                from_status=_normalize_status(before_issue["status"]),
                to_status="IN_PROGRESS",
                actor_role=actor_role,
                actor_id=actor_id,
                notes="Repair rejected, rework required",
                metadata={"quality_score": quality_score},
            )

        self._append_audit(
            event_type="REPAIR_VERIFIED",
            actor_role=actor_role,
            actor_id=actor_id,
            entity_type="WORK_ORDER",
            entity_id=work_order.work_order_id,
            before_state=before_wo,
            after_state=self.serialize_work_order(work_order),
            reason="FR-10 repair quality verification",
        )
        self._append_audit(
            event_type="ISSUE_STATUS_POST_VERIFICATION",
            actor_role=actor_role,
            actor_id=actor_id,
            entity_type="ISSUE",
            entity_id=issue.public_id,
            before_state=before_issue,
            after_state=self.serialize_issue(issue),
            reason="FR-10 issue lifecycle progression",
        )

        if contractor:
            self._update_contractor_score(contractor, work_order, quality_score)

        db.session.commit()
        return {
            "work_order": self.serialize_work_order(work_order),
            "issue": self.serialize_issue(issue),
            "passed": passed,
        }

    def get_contractor_performance(self, contractor_id: str) -> Dict[str, Any]:
        contractor = self._get_contractor(contractor_id)
        return {"contractor": self.serialize_contractor(contractor)}

    # ==========================
    # Asset Health & Predictions
    # ==========================

    def upsert_asset_health(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        asset_id = str(payload.get("asset_id") or "").strip()
        if not asset_id:
            raise ValueError("asset_id is required")

        asset = SRSAssetORM.query.get(asset_id)
        if asset is None:
            asset = SRSAssetORM(asset_id=asset_id, asset_type=str(payload.get("asset_type") or "road"))
            db.session.add(asset)

        age = _clamp(_to_float(payload.get("age_years"), default=0.0), 0.0, 120.0)
        degradation_rate = _clamp(_to_float(payload.get("degradation_rate"), default=0.1), 0.0, 1.0)
        usage_index = _clamp(_to_float(payload.get("usage_index"), default=50.0), 0.0, 100.0)
        sensor_score = _clamp(_to_float(payload.get("sensor_score"), default=80.0), 0.0, 100.0)
        criticality = str(payload.get("criticality") or "MEDIUM").upper()

        health = _clamp(100.0 - (age * 0.9) - (degradation_rate * 50.0) - (usage_index * 0.2) + (sensor_score * 0.35), 0.0, 100.0)
        criticality_factor = {"LOW": 1.3, "MEDIUM": 1.0, "HIGH": 0.7, "CRITICAL": 0.5}.get(criticality, 1.0)
        predicted_failure_days = int(max(7, min(3650, round((health + 5.0) * criticality_factor * 2.4))))

        asset.asset_type = str(payload.get("asset_type") or asset.asset_type)
        asset.ward = str(payload.get("ward") or asset.ward or "").strip() or None
        asset.lat = _to_float(payload.get("lat"))
        asset.lon = _to_float(payload.get("lon"))
        asset.age_years = age
        asset.criticality = criticality
        asset.usage_index = usage_index
        asset.health_score = round(health, 2)
        asset.predicted_failure_days = predicted_failure_days
        asset.degradation_rate = degradation_rate
        asset.last_sensor_score = sensor_score
        asset.maintenance_status = (
            "IMMEDIATE" if health < 35 else ("SCHEDULED" if health < 60 or predicted_failure_days < 60 else "MONITOR")
        )
        asset.last_inspection_at = _parse_timestamp(payload.get("last_inspection_at")) or asset.last_inspection_at
        asset.accessibility_compliant = bool(payload.get("accessibility_compliant", asset.accessibility_compliant))

        self._append_audit(
            event_type="ASSET_HEALTH_UPDATED",
            actor_role="system",
            actor_id=None,
            entity_type="ASSET",
            entity_id=asset.asset_id,
            before_state={},
            after_state=self.serialize_asset(asset),
            reason="FR-12 infrastructure health monitoring",
        )
        db.session.commit()
        return {"asset": self.serialize_asset(asset)}

    def maintenance_schedule(self, horizon_days: int = 90) -> Dict[str, Any]:
        horizon = int(max(7, min(horizon_days, 365)))
        rows = (
            SRSAssetORM.query
            .filter(
                db.or_(
                    SRSAssetORM.predicted_failure_days <= horizon,
                    SRSAssetORM.health_score < 60.0,
                )
            )
            .order_by(SRSAssetORM.predicted_failure_days.asc(), SRSAssetORM.health_score.asc())
            .all()
        )
        plans = []
        for asset in rows:
            priority = "P1" if asset.health_score < 35 else ("P2" if asset.health_score < 55 else "P3")
            plans.append(
                {
                    "asset_id": asset.asset_id,
                    "asset_type": asset.asset_type,
                    "priority": priority,
                    "predicted_failure_days": int(asset.predicted_failure_days or 365),
                    "health_score": round(float(asset.health_score or 0.0), 2),
                    "recommended_window_days": max(1, min(30, int((asset.predicted_failure_days or 30) / 2))),
                }
            )
        return {"horizon_days": horizon, "maintenance_plan": plans}

    # ==========================
    # Risk & Planning
    # ==========================

    def flood_prediction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        rainfall_mm = _clamp(_to_float(payload.get("rainfall_mm"), default=0.0), 0.0, 1000.0)
        drain_capacity_pct = _clamp(_to_float(payload.get("drain_capacity_pct"), default=70.0), 0.0, 100.0)
        blockage_index = _clamp(_to_float(payload.get("blockage_index"), default=0.2), 0.0, 1.0)
        soil_saturation = _clamp(_to_float(payload.get("soil_saturation"), default=0.5), 0.0, 1.0)

        demand_pressure = min(1.0, rainfall_mm / 180.0)
        capacity_gap = max(0.0, 1.0 - (drain_capacity_pct / 100.0))
        risk_score = _clamp(
            (demand_pressure * 0.45) + (blockage_index * 0.3) + (capacity_gap * 0.15) + (soil_saturation * 0.1),
            0.0,
            1.0,
        )
        band = "CRITICAL" if risk_score >= 0.8 else ("HIGH" if risk_score >= 0.6 else ("MEDIUM" if risk_score >= 0.4 else "LOW"))
        return {
            "risk_score": round(risk_score, 3),
            "risk_band": band,
            "actions": [
                "Dispatch pre-monsoon cleaning crew" if band in {"HIGH", "CRITICAL"} else "Continue routine desilting",
                "Publish citizen flood advisory" if band in {"HIGH", "CRITICAL"} else "Monitor rainfall feed",
            ],
        }

    def traffic_impact(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        baseline_vph = _clamp(_to_float(payload.get("baseline_vehicles_per_hour"), default=5000.0), 50.0, 250000.0)
        lane_closure_pct = _clamp(_to_float(payload.get("lane_closure_pct"), default=20.0), 0.0, 100.0)
        work_duration_hours = _clamp(_to_float(payload.get("work_duration_hours"), default=8.0), 0.5, 336.0)
        peak_hour = bool(payload.get("peak_hour", True))

        effective_capacity_drop = (lane_closure_pct / 100.0) * (1.25 if peak_hour else 0.9)
        expected_delay_min = round(_clamp(effective_capacity_drop * 90.0 + (work_duration_hours * 0.3), 0.0, 240.0), 1)
        congestion_index = round(_clamp(effective_capacity_drop * 100.0, 0.0, 100.0), 1)

        return {
            "expected_delay_minutes": expected_delay_min,
            "congestion_index": congestion_index,
            "recommended_window": "22:00-05:00" if expected_delay_min > 25 else "10:00-16:00",
            "actions": [
                "Issue diversion advisory",
                "Coordinate adaptive traffic signals" if expected_delay_min > 15 else "No dynamic signal change required",
            ],
        }

    def register_utility(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        utility_id = str(payload.get("utility_id") or "").strip()
        if not utility_id:
            raise ValueError("utility_id is required")

        geometry = payload.get("geometry") or []
        utility = SRSUtilityMapORM.query.get(utility_id)
        if utility is None:
            utility = SRSUtilityMapORM(utility_id=utility_id, utility_type=str(payload.get("utility_type") or "water"))
            db.session.add(utility)

        utility.utility_type = str(payload.get("utility_type") or utility.utility_type).lower()
        utility.ward = str(payload.get("ward") or "").strip() or None
        utility.geometry_json = json.dumps(geometry)
        utility.depth_m = _clamp(_to_float(payload.get("depth_m"), default=1.5), 0.1, 30.0)
        utility.active = bool(payload.get("active", True))

        self._append_audit(
            event_type="UTILITY_MAP_UPDATED",
            actor_role="engineer",
            actor_id=None,
            entity_type="UTILITY",
            entity_id=utility.utility_id,
            before_state={},
            after_state=self.serialize_utility(utility),
            reason="FR-16 utility mapping",
        )
        db.session.commit()
        return {"utility": self.serialize_utility(utility)}

    def pre_dig_verify(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        lat = _to_float(payload.get("lat"))
        lon = _to_float(payload.get("lon"))
        radius_m = _clamp(_to_float(payload.get("radius_m"), default=5.0), 1.0, 200.0)
        if lat is None or lon is None:
            raise ValueError("lat and lon are required")

        intersects = []
        utilities = SRSUtilityMapORM.query.filter_by(active=True).all()
        for utility in utilities:
            points = _safe_json_loads(utility.geometry_json, default=[])
            for point in points:
                p_lat = _to_float(point.get("lat")) if isinstance(point, dict) else None
                p_lon = _to_float(point.get("lon")) if isinstance(point, dict) else None
                if p_lat is None or p_lon is None:
                    continue
                distance = _haversine_km(lat, lon, p_lat, p_lon) * 1000.0
                if distance <= radius_m:
                    intersects.append(
                        {
                            "utility_id": utility.utility_id,
                            "utility_type": utility.utility_type,
                            "distance_m": round(distance, 2),
                            "depth_m": round(float(utility.depth_m or 0.0), 2),
                        }
                    )
                    break

        return {
            "clearance_status": "HOLD" if intersects else "APPROVED",
            "intersections": intersects,
            "penalty_warning": bool(intersects),
        }

    # ==========================
    # Accessibility / Twin / Dashboard
    # ==========================

    def tag_accessibility_issue(self, issue_public_id: str, barrier_type: str, actor_role: str) -> Dict[str, Any]:
        issue = self._get_issue(issue_public_id)
        before = self.serialize_issue(issue)
        issue.accessibility_flag = True
        issue.accessibility_barrier_type = str(barrier_type or "general").strip().lower()

        self._append_audit(
            event_type="ACCESSIBILITY_TAGGED",
            actor_role=actor_role,
            actor_id=None,
            entity_type="ISSUE",
            entity_id=issue.public_id,
            before_state=before,
            after_state=self.serialize_issue(issue),
            reason="FR-17 accessibility issue management",
        )
        db.session.commit()
        return {"issue": self.serialize_issue(issue)}

    def digital_twin_overview(self) -> Dict[str, Any]:
        assets = SRSAssetORM.query.all()
        issues = SRSIssueORM.query.all()
        return {
            "assets": [self.serialize_asset(a) for a in assets],
            "issues": [self.serialize_issue(i) for i in issues],
            "city_health_index": round(
                (
                    (sum(float(a.health_score or 0.0) for a in assets) / len(assets)) if assets else 80.0
                ) * 0.6
                + (
                    (sum(1 for i in issues if _normalize_status(i.status) in {"RESOLVED", "CLOSED"}) / len(issues) * 100.0)
                    if issues else 75.0
                ) * 0.4,
                2,
            ),
        }

    def public_dashboard(self) -> Dict[str, Any]:
        issues = SRSIssueORM.query.all()
        assets = SRSAssetORM.query.all()
        total = len(issues)
        status_counts: Dict[str, int] = {}
        for issue in issues:
            status = _normalize_status(issue.status)
            status_counts[status] = status_counts.get(status, 0) + 1

        resolved = status_counts.get("RESOLVED", 0) + status_counts.get("CLOSED", 0)
        sla_met = sum(1 for i in issues if i.sla_deadline and ((i.resolved_at or i.closed_at or datetime.utcnow()) <= i.sla_deadline))
        sla_ratio = round((sla_met / total) * 100.0, 2) if total else 0.0

        avg_health = round(sum(float(a.health_score or 0.0) for a in assets) / len(assets), 2) if assets else 0.0

        return {
            "issues_total": total,
            "issues_resolved": resolved,
            "status_breakdown": status_counts,
            "sla_compliance_percent": sla_ratio,
            "asset_health_avg": avg_health,
        }

    # ==========================
    # Governance / Audit / Budget
    # ==========================

    def list_audit_logs(self, limit: int = 100) -> Dict[str, Any]:
        rows = SRSAuditLogORM.query.order_by(SRSAuditLogORM.id.desc()).limit(max(1, min(limit, 500))).all()
        return {
            "count": len(rows),
            "items": [self.serialize_audit(r) for r in rows],
        }

    def budget_event(self, payload: Dict[str, Any], actor_role: str, actor_id: Optional[str] = None) -> Dict[str, Any]:
        work_order_id = str(payload.get("work_order_id") or "").strip()
        if not work_order_id:
            raise ValueError("work_order_id is required")

        planned = max(0.0, _to_float(payload.get("planned_cost"), default=0.0))
        actual = max(0.0, _to_float(payload.get("actual_cost"), default=0.0))
        variance = 0.0 if planned == 0.0 else round(((actual - planned) / planned) * 100.0, 2)

        anomaly = variance >= 20.0 or (planned > 0.0 and actual >= planned * 1.5)
        reason = "Cost overrun beyond threshold" if anomaly else None

        row = SRSBudgetEventORM(
            work_order_id=work_order_id,
            category=str(payload.get("category") or "general").lower(),
            planned_cost=planned,
            actual_cost=actual,
            variance_percent=variance,
            anomaly_flag=anomaly,
            anomaly_reason=reason,
        )
        db.session.add(row)
        self._append_audit(
            event_type="BUDGET_EVENT_RECORDED",
            actor_role=actor_role,
            actor_id=actor_id,
            entity_type="BUDGET",
            entity_id=str(work_order_id),
            before_state={},
            after_state=self.serialize_budget_event(row),
            reason="FR-21 budget and cost monitoring",
        )
        db.session.commit()
        return {"budget_event": self.serialize_budget_event(row)}

    def budget_summary(self) -> Dict[str, Any]:
        rows = SRSBudgetEventORM.query.all()
        if not rows:
            return {
                "total_events": 0,
                "planned_total": 0.0,
                "actual_total": 0.0,
                "anomalies": 0,
            }

        planned_total = round(sum(float(r.planned_cost or 0.0) for r in rows), 2)
        actual_total = round(sum(float(r.actual_cost or 0.0) for r in rows), 2)
        anomalies = sum(1 for r in rows if r.anomaly_flag)
        return {
            "total_events": len(rows),
            "planned_total": planned_total,
            "actual_total": actual_total,
            "variance_percent": round(0.0 if planned_total == 0 else ((actual_total - planned_total) / planned_total) * 100.0, 2),
            "anomalies": anomalies,
        }

    # ==========================
    # Offline Sync + Override
    # ==========================

    def sync_offline_issues(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        queue = payload.get("issues") or []
        synced = []
        failed = []
        for row in queue:
            try:
                row = dict(row)
                row["captured_offline"] = True
                result = self.report_issue(row)
                issue_id = result["issue"]["issue_id"]
                issue = self._get_issue(issue_id)
                issue.synced_at = datetime.utcnow()
                db.session.commit()
                synced.append({"issue_id": issue_id})
            except Exception as exc:  # pragma: no cover - defensive
                db.session.rollback()
                failed.append({"error": str(exc)})

        return {"synced_count": len(synced), "failed_count": len(failed), "synced": synced, "failed": failed}

    def manual_override(
        self,
        payload: Dict[str, Any],
        actor_role: str,
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        target_type = str(payload.get("target_type") or "").strip().upper()
        target_id = str(payload.get("target_id") or "").strip()
        field = str(payload.get("field") or "").strip()
        value = payload.get("value")
        reason = str(payload.get("reason") or "Manual override").strip()

        if target_type == "ISSUE":
            issue = self._get_issue(target_id)
            before = self.serialize_issue(issue)
            if field == "status":
                issue.status = _normalize_status(str(value))
            elif field == "priority_tier":
                issue.priority_tier = str(value).upper()
            elif field == "is_emergency":
                issue.is_emergency = bool(value)
                if issue.is_emergency and not issue.escalated_at:
                    issue.escalated_at = datetime.utcnow()
            else:
                setattr(issue, field, value)

            self._append_issue_event(
                issue_public_id=issue.public_id,
                from_status=_normalize_status(before.get("status", "")),
                to_status=_normalize_status(issue.status),
                actor_role=actor_role,
                actor_id=actor_id,
                notes=reason,
                metadata={"manual_override": True, "field": field},
            )
            self._append_audit(
                event_type="MANUAL_OVERRIDE",
                actor_role=actor_role,
                actor_id=actor_id,
                entity_type="ISSUE",
                entity_id=issue.public_id,
                before_state=before,
                after_state=self.serialize_issue(issue),
                reason=reason,
            )
            db.session.commit()
            return {"target": "ISSUE", "entity": self.serialize_issue(issue)}

        if target_type == "WORK_ORDER":
            wo = self._get_work_order(target_id)
            before = self.serialize_work_order(wo)
            if field == "status":
                wo.status = str(value).upper()
            else:
                setattr(wo, field, value)
            self._append_audit(
                event_type="MANUAL_OVERRIDE",
                actor_role=actor_role,
                actor_id=actor_id,
                entity_type="WORK_ORDER",
                entity_id=wo.work_order_id,
                before_state=before,
                after_state=self.serialize_work_order(wo),
                reason=reason,
            )
            db.session.commit()
            return {"target": "WORK_ORDER", "entity": self.serialize_work_order(wo)}

        raise ValueError("Unsupported target_type")

    # ==========================
    # Serialization Helpers
    # ==========================

    def serialize_issue(self, issue: SRSIssueORM) -> Dict[str, Any]:
        return {
            "issue_id": issue.public_id,
            "source": issue.source,
            "title": issue.title,
            "description": issue.description,
            "category": issue.category,
            "location": {"lat": issue.lat, "lon": issue.lon, "ward": issue.ward},
            "status": _normalize_status(issue.status),
            "severity": issue.severity,
            "risk_level": issue.risk_level,
            "priority_tier": issue.priority_tier,
            "priority_score": round(float(issue.priority_score or 0.0), 2),
            "duplicate_of_issue_id": issue.duplicate_of_issue_id,
            "fraud_score": round(float(issue.fraud_score or 0.0), 3),
            "is_emergency": bool(issue.is_emergency),
            "accessibility_flag": bool(issue.accessibility_flag),
            "work_order_id": issue.work_order_id,
            "sla_deadline": issue.sla_deadline.isoformat() if issue.sla_deadline else None,
            "captured_offline": bool(issue.captured_offline),
            "synced_at": issue.synced_at.isoformat() if issue.synced_at else None,
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
        }

    def serialize_issue_event(self, event: SRSIssueEventORM) -> Dict[str, Any]:
        return {
            "issue_id": event.issue_public_id,
            "from_status": event.from_status,
            "to_status": event.to_status,
            "actor_role": event.actor_role,
            "actor_id": event.actor_id,
            "notes": event.notes,
            "metadata": _safe_json_loads(event.metadata_json, default={}),
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }

    def serialize_work_order(self, wo: SRSWorkOrderORM) -> Dict[str, Any]:
        return {
            "work_order_id": wo.work_order_id,
            "issue_id": wo.issue_public_id,
            "status": wo.status,
            "contractor_id": wo.contractor_id,
            "assigned_team": wo.assigned_team,
            "sla_hours": wo.sla_hours,
            "due_at": wo.due_at.isoformat() if wo.due_at else None,
            "estimated_cost": round(float(wo.estimated_cost or 0.0), 2),
            "actual_cost": round(float(wo.actual_cost or 0.0), 2),
            "quality_score": round(float(wo.quality_score or 0.0), 2) if wo.quality_score is not None else None,
            "payment_status": wo.payment_status,
        }

    def serialize_contractor(self, contractor: SRSContractorORM) -> Dict[str, Any]:
        return {
            "contractor_id": contractor.contractor_id,
            "name": contractor.name,
            "specialization": contractor.specialization,
            "availability_status": contractor.availability_status,
            "scores": {
                "sla_adherence": round(float(contractor.sla_adherence_score or 0.0), 2),
                "repair_quality": round(float(contractor.repair_quality_score or 0.0), 2),
                "durability": round(float(contractor.durability_score or 0.0), 2),
                "reliability": round(float(contractor.reliability_score or 0.0), 2),
            },
            "total_jobs": int(contractor.total_jobs or 0),
            "blacklisted": bool(contractor.blacklisted),
        }

    def serialize_asset(self, asset: SRSAssetORM) -> Dict[str, Any]:
        return {
            "asset_id": asset.asset_id,
            "asset_type": asset.asset_type,
            "ward": asset.ward,
            "health_score": round(float(asset.health_score or 0.0), 2),
            "predicted_failure_days": int(asset.predicted_failure_days or 0),
            "criticality": asset.criticality,
            "maintenance_status": asset.maintenance_status,
            "location": {"lat": asset.lat, "lon": asset.lon},
            "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
        }

    def serialize_utility(self, utility: SRSUtilityMapORM) -> Dict[str, Any]:
        return {
            "utility_id": utility.utility_id,
            "utility_type": utility.utility_type,
            "ward": utility.ward,
            "depth_m": round(float(utility.depth_m or 0.0), 2),
            "active": bool(utility.active),
            "geometry": _safe_json_loads(utility.geometry_json, default=[]),
        }

    def serialize_budget_event(self, row: SRSBudgetEventORM) -> Dict[str, Any]:
        return {
            "id": row.id,
            "work_order_id": row.work_order_id,
            "category": row.category,
            "planned_cost": round(float(row.planned_cost or 0.0), 2),
            "actual_cost": round(float(row.actual_cost or 0.0), 2),
            "variance_percent": round(float(row.variance_percent or 0.0), 2),
            "anomaly_flag": bool(row.anomaly_flag),
            "anomaly_reason": row.anomaly_reason,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    def serialize_audit(self, row: SRSAuditLogORM) -> Dict[str, Any]:
        return {
            "id": row.id,
            "event_type": row.event_type,
            "actor_role": row.actor_role,
            "actor_id": row.actor_id,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "reason": row.reason,
            "immutable_hash": row.immutable_hash,
            "previous_hash": row.previous_hash,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    # ==========================
    # Internal Methods
    # ==========================

    def _get_issue(self, issue_public_id: str) -> SRSIssueORM:
        issue = SRSIssueORM.query.filter_by(public_id=issue_public_id).first()
        if issue is None:
            raise ValueError("Issue not found")
        return issue

    def _get_work_order(self, work_order_id: str) -> SRSWorkOrderORM:
        row = SRSWorkOrderORM.query.filter_by(work_order_id=work_order_id).first()
        if row is None:
            raise ValueError("Work order not found")
        return row

    def _get_contractor(self, contractor_id: str) -> SRSContractorORM:
        if not contractor_id:
            raise ValueError("contractor_id is required")
        contractor = SRSContractorORM.query.filter_by(contractor_id=contractor_id).first()
        if contractor is None:
            raise ValueError("Contractor not found")
        return contractor

    def _append_issue_event(
        self,
        issue_public_id: str,
        from_status: Optional[str],
        to_status: str,
        actor_role: str,
        actor_id: Optional[str],
        notes: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        db.session.add(
            SRSIssueEventORM(
                issue_public_id=issue_public_id,
                from_status=from_status,
                to_status=_normalize_status(to_status),
                actor_role=actor_role,
                actor_id=actor_id,
                notes=notes,
                metadata_json=json.dumps(metadata or {}),
            )
        )

    def _append_audit(
        self,
        event_type: str,
        actor_role: str,
        actor_id: Optional[str],
        entity_type: str,
        entity_id: str,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        reason: Optional[str] = None,
    ) -> None:
        prev = SRSAuditLogORM.query.order_by(SRSAuditLogORM.id.desc()).first()
        prev_hash = prev.immutable_hash if prev else ""
        payload = json.dumps(
            {
                "event_type": event_type,
                "actor_role": actor_role,
                "actor_id": actor_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "before_state": before_state,
                "after_state": after_state,
                "reason": reason,
                "ts": datetime.utcnow().isoformat(),
            },
            sort_keys=True,
        )
        immutable_hash = hashlib.sha256((prev_hash + payload).encode("utf-8")).hexdigest()
        db.session.add(
            SRSAuditLogORM(
                event_type=event_type,
                actor_role=actor_role,
                actor_id=actor_id,
                entity_type=entity_type,
                entity_id=entity_id,
                before_state=json.dumps(before_state),
                after_state=json.dumps(after_state),
                reason=reason,
                previous_hash=prev_hash or None,
                immutable_hash=immutable_hash,
            )
        )

    def _localized_message(self, language: str, key: str) -> str:
        lang = (language or "en").lower()
        base = LANGUAGE_MESSAGES.get(lang, LANGUAGE_MESSAGES["en"])
        return base.get(key, LANGUAGE_MESSAGES["en"].get(key, "Status updated."))

    def _select_contractor(self, preferred_id: Optional[str], category: str) -> Optional[SRSContractorORM]:
        if preferred_id:
            candidate = SRSContractorORM.query.filter_by(contractor_id=preferred_id).first()
            if candidate and not candidate.blacklisted and candidate.availability_status == "AVAILABLE":
                return candidate

        pool = (
            SRSContractorORM.query
            .filter(SRSContractorORM.blacklisted.is_(False))
            .filter(SRSContractorORM.availability_status == "AVAILABLE")
            .order_by(SRSContractorORM.reliability_score.desc(), SRSContractorORM.total_jobs.asc())
            .all()
        )
        if not pool:
            return None

        cat = (category or "").lower()
        for row in pool:
            if row.specialization.lower() == cat:
                return row
        return pool[0]

    def _update_contractor_score(self, contractor: SRSContractorORM, work_order: SRSWorkOrderORM, quality_score: float) -> None:
        previous_jobs = float(contractor.total_jobs or 0)
        total_jobs = previous_jobs + 1.0
        contractor.total_jobs = int(total_jobs)

        sla_score = 100.0
        if work_order.due_at and work_order.completed_at and work_order.completed_at > work_order.due_at:
            delay_hours = (work_order.completed_at - work_order.due_at).total_seconds() / 3600.0
            sla_score = max(0.0, 100.0 - delay_hours * 2.5)

        durability_score = max(0.0, 100.0 - float(work_order.repeat_failure_count or 0) * 20.0)
        contractor.sla_adherence_score = _running_avg(contractor.sla_adherence_score, sla_score, previous_jobs)
        contractor.repair_quality_score = _running_avg(contractor.repair_quality_score, quality_score, previous_jobs)
        contractor.durability_score = _running_avg(contractor.durability_score, durability_score, previous_jobs)
        contractor.reliability_score = round(
            (contractor.sla_adherence_score * 0.35)
            + (contractor.repair_quality_score * 0.4)
            + (contractor.durability_score * 0.25),
            2,
        )
        contractor.blacklisted = contractor.reliability_score < 40.0 and contractor.total_jobs >= 5

    def _detect_duplicate(
        self,
        category: str,
        lat: Optional[float],
        lon: Optional[float],
        title: str,
        description: str,
        evidence_urls: List[str],
    ) -> Tuple[Optional[str], float]:
        query = SRSIssueORM.query.filter(SRSIssueORM.category == category)
        if lat is not None and lon is not None:
            query = query.filter(
                SRSIssueORM.lat.between(lat - 0.03, lat + 0.03),
                SRSIssueORM.lon.between(lon - 0.03, lon + 0.03),
            )
        candidates = query.order_by(SRSIssueORM.created_at.desc()).limit(80).all()

        best_id = None
        best_score = 0.0
        new_text = f"{title} {description}".strip().lower()
        new_media = {item.lower().split("/")[-1] for item in evidence_urls}

        for candidate in candidates:
            candidate_text = f"{candidate.title} {candidate.description}".lower()
            text_sim = _jaccard_similarity(new_text, candidate_text)
            media_sim = _set_similarity(new_media, {item.lower().split("/")[-1] for item in _safe_json_loads(candidate.evidence_urls, default=[])})
            dist_sim = 0.0
            if lat is not None and lon is not None and candidate.lat is not None and candidate.lon is not None:
                km = _haversine_km(lat, lon, candidate.lat, candidate.lon)
                dist_sim = max(0.0, 1.0 - min(km / 0.5, 1.0))
            score = (text_sim * 0.5) + (dist_sim * 0.4) + (media_sim * 0.1)
            if score > best_score:
                best_score = score
                best_id = candidate.public_id

        if best_score < 0.55:
            return None, round(best_score, 3)
        return best_id, round(best_score, 3)

    def _fraud_score(
        self,
        reporter_id: Optional[str],
        reporter_reputation: float,
        evidence_urls: List[str],
        duplicate_score: float,
        title: str,
        description: str,
        source: str,
        has_location: bool,
    ) -> float:
        score = 0.08
        if not reporter_id:
            score += 0.12
        if reporter_reputation < 0.4:
            score += 0.18
        if not evidence_urls:
            score += 0.20
        if duplicate_score >= 0.85:
            score += 0.20
        if len((title + description).strip()) < 40:
            score += 0.12
        if source == "citizen" and not has_location:
            score += 0.12
        return _clamp(score, 0.0, 1.0)

    def _classify_and_prioritize(
        self,
        category: str,
        title: str,
        description: str,
        source: str,
        reporter_reputation: float,
        fraud_score: float,
    ) -> Tuple[str, str, str, float, List[str]]:
        text = f"{title} {description}".lower()
        severity = "MEDIUM"
        explainability = []

        critical_markers = ["open manhole", "collapsed", "electrocution", "bridge crack", "fire", "flood"]
        high_markers = ["pothole", "leak", "overflow", "broken", "short circuit"]

        if any(marker in text for marker in critical_markers):
            severity = "CRITICAL"
            explainability.append("Critical safety marker detected in complaint text.")
        elif any(marker in text for marker in high_markers):
            severity = "HIGH"
            explainability.append("High-impact infrastructure marker detected.")

        if category in {"safety", "bridge", "emergency"} and severity != "CRITICAL":
            severity = "HIGH"
            explainability.append("Safety category increases severity.")
        if source in {"cctv", "sensor"}:
            explainability.append("Automated source corroborates signal reliability.")
        if fraud_score >= 0.75:
            explainability.append("High fraud risk lowers automatic confidence.")

        safety = {"LOW": 30.0, "MEDIUM": 55.0, "HIGH": 80.0, "CRITICAL": 95.0}[severity]
        usage = {
            "road": 80.0,
            "water": 75.0,
            "drain": 78.0,
            "electricity": 82.0,
            "accessibility": 70.0,
        }.get(category, 60.0)
        cost = {
            "road": 68.0,
            "water": 72.0,
            "bridge": 85.0,
            "electricity": 76.0,
            "drain": 74.0,
        }.get(category, 58.0)

        score = (safety * 0.5) + (usage * 0.3) + (cost * 0.2)
        score += 4.0 if source in {"sensor", "cctv"} else 0.0
        score -= (1.0 - _clamp(reporter_reputation, 0.0, 1.0)) * 4.0
        score -= fraud_score * 10.0
        score = _clamp(score, 0.0, 100.0)

        if score >= 80:
            tier = "CRITICAL"
        elif score >= 65:
            tier = "HIGH"
        elif score >= 45:
            tier = "MEDIUM"
        else:
            tier = "LOW"

        risk_level = tier
        explainability.append(f"Priority score computed as {round(score, 2)} from safety/usage/cost weighted impacts.")
        return severity, risk_level, tier, round(score, 2), explainability

    def _detect_emergency(self, title: str, description: str, category: str, severity: str) -> Tuple[bool, Optional[str]]:
        text = f"{title} {description}".lower()
        markers = [
            "open manhole",
            "collapsed road",
            "bridge crack",
            "fire",
            "electrocution",
            "live wire",
            "major flooding",
        ]
        for marker in markers:
            if marker in text:
                return True, marker
        if severity == "CRITICAL":
            return True, "critical severity classification"
        if category in {"safety", "bridge"} and "danger" in text:
            return True, "safety critical risk context"
        return False, None

    def _impact_breakdown(self, priority_score: float, category: str, severity: str) -> Tuple[float, float, float]:
        safety = _clamp(priority_score + (8 if severity == "CRITICAL" else 0), 0, 100)
        usage = _clamp(priority_score + (5 if category in {"road", "water", "electricity"} else -5), 0, 100)
        cost = _clamp(priority_score + (6 if category in {"bridge", "water"} else -3), 0, 100)
        return round(safety, 2), round(usage, 2), round(cost, 2)

    def _category_from_source(self, source_type: str) -> str:
        mapping = {
            "sensor": "water",
            "cctv": "road",
            "smartphone": "road",
            "dashcam": "road",
        }
        return mapping.get(source_type.lower(), "other")


def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _to_list_str(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _issue_id() -> str:
    return f"ISS-{uuid.uuid4().hex[:10].upper()}"


def _work_order_id() -> str:
    return f"WO-{uuid.uuid4().hex[:10].upper()}"


def _normalize_status(status: str) -> str:
    return str(status or "RECEIVED").strip().upper()


def _safe_json_loads(raw: Optional[str], default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _running_avg(current: Optional[float], new_value: float, n_prior: float) -> float:
    base = float(current or 0.0)
    return round(((base * n_prior) + new_value) / max(1.0, n_prior + 1.0), 2)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _tokenize(text: str) -> set:
    return {token for token in text.lower().split() if token.isalpha() or token.isalnum()}


def _jaccard_similarity(text_a: str, text_b: str) -> float:
    a = _tokenize(text_a)
    b = _tokenize(text_b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _set_similarity(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
