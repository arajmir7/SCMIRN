from dataclasses import replace
from pathlib import Path

import yaml

from app.staff_auth.authorization import PolicyAttributes, StaffPrincipal, authorize


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
