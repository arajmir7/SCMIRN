# Staff authorization policy

**Status:** local code control; not an authorization approval for production.  
**Implementation:** `src/backend/app/staff_auth/authorization.py`.

## Decision rule

All decisions default to deny. The caller must be an active staff principal with a verified MFA session, a known role grant, a non-empty tenant, an exact tenant match to the resource, and a server-defined purpose. Purpose is set by the route and is never accepted from request JSON.

| Action | Allowed current grants | Additional attributes |
| --- | --- | --- |
| `case:list` / `case:read` | `CASE_OFFICER`, `TENANT_ADMIN`, `AUDITOR` | Officers must have created, own, or be assigned the case. Admin/auditor reads stay in the exact tenant. |
| `case:create` | `CASE_OFFICER`, `TENANT_ADMIN` | Case operations purpose, internal metadata sensitivity, exact tenant; an officer creates for their own scope. |
| `case:update_status` | `CASE_OFFICER`, `TENANT_ADMIN` | Exact tenant; officer must have created, own, or be assigned the case. Auditor is read-only. |
| `source:approve` | `SOURCE_REVIEWER`, `TENANT_ADMIN` | Source must be `PENDING_CHECK`, department and jurisdiction must be present, purpose must be source governance, and maker and checker must differ. |

The current staff-case schema has no department or jurisdiction columns and stores metadata-only records without citizen linkage. The policy does not infer these attributes from a free-text field. Source approval has no public route yet; the evaluator denies it if the required scope is missing. A future normalized service/case model must provide verified scope before service-level actions are authorized.

## Current role mapping and gaps

| Target role | Current state |
| --- | --- |
| Citizen | Public routes have no account role; subject-bound identity and case linkage are not implemented. |
| Assisted-service operator | Not assignable; consent delegation and assisted-service scope are not implemented. |
| Officer | `CASE_OFFICER`, creator/assignment scoped for available staff cases. |
| Supervisor | Not assignable; supervisory separation and jurisdiction scope are not implemented. |
| Service/source reviewer | `SOURCE_REVIEWER`; approval policy requires independent checker attributes but no governance endpoint exists. |
| Tenant/government administrator | `TENANT_ADMIN`, limited to its tenant. |
| Auditor | `AUDITOR`, read-only within its tenant; audit data access remains governed separately by database roles. |

This is a partial policy closure. Do not expand the production allowlist or set `STAFF_API_ENABLED=true` based on this document. Existing PostgreSQL forced RLS remains the independent database boundary; policy evaluation does not replace it.

## Negative tests

`src/backend/tests/unit/test_staff_authorization.py` covers missing MFA/tenant/purpose, unknown actions, owner/assignment denial, cross-tenant denial, auditor write denial and maker-checker/scope failures. `src/backend/tests/unit/api/test_staff_auth.py` covers authenticated case visibility and non-enumerating 404 behavior for unauthorized reads and writes. PostgreSQL isolation evidence must use the restricted roles and remains a separate release gate.
