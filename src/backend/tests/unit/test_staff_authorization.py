from dataclasses import replace

from app.staff_auth.authorization import PolicyAttributes, StaffPrincipal, authorize


def _principal(**overrides):
    values = {
        "user_id": "staff-a",
        "tenant_id": "tenant-a",
        "roles": frozenset({"CASE_OFFICER"}),
        "active": True,
        "mfa_verified": True,
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
    principal = _principal(roles=frozenset({"SOURCE_REVIEWER"}))
    ready = _attributes(
        purpose="SOURCE_GOVERNANCE", department_id="department-a",
        jurisdiction_id="district-a", source_state="PENDING_CHECK",
        created_by_id="staff-b",
    )
    assert authorize(principal, "source:approve", ready)
    assert not authorize(principal, "source:approve", replace(ready, created_by_id="staff-a"))
    assert not authorize(principal, "source:approve", replace(ready, jurisdiction_id=None))
    assert not authorize(principal, "source:approve", replace(ready, source_state="DRAFT"))
