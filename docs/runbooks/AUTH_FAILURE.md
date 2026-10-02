# Authentication or authorization failure

## Symptoms

No production identity provider or protected officer workflow is verified. Unexpected login success, role changes, cross-tenant reads, or denial spikes are security incidents.

## Diagnosis

1. Identify the exact deployment and route; production allowlist should expose only health/readiness and source-gated public routes.
2. Review identity provider logs and application request IDs through approved access controls.
3. Preserve relevant audit/security events without exporting tokens, raw citizen statements, or identity documents.

## Safe action

Disable the affected privileged route or deployment through an authorized operator. Do not grant broad roles, disable MFA, bypass authorization, or use a test account with real data.

## Verification

Require negative tests for unauthenticated access, role escalation, object-level access and tenant escape before restoring service. These production identity gates are currently unverified.

## Rollback / escalation

Escalate to the identity/security owner. If unauthorized access is plausible, follow [`SECURITY_INCIDENT.md`](SECURITY_INCIDENT.md).

## Data-risk notes

Assume credentials or citizen data may be exposed until reviewed. Follow organizational notification and retention procedures.
