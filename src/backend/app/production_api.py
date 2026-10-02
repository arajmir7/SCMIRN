"""Production API operations permitted before the broader readiness review."""

PRODUCTION_API_ALLOWLIST = {
    "/api/health": frozenset({"GET"}),
    "/api/ready": frozenset({"GET"}),
    "/api/v1/triage": frozenset({"POST"}),
    "/api/v1/jurisdiction/resolve": frozenset({"POST"}),
    "/api/v1/services": frozenset({"GET"}),
    "/api/v1/services/<service_id>": frozenset({"GET"}),
    "/api/v1/evidence/check": frozenset({"POST"}),
    "/api/v1/sources/<source_key>": frozenset({"GET"}),
    "/api/v1/staff/auth/login": frozenset({"POST"}),
    "/api/v1/staff/auth/mfa": frozenset({"POST"}),
    "/api/v1/staff/auth/mfa/enroll/confirm": frozenset({"POST"}),
    "/api/v1/staff/auth/me": frozenset({"GET"}),
    "/api/v1/staff/auth/password/change": frozenset({"POST"}),
    "/api/v1/staff/auth/logout": frozenset({"POST"}),
    "/api/v1/staff/cases": frozenset({"GET", "POST"}),
    "/api/v1/staff/cases/<case_id>": frozenset({"GET"}),
    "/api/v1/staff/cases/<case_id>/status": frozenset({"POST"}),
}


def is_production_api_allowed(rule: str | None, method: str) -> bool:
    """Return whether a registered route and method are in the reviewed allowlist."""
    return bool(rule and method.upper() in PRODUCTION_API_ALLOWLIST.get(rule, ()))
