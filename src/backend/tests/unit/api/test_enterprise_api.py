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


def test_city_health_score_endpoint(client):
    response = client.get("/api/v1/enterprise/executive/city-health-score?city_id=demo-metro")
    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload["city_health_score"], int)
    assert 0 <= payload["city_health_score"] <= 100
    assert "components" in payload
    assert set(payload["components"].keys()) == {
        "infrastructure",
        "citizen_satisfaction",
        "emergency_readiness",
        "economic_impact",
    }


def test_risk_radar_endpoint(client):
    response = client.get("/api/v1/enterprise/executive/risk-radar?city_id=demo-metro")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["visualization"]["mode"] == "3D_GLOBE"
    assert len(payload["nodes"]) > 0
    first = payload["nodes"][0]
    assert "forecasts" in first
    assert {"7d", "30d", "90d"} <= set(first["forecasts"].keys())


def test_crisis_sandbox_endpoint(client):
    response = client.post(
        "/api/v1/enterprise/executive/crisis-sandbox/simulate",
        json={
            "city_id": "demo-metro",
            "events": [
                {"event_type": "EARTHQUAKE", "intensity": 0.72, "duration_hours": 10},
                {"event_type": "CYBERATTACK", "intensity": 0.64, "duration_hours": 8},
            ],
            "population_exposed": 850000,
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["outcomes"]["affected_citizens"] > 0
    assert len(payload["cascade_effects"]) == 12


def test_roi_calculator_endpoint(client):
    response = client.post(
        "/api/v1/enterprise/executive/roi-calculate",
        json={
            "horizon_years": 5,
            "discount_rate": 0.08,
            "baseline_losses": {
                "infrastructure_failures": 55000000,
                "emergency_response_overrun": 21000000,
                "compliance_penalties": 9000000,
            },
            "investments": [
                {
                    "initiative": "Predictive Maintenance Upgrade",
                    "capex": 22000000,
                    "opex_annual": 2600000,
                    "expected_loss_reduction_percent": 24,
                    "implementation_months": 6,
                },
                {
                    "initiative": "Automated Incident Orchestration",
                    "capex": 12000000,
                    "opex_annual": 1500000,
                    "expected_loss_reduction_percent": 18,
                    "implementation_months": 4,
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    summary = payload["summary"]
    assert summary["baseline_annual_losses_inr"] > 0
    assert summary["combined_loss_reduction_percent"] > 0
    assert "npv_inr" in summary


def test_connector_catalog_and_authorize_endpoint(client):
    catalog = client.get("/api/v1/enterprise/integrations/connectors")
    assert catalog.status_code == 200
    catalog_json = catalog.get_json()
    assert catalog_json["count"] >= 20

    authorize = client.post(
        "/api/v1/enterprise/integrations/connectors/salesforce/authorize",
        json={
            "tenant_id": "city-of-demo",
            "redirect_uri": "https://example.gov/oauth/callback",
            "scopes": ["read", "write"],
        },
    )
    assert authorize.status_code == 200
    auth_json = authorize.get_json()
    assert auth_json["connector_id"] == "salesforce"
    assert "authorization_url" in auth_json


def test_kill_switch_endpoint(client):
    response = client.post(
        "/api/v1/enterprise/security/kill-switch",
        json={
            "node_ids": ["substation-11", "iot-gateway-22"],
            "compromise_type": "MALWARE",
            "preserve_services": ["EMERGENCY_DISPATCH", "HOSPITAL_POWER"],
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["isolated_nodes"]) == 2
    assert payload["containment"]["zero_trust_reauth_enforced"] is True


def test_briefing_dispatch_uses_real_sender_contract(client, monkeypatch):
    import app.api.v1.enterprise as enterprise_api

    monkeypatch.setattr(enterprise_api, "resolve_email_provider", lambda _cfg: "sendgrid")

    def fake_send_briefing_email(
        *,
        config,
        recipient,
        subject,
        body_text,
        attachment_bytes=None,
        attachment_filename=None,
    ):
        assert subject.startswith("[SCMIRN] Daily Executive Briefing")
        assert isinstance(body_text, str) and len(body_text) > 20
        return {
            "status": "SENT",
            "provider": "sendgrid",
            "message_id": f"msg-{recipient}",
        }

    monkeypatch.setattr(enterprise_api, "send_briefing_email", fake_send_briefing_email)

    response = client.post(
        "/api/v1/enterprise/executive/briefings/generate",
        json={
            "city_id": "demo-metro",
            "recipients": ["ceo@example.org", "ciso@example.org"],
            "include_pdf": True,
            "include_recommendations": True,
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["email_dispatch"]["provider"] == "sendgrid"
    assert payload["email_dispatch"]["status"] == "SENT"
    assert payload["email_dispatch"]["sent_count"] == 2
    assert payload["email_dispatch"]["failed_count"] == 0
    assert all(item["status"] == "SENT" for item in payload["email_dispatch"]["recipients"])
