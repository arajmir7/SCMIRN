from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import text

from app import create_app
from app.config import validate_production_config
from app.extensions import db
from app.api.v1 import routes as health_routes
from app.infrastructure.database.models import IssueORM
from app.source_routing.audit_chain import append_event, verify_chain
from app.source_routing.audit_models import AuditEvent
from app.source_routing.models import (
    Authority,
    GovernmentService,
    OfficialSource,
    RouteDecision,
    RouteRule,
    utcnow_naive,
)
from app.source_routing.registry_seed import seed_routing_registry
from app.source_routing.retention import purge_expired_route_decisions


@pytest.fixture
def routing_app():
    app = create_app("testing")
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_routing_registry()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def routing_client(routing_app):
    return routing_app.test_client()


def _triage(client, description="UPI fraud was reported", headers=None, consent=True):
    payload = {"description": description}
    if consent:
        payload["consent_to_process"] = True
    return client.post("/api/v1/triage", json=payload, headers=headers or {})


def _add_synthetic_route(
    routing_app,
    application_channel="https://example.gov.test/route",
    geography=None,
):
    with routing_app.app_context():
        now = utcnow_naive()
        source = OfficialSource(
            source_key="synthetic-test-source", version=1, authority="Synthetic test authority",
            title="Synthetic route source fixture", source_type="TEST_FIXTURE", jurisdiction="TEST",
            canonical_url="https://example.gov.test/route", document_hash="a" * 64,
            verification_status="VERIFIED", retrieved_at=now, verified_at=now,
        )
        db.session.add(source)
        db.session.flush()
        authority = Authority(
            authority_key="synthetic-test-authority", version=1, canonical_name="Synthetic test authority",
            authority_level="OTHER", jurisdiction={"country": "TEST"}, official_source_id=source.id,
            status="ACTIVE", created_at=now,
        )
        db.session.add(authority)
        db.session.flush()
        service = GovernmentService(
            service_key="synthetic-test-service", version=1, canonical_name="Synthetic test service",
            authority_id=authority.id, authority_level="OTHER", jurisdiction={"country": "TEST"},
            geography=geography or {"scope": "national"}, official_url="https://example.gov.test/route",
            application_channel=application_channel, integration_mode="OFFICIAL_HANDOFF_ONLY",
            status="ACTIVE", created_at=now,
        )
        service.sources.append(source)
        db.session.add(service)
        db.session.flush()
        db.session.add(RouteRule(
            rule_key="synthetic-test-rule", version=1, issue_type="SYNTHETIC_TEST",
            match_terms=["synthetic route fixture"], exclusion_terms=[], authority_id=authority.id,
            service_version_id=service.id, source_ids=[source.id], priority=100,
            status="ACTIVE", created_at=now,
        ))
        db.session.commit()


def test_consent_is_required_and_raw_description_is_not_persisted(routing_app, routing_client):
    denied = _triage(routing_client, consent=False)
    assert denied.status_code == 400
    description = "Synthetic online payment fraud record 4821"
    accepted = _triage(routing_client, description)
    assert accepted.status_code == 200
    payload = accepted.get_json()
    assert payload["outcome"] == "ROUTE_UNCERTAIN"
    assert payload["submission_status"] == "NOT_SUBMITTED"
    assert payload["official_reference"] is None
    assert payload["official_handoff"] is None
    with routing_app.app_context():
        decision = db.session.get(RouteDecision, payload["decision_id"])
        assert description not in str(decision.input_facts)
        assert description not in str(decision.output)
        assert AuditEvent.query.count() == 1
        assert verify_chain()["valid"] is True


def test_idempotency_replay_and_conflict(routing_client):
    headers = {"Idempotency-Key": "same-synthetic-request"}
    first = _triage(routing_client, headers=headers)
    replay = _triage(routing_client, headers=headers)
    conflict = _triage(routing_client, "different input", headers=headers)
    assert first.status_code == replay.status_code == 200
    assert first.get_json()["decision_id"] == replay.get_json()["decision_id"]
    assert conflict.status_code == 409


def test_emergency_signal_abstains_from_authority(routing_client):
    response = _triage(routing_client, "Someone is in immediate danger now")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["outcome"] == "URGENT_HUMAN_HELP_REQUIRED"
    assert payload["urgent_human_help_required"] is True
    assert payload["urgency"] == "UNASSESSED"
    assert payload["urgency_signal"] == "POSSIBLE_IMMEDIATE_DANGER"
    assert payload["authority"] is None


def test_cyber_portal_draft_is_gated_and_four_verified_services_are_listed(routing_client):
    sources = routing_client.get("/api/v1/services")
    source = routing_client.get("/api/v1/sources/national-cybercrime-portal-financial-fraud-1930")
    evidence = routing_client.post("/api/v1/evidence/check", json={"service_id": "online-financial-cyber-fraud-reporting"})
    assert sources.status_code == 200
    payload = sources.get_json()
    assert payload["count"] == 4
    assert {item["service_id"] for item in payload["items"]} == {
        "national-consumer-helpline",
        "cpgrams-public-service-grievance",
        "rti-online-central-public-authority",
        "nalsa-telelaw-legal-help",
    }
    assert source.status_code == 200
    assert source.get_json()["verification_status"] == "DRAFT"
    assert source.get_json()["document_hash"] is None
    assert evidence.status_code == 200
    assert evidence.get_json()["status"] == "SOURCE_UNVERIFIED"


@pytest.mark.parametrize(
    ("description", "service_id"),
    [
        ("I need help with a consumer grievance", "national-consumer-helpline"),
        ("I need a public grievance for government service delivery", "cpgrams-public-service-grievance"),
        ("I need an RTI request to a central ministry", "rti-online-central-public-authority"),
        ("I need NALSA legal aid", "nalsa-telelaw-legal-help"),
    ],
)
def test_official_handoff_candidates_are_explicit_and_non_submitting(
    routing_client, description, service_id
):
    response = _triage(routing_client, description)
    assert response.status_code == 200
    result = response.get_json()
    assert result["outcome"] == "OFFICIAL_HANDOFF_ONLY"
    assert result["service"]["service_id"] == service_id
    assert result["submission_status"] == "NOT_SUBMITTED"
    assert result["official_reference"] is None
    assert result["official_handoff"]["url"].startswith("https://")


def test_central_rti_handoff_excludes_state_and_nct_delhi_requests(routing_client):
    response = _triage(
        routing_client,
        "I need an RTI request to a state public authority in NCT Delhi",
    )
    assert response.status_code == 200
    result = response.get_json()
    assert result["outcome"] == "ROUTE_UNCERTAIN"
    assert result["service"] is None


def test_official_catalog_import_is_idempotent(routing_app):
    with routing_app.app_context():
        before = (
            OfficialSource.query.count(),
            Authority.query.count(),
            GovernmentService.query.count(),
            RouteRule.query.count(),
        )
        seed_routing_registry()
        seed_routing_registry()
        after = (
            OfficialSource.query.count(),
            Authority.query.count(),
            GovernmentService.query.count(),
            RouteRule.query.count(),
        )
        assert after == before


def test_verified_synthetic_source_can_render_only_handoff_not_submission(routing_app, routing_client):
    _add_synthetic_route(routing_app)
    response = _triage(routing_client, "I need a synthetic route fixture", headers={"Idempotency-Key": "synthetic-handoff"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["outcome"] == "OFFICIAL_HANDOFF_ONLY"
    assert payload["urgency"] == "UNASSESSED"
    assert payload["urgency_signal"] == "NONE_DETECTED"
    assert payload["official_handoff"]["url"] == "https://example.gov.test/route"
    assert payload["submission_status"] == "NOT_SUBMITTED"
    assert payload["official_reference"] is None


def test_verified_source_does_not_authorize_handoff_to_another_host(routing_app, routing_client):
    _add_synthetic_route(routing_app, application_channel="https://unverified.example/submit")

    response = _triage(routing_client, "I need a synthetic route fixture")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["outcome"] == "ROUTE_UNCERTAIN"
    assert payload["authority"] is None
    assert payload["official_handoff"] is None


@pytest.mark.parametrize(
    ("geography", "state", "district", "expected"),
    [
        ({"scope": "state", "states": ["Test State"]}, None, None, "ROUTE_UNCERTAIN"),
        ({"scope": "state", "states": ["Test State"]}, "Other State", None, "ROUTE_UNCERTAIN"),
        ({"scope": "state", "states": ["Test State"]}, "Test State", None, "OFFICIAL_HANDOFF_ONLY"),
        (
            {"scope": "district", "states": ["Test State"], "districts": ["North District"]},
            "Test State", None, "ROUTE_UNCERTAIN",
        ),
        (
            {"scope": "district", "states": ["Test State"], "districts": ["North District"]},
            "Test State", "South District", "ROUTE_UNCERTAIN",
        ),
        (
            {"scope": "district", "states": ["Test State"], "districts": ["North District"]},
            "Test State", "North District", "OFFICIAL_HANDOFF_ONLY",
        ),
    ],
)
def test_local_service_requires_explicit_matching_geography(
    routing_app, routing_client, geography, state, district, expected
):
    _add_synthetic_route(routing_app, geography=geography)
    response = routing_client.post(
        "/api/v1/triage",
        json={
            "description": "I need a synthetic route fixture",
            "state": state,
            "district": district,
            "consent_to_process": True,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["outcome"] == expected
    assert payload["submission_status"] == "NOT_SUBMITTED"
    if expected == "ROUTE_UNCERTAIN":
        assert payload["authority"] is None
        assert payload["official_handoff"] is None


def test_retention_purge_is_dry_runnable_and_audited(routing_app, routing_client):
    payload = _triage(routing_client).get_json()
    with routing_app.app_context():
        decision = db.session.get(RouteDecision, payload["decision_id"])
        decision.retention_until = utcnow_naive() - timedelta(seconds=1)
        db.session.commit()
        dry = purge_expired_route_decisions(dry_run=True)
        assert dry["would_delete"] == 1 and dry["deleted"] == 0
        assert db.session.get(RouteDecision, payload["decision_id"]) is not None
        purged = purge_expired_route_decisions()
        assert purged["deleted"] == 1 and purged["pending"] == 0
        assert db.session.get(RouteDecision, payload["decision_id"]) is None
        assert verify_chain()["valid"] is True


def test_audit_chain_rejects_sensitive_details_and_detects_tampering(routing_app):
    with routing_app.app_context():
        with pytest.raises(ValueError):
            append_event(
                tenant_id="test", actor_id="test-actor", actor_role="test", action="test.write",
                object_type="test", object_id="synthetic", details={"description": "must not persist"},
            )
        event = append_event(
            tenant_id="test", actor_id="test-actor", actor_role="test", action="test.write",
            object_type="test", object_id="synthetic", details={"outcome": "ROUTE_UNCERTAIN"},
        )
        db.session.commit()
        db.session.execute(text("UPDATE audit_events SET action = 'tampered' WHERE sequence = :sequence"), {"sequence": event.sequence})
        db.session.commit()
        assert verify_chain()["valid"] is False


def test_empty_issue_list_does_not_seed_demo_records_in_testing(routing_app, routing_client):
    response = routing_client.get("/api/issues")
    assert response.status_code == 200
    assert response.get_json()["count"] == 0
    with routing_app.app_context():
        assert IssueORM.query.count() == 0


def test_payment_endpoints_do_not_change_funding(routing_app, routing_client):
    with routing_app.app_context():
        issue = IssueORM(
            public_id="synthetic-no-payment", title="Synthetic payment endpoint test",
            description="Synthetic test data only, no real issue.", category="road",
            lat=0, lon=0,
            priority_score=0, priority_tier="low", fund_target=0, fund_collected=0,
            status="reported", media_files="[]", integrity_hash="test",
        )
        db.session.add(issue)
        db.session.commit()
        issue_id = issue.id

    response = routing_client.post("/api/donate", json={"issue_id": issue_id, "amount": 100})
    assert response.status_code == 503
    assert response.get_json()["code"] == "PAYMENTS_NOT_CONFIGURED"
    with routing_app.app_context():
        assert db.session.get(IssueORM, issue_id).fund_collected == 0


def test_production_gate_blocks_legacy_mutations_and_allows_source_routes(routing_app, routing_client):
    routing_app.config["SCMIRN_ENVIRONMENT"] = "production"
    for method, path, kwargs in [
        ("post", "/api/ai-assistant", {"json": {"message": "synthetic"}}),
        ("post", "/api/donate", {"json": {"issue_id": 1, "amount": 100}}),
        ("post", "/api/v1/blockchain/register-issue", {"json": {}}),
        ("post", "/api/report-issue", {"data": {"title": "Synthetic test", "description": "Synthetic test record only"}}),
        ("get", "/api/offices", {}),
    ]:
        response = getattr(routing_client, method)(path, **kwargs)
        assert response.status_code == 503
        assert response.get_json()["code"] == "PRODUCTION_ENDPOINT_DISABLED"

    services = routing_client.get("/api/v1/services")
    assert services.status_code == 200
    assert services.get_json()["count"] == 4
    assert routing_client.get("/api/v1/services/not-in-catalog").status_code == 404
    assert routing_client.get("/api/health").status_code == 200
    assert routing_client.get("/api/ready").status_code == 200

    routing_app.config["MIGRATION_MODE"] = True
    migration_block = routing_client.get("/api/v1/services")
    assert migration_block.status_code == 503
    assert migration_block.get_json()["code"] == "MIGRATION_MODE"


def test_readiness_fails_closed_when_configured_redis_is_unavailable(routing_app, routing_client, monkeypatch):
    class UnavailableRedis:
        def ping(self):
            raise OSError("synthetic Redis outage")

        def close(self):
            pass

    routing_app.config["CACHE_TYPE"] = "RedisCache"
    routing_app.config["REDIS_URL"] = "rediss://synthetic.invalid:6380/0"
    monkeypatch.setattr(health_routes.Redis, "from_url", lambda *args, **kwargs: UnavailableRedis())

    response = routing_client.get("/api/ready")
    assert response.status_code == 503
    assert response.get_json() == {"status": "not_ready"}


def test_production_config_requires_tls_database_cache_and_explicit_secrets():
    ready = {
        "SECRET_KEY": "s" * 48,
        "JWT_SECRET_KEY": "j" * 48,
        "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://db-user:db-pass@db.internal/scmirn?sslmode=verify-full&sslrootcert=%2Frun%2Fpostgres-ca.crt",
        "REDIS_URL": "rediss://cache-user:cache-pass@cache.example.test:6380/0?ssl_ca_certs=%2Frun%2Fredis-ca.crt&ssl_cert_reqs=required&ssl_check_hostname=true",
        "CORS_ORIGINS": ["https://civic.gov.in"],
    }
    validate_production_config(ready)

    unsafe = {**ready, "REDIS_URL": "redis://cache.example.test:6379/0", "CORS_ORIGINS": ["http://localhost:5173"]}
    with pytest.raises(RuntimeError, match="TLS-protected Redis"):
        validate_production_config(unsafe)

    unsafe_redis_tls = {**ready, "REDIS_URL": "rediss://cache-user:cache-pass@cache.example.test:6380/0?ssl_ca_certs=%2Frun%2Fredis-ca.crt&ssl_cert_reqs=required&ssl_check_hostname=false"}
    with pytest.raises(RuntimeError, match="hostname verification"):
        validate_production_config(unsafe_redis_tls)

    unsafe_database = {**ready, "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://db-user:db-pass@db.internal/scmirn"}
    with pytest.raises(RuntimeError, match="sslmode=verify-full"):
        validate_production_config(unsafe_database)


def test_production_config_keeps_redis_urls_consistent():
    from app.config import ProductionConfig

    assert ProductionConfig.REDIS_URL == ProductionConfig.CACHE_REDIS_URL
    assert ProductionConfig.REDIS_URL == ProductionConfig.RATELIMIT_STORAGE_URI


def test_application_errors_are_safe_and_have_server_generated_request_ids(routing_app, routing_client, caplog):
    sentinel = "citizen-private-statement-abc123"
    routing_app.config["PROPAGATE_EXCEPTIONS"] = False

    @routing_app.get("/test/private-error")
    def private_error():
        raise RuntimeError(sentinel)

    response = routing_client.get("/test/private-error", headers={"X-Request-ID": "attacker-controlled"})
    body = response.get_json()
    assert response.status_code == 500
    assert body["error_code"] == "INTERNAL_ERROR"
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert body["request_id"] != "attacker-controlled"
    assert sentinel not in response.get_data(as_text=True)
    assert sentinel not in caplog.text


def test_source_routing_errors_include_stable_code_and_request_id(routing_client):
    response = routing_client.post("/api/v1/triage", json={})
    body = response.get_json()
    assert response.status_code == 400
    assert body["error_code"] == "VALIDATION_FAILED"
    assert body["request_id"] == response.headers["X-Request-ID"]
