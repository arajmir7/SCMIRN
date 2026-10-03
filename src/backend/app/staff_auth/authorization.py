"""Default-deny attribute policy for the bounded staff workflows.

The current staff schema has tenant ownership and case creator/assignment data,
but it does not yet have department or jurisdiction keys. Policy decisions that
need those dimensions (such as source approval) therefore require them in the
context and deny when they are absent. This module is deliberately pure so
negative authorization behavior can be tested without a privileged database.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StaffPrincipal:
    user_id: str
    tenant_id: str
    roles: frozenset[str]
    active: bool
    mfa_verified: bool
    department_ids: frozenset[str] = frozenset()
    jurisdiction_ids: frozenset[str] = frozenset()
    service_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class PolicyAttributes:
    tenant_id: str | None
    purpose: str | None
    sensitivity: str = "INTERNAL"
    created_by_id: str | None = None
    owner_id: str | None = None
    assigned_user_id: str | None = None
    department_id: str | None = None
    jurisdiction_id: str | None = None
    source_state: str | None = None
    service_id: str | None = None
    approval_stage: str | None = None
    risk_tier: str | None = None
    case_id: str | None = None
    legal_hold: bool = False


_CASE_READ_ROLES = frozenset({"TENANT_ADMIN", "CASE_OFFICER", "AUDITOR"})
_CASE_WRITE_ROLES = frozenset({"TENANT_ADMIN", "CASE_OFFICER"})
_KNOWN_ROLES = frozenset({"TENANT_ADMIN", "CASE_OFFICER", "SOURCE_REVIEWER", "AUDITOR"})
SUPPORTED_ACTIONS = frozenset({
    "case:list", "case:read", "case:create", "case:update_status",
    "evidence:upload", "evidence:read", "evidence:delete", "source:approve",
})


def authorize(
    principal: StaffPrincipal,
    action: str,
    attributes: PolicyAttributes,
) -> bool:
    """Evaluate a named action against identity and resource attributes.

    Unknown actions, incomplete principals, missing purpose/scope and unknown
    role grants are denied. The purpose is supplied by the server route, never
    trusted from request JSON.
    """
    if (
        not principal.user_id
        or not principal.tenant_id
        or not principal.active
        or not principal.mfa_verified
        or not principal.roles
        or not principal.roles.issubset(_KNOWN_ROLES)
        or not attributes.tenant_id
        or attributes.tenant_id != principal.tenant_id
        or not attributes.purpose
    ):
        return False

    # Session-protected routes declare their policy actions at the decorator.
    # A view cannot broaden its reachable policy checks without updating that
    # route contract, which is also parity-tested against the YAML matrix.
    from flask import g, has_request_context
    if has_request_context() and hasattr(g, "staff_route_policy_actions"):
        if action not in g.staff_route_policy_actions:
            return False

    if action in {"case:list", "case:read"}:
        if attributes.purpose != "CASE_OPERATIONS" or attributes.sensitivity not in {"INTERNAL", "RESTRICTED"}:
            return False
        if not principal.roles.intersection(_CASE_READ_ROLES):
            return False
        if attributes.sensitivity == "RESTRICTED":
            return (
                "CASE_OFFICER" in principal.roles
                and principal.user_id in {
                    attributes.created_by_id,
                    attributes.owner_id,
                    attributes.assigned_user_id,
                }
            )
        if principal.roles.intersection({"TENANT_ADMIN", "AUDITOR"}):
            return True
        return principal.user_id in {
            attributes.created_by_id,
            attributes.owner_id,
            attributes.assigned_user_id,
        }

    if action in {"case:create", "case:update_status"}:
        if attributes.purpose != "CASE_OPERATIONS" or attributes.sensitivity != "INTERNAL":
            return False
        if not principal.roles.intersection(_CASE_WRITE_ROLES):
            return False
        if "TENANT_ADMIN" in principal.roles:
            return True
        return principal.user_id in {
            attributes.created_by_id,
            attributes.owner_id,
            attributes.assigned_user_id,
        }

    if action in {"evidence:upload", "evidence:read", "evidence:delete"}:
        if (
            attributes.purpose != "CASE_EVIDENCE"
            or attributes.sensitivity != "RESTRICTED"
            or not attributes.case_id
            or "CASE_OFFICER" not in principal.roles
        ):
            return False
        if action == "evidence:delete" and attributes.legal_hold:
            return False
        return principal.user_id in {
            attributes.created_by_id,
            attributes.owner_id,
            attributes.assigned_user_id,
        }

    if action == "source:approve":
        if (
            attributes.purpose != "SOURCE_GOVERNANCE"
            or not attributes.department_id
            or not attributes.jurisdiction_id
            or not attributes.service_id
            or attributes.approval_stage != "REVIEW"
            or attributes.risk_tier not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
            or attributes.source_state != "PENDING_CHECK"
            or not attributes.created_by_id
            or attributes.created_by_id == principal.user_id
            or attributes.sensitivity != "INTERNAL"
            or attributes.department_id not in principal.department_ids
            or attributes.jurisdiction_id not in principal.jurisdiction_ids
            or attributes.service_id not in principal.service_ids
        ):
            return False
        return bool(principal.roles.intersection({"SOURCE_REVIEWER", "TENANT_ADMIN"}))

    return False
