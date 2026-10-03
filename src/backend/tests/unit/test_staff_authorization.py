from dataclasses import replace
from pathlib import Path

import yaml

from app.staff_auth.authorization import PolicyAttributes, StaffPrincipal, SUPPORTED_ACTIONS, authorize
from app.staff_auth.security import ROLES


def _principal(**overrides):
    values = {
        "user_id": "staff-a",
        "tenant_id": "tenant-a",
        "roles": frozenset({"CASE_OFFICER"}),
        "active": True,
        "mfa_verified": True,
        "department_ids": frozenset(),
        "jurisdiction_ids": frozenset(),
        "service_ids": frozenset(),
    }
    values.update(overrides)
    return StaffPrincipal(**values)


def _attributes(**overrides):
    values = {
        "tenant_id": "tenant-a",
        "purpose": "CASE_OPERATIONS",
        "sensitivity": "INTERNAL",
        "created_by_id": "staff-a",
        "owner_id": "staff-a",
        "assigned_user_id": None,
    }
    values.update(overrides)
    return PolicyAttributes(**values)


def test_policy_denies_missing_mfa_tenant_or_server_defined_purpose():
    assert not authorize(_principal(mfa_verified=False), "case:read", _attributes())
    assert not authorize(_principal(tenant_id=""), "case:read", _attributes())
    assert not authorize(_principal(), "case:read", _attributes(purpose=""))
    assert not authorize(_principal(), "unregistered:action", _attributes())


def test_case_officer_can_read_only_owned_or_assigned_cases():
    principal = _principal()
    assert authorize(principal, "case:read", _attributes())
    assert authorize(
        principal, "case:read", _attributes(created_by_id="staff-b", owner_id="staff-b", assigned_user_id="staff-a")
    )
    assert not authorize(
        principal, "case:read", _attributes(created_by_id="staff-b", owner_id="staff-b", assigned_user_id="staff-b")
    )


def test_tenant_admin_can_read_tenant_cases_but_never_cross_tenant():
    principal = _principal(roles=frozenset({"TENANT_ADMIN"}))
    unassigned = _attributes(created_by_id="staff-b", owner_id="staff-b")
    assert authorize(principal, "case:read", unassigned)
    assert not authorize(principal, "case:read", _attributes(tenant_id="tenant-b"))
    assert not authorize(
        principal, "case:read", replace(unassigned, sensitivity="RESTRICTED")
    )


def test_auditor_is_read_only():
    principal = _principal(roles=frozenset({"AUDITOR"}))
    assert authorize(principal, "case:read", _attributes(created_by_id="staff-b", owner_id="staff-b"))
    assert not authorize(principal, "case:update_status", _attributes())
    assert not authorize(principal, "case:create", _attributes())


def test_source_approval_requires_separate_reviewer_and_complete_scope():
    principal = _principal(
        roles=frozenset({"SOURCE_REVIEWER"}),
        department_ids=frozenset({"department-a"}),
        jurisdiction_ids=frozenset({"district-a"}),
        service_ids=frozenset({"service-a"}),
    )
    ready = _attributes(
        purpose="SOURCE_GOVERNANCE", department_id="department-a",
        jurisdiction_id="district-a", service_id="service-a",
        approval_stage="REVIEW", risk_tier="HIGH", source_state="PENDING_CHECK",
        created_by_id="staff-b",
    )
    assert not authorize(_principal(roles=frozenset({"SOURCE_REVIEWER"})), "source:approve", ready)
    assert authorize(principal, "source:approve", ready)
    assert not authorize(principal, "source:approve", replace(ready, created_by_id="staff-a"))
    assert not authorize(principal, "source:approve", replace(ready, jurisdiction_id=None))
    assert not authorize(principal, "source:approve", replace(ready, jurisdiction_id="district-b"))
    assert not authorize(principal, "source:approve", replace(ready, service_id="service-b"))
    assert not authorize(principal, "source:approve", replace(ready, approval_stage="DRAFT"))
    assert not authorize(principal, "source:approve", replace(ready, source_state="DRAFT"))


def test_machine_readable_authorization_matrix_generates_policy_expectations():
    repository = Path(__file__).resolve().parents[4]
    matrix = yaml.safe_load((repository / "docs/security/authorization-matrix.yaml").read_text(encoding="utf-8"))
    implemented_roles = {
        role["staff_role"]
        for role in matrix["roles"]
        if role["staff_role"] is not None
    }
    assert implemented_roles == {"TENANT_ADMIN", "CASE_OFFICER", "SOURCE_REVIEWER", "AUDITOR"}
    for case in matrix["policy_cases"]:
        principal_data = dict(case["principal"])
        for scope_name in ("department_ids", "jurisdiction_ids", "service_ids"):
            if scope_name in principal_data:
                principal_data[scope_name] = frozenset(principal_data[scope_name])
        principal_data["roles"] = frozenset(principal_data["roles"])
        attributes = PolicyAttributes(**case["attributes"])
        expected = case["expected"] == "ALLOW"
        assert authorize(StaffPrincipal(**principal_data), case["action"], attributes) is expected, case["id"]


def test_staff_route_registry_matches_machine_readable_authorization_contract():
    from flask import Flask
    from app.staff_auth.api import bp as staff_auth_bp
    from app.evidence_vault.api import bp as staff_evidence_bp

    repository = Path(__file__).resolve().parents[4]
    matrix = yaml.safe_load((repository / "docs/security/authorization-matrix.yaml").read_text(encoding="utf-8"))
    assert matrix["route_contract_version"] == 1
    assert matrix["scope"] == "Current staff and evidence endpoints only; not a complete government RBAC approval."

    app = Flask("staff_route_contract")
    app.register_blueprint(staff_auth_bp, url_prefix="/api/v1/staff")
    app.register_blueprint(staff_evidence_bp, url_prefix="/api/v1/staff")

    actual = {}
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith("/api/v1/staff/"):
            continue
        view = app.view_functions[rule.endpoint]
        for method in set(rule.methods or ()) - {"HEAD", "OPTIONS"}:
            key = (rule.rule, method)
            assert key not in actual, f"duplicate runtime route method: {key}"
            actual[key] = view

    expected = {}
    authentication_modes = {
        "PUBLIC_CREDENTIALS",
        "SIGNED_MFA_CHALLENGE",
        "ONE_TIME_ENROLLMENT_TOKEN",
        "MFA_SESSION",
    }
    for route in matrix["routes"]:
        assert route["path"].startswith("/api/v1/staff/")
        assert route["authentication"] in authentication_modes
        assert isinstance(route["required_roles"], list)
        assert set(route["required_roles"]).issubset(ROLES)
        assert isinstance(route["policy_actions"], list)
        assert set(route["policy_actions"]).issubset(SUPPORTED_ACTIONS)
        for method in route["methods"]:
            key = (route["path"], method)
            assert key not in expected, f"duplicate matrix route method: {key}"
            session_protected = route["authentication"] == "MFA_SESSION"
            assert route["csrf_required"] is (session_protected and method not in {"GET", "HEAD", "OPTIONS"})
            expected[key] = route

    assert set(actual) == set(expected), {
        "missing_from_matrix": sorted(set(actual) - set(expected)),
        "stale_matrix_entries": sorted(set(expected) - set(actual)),
    }
    for key, view in actual.items():
        route = expected[key]
        runtime_policy = getattr(view, "__scmirn_staff_route_policy__", None)
        if route["authentication"] == "MFA_SESSION":
            assert runtime_policy is not None, f"{key} lost staff session enforcement"
            assert runtime_policy["authentication"] == route["authentication"]
            assert list(runtime_policy["required_roles"]) == sorted(route["required_roles"])
            assert list(runtime_policy["policy_actions"]) == sorted(route["policy_actions"])
        else:
            assert runtime_policy is None, f"{key} has undocumented staff session enforcement"


def test_restricted_evidence_requires_assigned_case_officer_and_case_scope():
    principal = _principal()
    evidence = _attributes(
        purpose="CASE_EVIDENCE", sensitivity="RESTRICTED", case_id="case-a",
    )
    assert authorize(principal, "evidence:read", evidence)
    assert authorize(principal, "evidence:upload", evidence)
    assert not authorize(
        _principal(roles=frozenset({"TENANT_ADMIN"})), "evidence:read",
        replace(evidence, created_by_id="staff-b", owner_id="staff-b"),
    )
    assert not authorize(
        _principal(roles=frozenset({"AUDITOR"})), "evidence:read",
        replace(evidence, created_by_id="staff-b", owner_id="staff-b"),
    )
    assert not authorize(
        _principal(), "evidence:read",
        replace(evidence, created_by_id="staff-b", owner_id="staff-b", assigned_user_id="staff-b"),
    )
    assert not authorize(principal, "evidence:read", replace(evidence, case_id=None))
    assert not authorize(principal, "evidence:read", replace(evidence, tenant_id="tenant-b"))


def test_legal_hold_blocks_evidence_deletion_even_for_assigned_officer():
    attributes = _attributes(
        purpose="CASE_EVIDENCE", sensitivity="RESTRICTED", case_id="case-a",
        legal_hold=True,
    )
    assert not authorize(_principal(), "evidence:delete", attributes)
    assert authorize(_principal(), "evidence:delete", replace(attributes, legal_hold=False))


def test_request_policy_cannot_evaluate_actions_outside_the_route_declaration():
    from flask import Flask, g

    app = Flask("staff_policy_action_guard")
    with app.test_request_context("/api/v1/staff/cases/example"):
        g.staff_route_policy_actions = frozenset({"case:read"})
        assert authorize(_principal(), "case:read", _attributes())
        assert not authorize(_principal(), "case:update_status", _attributes())
