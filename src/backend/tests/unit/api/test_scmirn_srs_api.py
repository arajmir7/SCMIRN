from __future__ import annotations

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def client():
    app = create_app("testing")
    with app.app_context():
        db.create_all()

    with app.test_client() as test_client:
        yield test_client

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_srs_issue_lifecycle_workflow(client):
    report = client.post(
        "/api/v1/scmirn/issues/report",
        json={
            "source": "citizen",
            "title": "Open manhole near school gate",
            "description": "Open manhole causing danger for children near main school crossing.",
            "category": "safety",
            "lat": 28.6139,
            "lon": 77.2090,
            "evidence_urls": ["https://example.com/open-manhole.jpg"],
            "reporter": {"id": "citizen-1", "language": "en", "reputation": 0.9},
        },
    )
    assert report.status_code == 201
    report_json = report.get_json()
    assert report_json["success"] is True
    assert report_json["issue"]["status"] == "RECEIVED"
    assert report_json["issue"]["is_emergency"] is True

    issue_id = report_json["issue"]["issue_id"]

    transition = client.post(
        f"/api/v1/scmirn/issues/{issue_id}/transition",
        json={"to_status": "VERIFIED", "notes": "Validated by control room"},
        headers={"X-Actor-Role": "engineer", "X-Actor-Id": "eng-1"},
    )
    assert transition.status_code == 200
    assert transition.get_json()["issue"]["status"] == "VERIFIED"

    wo = client.post(
        "/api/v1/scmirn/work-orders/generate",
        json={"issue_id": issue_id, "estimated_cost": 12000, "warranty_days": 120},
        headers={"X-Actor-Role": "engineer", "X-Actor-Id": "eng-1"},
    )
    assert wo.status_code == 201
    work_order_id = wo.get_json()["work_order"]["work_order_id"]

    assign = client.post(
        f"/api/v1/scmirn/work-orders/{work_order_id}/assign",
        json={"assigned_team": "Ward Team A", "sla_hours": 12},
        headers={"X-Actor-Role": "dispatcher", "X-Actor-Id": "dispatch-1"},
    )
    assert assign.status_code == 200
    assert assign.get_json()["work_order"]["status"] == "ASSIGNED"

    verify = client.post(
        f"/api/v1/scmirn/work-orders/{work_order_id}/verify",
        json={
            "ai_quality_score": 92,
            "sensor_health_delta": 26,
            "inspector_validated": True,
            "citizen_validated": True,
            "actual_cost": 11800,
        },
        headers={"X-Actor-Role": "qa_inspector", "X-Actor-Id": "qa-1"},
    )
    assert verify.status_code == 200
    verify_json = verify.get_json()
    assert verify_json["passed"] is True
    assert verify_json["issue"]["status"] in {"CLOSED", "RESOLVED"}

    lifecycle = client.get(f"/api/v1/scmirn/issues/{issue_id}/lifecycle")
    assert lifecycle.status_code == 200
    timeline = lifecycle.get_json()["timeline"]
    statuses = [item["to_status"] for item in timeline]
    assert "RECEIVED" in statuses
    assert "VERIFIED" in statuses
    assert "ASSIGNED" in statuses


def test_duplicate_and_fraud_detection(client):
    first = client.post(
        "/api/v1/scmirn/issues/report",
        json={
            "source": "citizen",
            "title": "Large pothole near bus stop",
            "description": "Pothole on main road near ward bus stop causing vehicle damage.",
            "category": "road",
            "lat": 28.612,
            "lon": 77.21,
            "evidence_urls": ["https://example.com/p1.jpg"],
            "reporter": {"id": "citizen-2", "language": "en", "reputation": 0.8},
        },
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/scmirn/issues/report",
        json={
            "source": "citizen",
            "title": "Large pothole near bus stop",
            "description": "Same pothole, still unresolved.",
            "category": "road",
            "lat": 28.6121,
            "lon": 77.2101,
            "evidence_urls": [],
            "reporter": {"language": "en", "reputation": 0.1},
        },
    )
    assert second.status_code == 201
    second_json = second.get_json()
    assert second_json["duplicate_detection"]["is_duplicate"] is True
    assert second_json["fraud_detection"]["fraud_score"] > 0.4


def test_asset_flood_traffic_utility_budget_paths(client):
    asset = client.post(
        "/api/v1/scmirn/assets/health",
        json={
            "asset_id": "ASSET-001",
            "asset_type": "bridge",
            "ward": "Ward-11",
            "age_years": 24,
            "degradation_rate": 0.55,
            "usage_index": 82,
            "sensor_score": 48,
            "criticality": "HIGH",
        },
    )
    assert asset.status_code == 200
    assert asset.get_json()["asset"]["health_score"] <= 100

    schedule = client.get("/api/v1/scmirn/assets/maintenance-schedule?horizon_days=180")
    assert schedule.status_code == 200
    assert isinstance(schedule.get_json()["maintenance_plan"], list)

    flood = client.post(
        "/api/v1/scmirn/risk/flood-predict",
        json={"rainfall_mm": 210, "drain_capacity_pct": 40, "blockage_index": 0.7, "soil_saturation": 0.8},
    )
    assert flood.status_code == 200
    assert flood.get_json()["risk_band"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    traffic = client.post(
        "/api/v1/scmirn/traffic/impact-simulate",
        json={"baseline_vehicles_per_hour": 9000, "lane_closure_pct": 50, "work_duration_hours": 10, "peak_hour": True},
    )
    assert traffic.status_code == 200
    assert traffic.get_json()["expected_delay_minutes"] > 0

    register_utility = client.post(
        "/api/v1/scmirn/utilities/register",
        json={
            "utility_id": "UTIL-001",
            "utility_type": "water",
            "ward": "Ward-11",
            "depth_m": 1.2,
            "geometry": [{"lat": 28.61, "lon": 77.20}],
        },
    )
    assert register_utility.status_code == 201

    pre_dig = client.post(
        "/api/v1/scmirn/utilities/pre-dig-verify",
        json={"lat": 28.61005, "lon": 77.20005, "radius_m": 30},
    )
    assert pre_dig.status_code == 200
    assert pre_dig.get_json()["clearance_status"] == "HOLD"

    report = client.post(
        "/api/v1/scmirn/issues/report",
        json={
            "source": "citizen",
            "title": "Water leakage near lane",
            "description": "Persistent leakage increasing every day.",
            "category": "water",
            "lat": 28.62,
            "lon": 77.22,
            "reporter": {"id": "citizen-3", "reputation": 0.7},
        },
    )
    issue_id = report.get_json()["issue"]["issue_id"]
    wo = client.post(
        "/api/v1/scmirn/work-orders/generate",
        json={"issue_id": issue_id, "estimated_cost": 10000, "warranty_days": 90},
        headers={"X-Actor-Role": "engineer"},
    )
    wo_id = wo.get_json()["work_order"]["work_order_id"]

    budget_event = client.post(
        "/api/v1/scmirn/finance/budget-event",
        json={"work_order_id": wo_id, "category": "water", "planned_cost": 10000, "actual_cost": 18000},
        headers={"X-Actor-Role": "finance_officer", "X-Actor-Id": "fin-1"},
    )
    assert budget_event.status_code == 201
    assert budget_event.get_json()["budget_event"]["anomaly_flag"] is True

    budget_summary = client.get("/api/v1/scmirn/finance/budget-summary")
    assert budget_summary.status_code == 200
    assert budget_summary.get_json()["anomalies"] >= 1


def test_offline_sync_manual_override_and_traceability(client):
    sync = client.post(
        "/api/v1/scmirn/sync/offline-issues",
        json={
            "issues": [
                {
                    "source": "citizen",
                    "title": "Streetlight not working",
                    "description": "Three streetlights are off in the colony lane.",
                    "category": "electricity",
                    "lat": 28.63,
                    "lon": 77.24,
                    "reporter": {"id": "citizen-4", "language": "hi", "reputation": 0.6},
                    "captured_at": "2026-02-10T09:10:00Z",
                }
            ]
        },
    )
    assert sync.status_code == 200
    assert sync.get_json()["synced_count"] == 1
    issue_id = sync.get_json()["synced"][0]["issue_id"]

    forbidden = client.post(
        "/api/v1/scmirn/governance/manual-override",
        json={"target_type": "ISSUE", "target_id": issue_id, "field": "status", "value": "VERIFIED"},
        headers={"X-Actor-Role": "ward_staff"},
    )
    assert forbidden.status_code == 403

    allowed = client.post(
        "/api/v1/scmirn/governance/manual-override",
        json={
            "target_type": "ISSUE",
            "target_id": issue_id,
            "field": "status",
            "value": "VERIFIED",
            "reason": "Emergency governance decision",
        },
        headers={"X-Actor-Role": "commissioner", "X-Actor-Id": "comm-1"},
    )
    assert allowed.status_code == 200
    assert allowed.get_json()["entity"]["status"] == "VERIFIED"

    audit = client.get("/api/v1/scmirn/governance/audit-logs?limit=20")
    assert audit.status_code == 200
    assert audit.get_json()["count"] >= 1

    traceability = client.get("/api/v1/scmirn/traceability")
    assert traceability.status_code == 200
    trace_json = traceability.get_json()
    assert "FR-24" in trace_json["functional_requirements"]
