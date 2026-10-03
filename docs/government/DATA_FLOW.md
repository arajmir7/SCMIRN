# Government data flow and trust boundaries

**Scope:** code and configuration inventory; production traffic and processor locations were not inspected.

The machine-readable [data-governance registry](data-governance-registry.yaml)
tracks the 35 mapped SQLAlchemy tables and all 471 fields. The CI checker
compares that inventory to live ORM metadata and requires each field to be
recorded as potentially personal/linkable or explicitly classified otherwise.
It contains 294 potentially personal/linkable candidate entries: 273 still
require accountable approval and 21 have explicit candidate exemptions. The
release approval mode blocks on the pending field, table, and profile decisions.

## Consent-gated source triage (development/test only)

1. The browser collects a free-text description and submits only after the explicit triage consent control.
2. Flask validates input length and optional state/district fields. Deterministic phrase classification and route rules run in process; no LLM is called by this route.
3. The description is normalized in memory. The persisted decision contains a keyed input fingerprint, bounded classifier/geography-presence facts, result, rule/service/source versions, idempotency digest, and retention deadline. Unit tests assert the raw description is absent from stored decision facts and output.
4. A route requires effective active records, verified source metadata including a SHA-256 content hash, service/source consistency, matching local geography, and safe same-host HTTPS channels. The current catalog has four internally reviewed handoff-only service candidates; the fifth candidate remains withheld because its official portal could not be reviewed with valid TLS. These source snapshots date from 2026-10-02 and have no scheduled drift review.
5. An emitted result states `NOT_SUBMITTED`; it does not create an official reference. A handoff opens the official host for the citizen to continue themselves. No SCMIRN connector submits a filing or receives official status.
6. The purge function deletes expired route decisions and appends count-only audit metadata. Production scheduling and deletion-lag alerting are not configured.

The resolver endpoint is registered for local development and tests but is
intentionally excluded from the production API allowlist. `route_decisions`
does not yet have a complete subject/tenant boundary and is quarantined from
the production runtime database role. Production currently exposes service
discovery and source metadata, not personalized triage or jurisdiction
resolution. See the [route matrix](../merge/ROUTE_MATRIX.md).

## Legacy and demo flows

Legacy issue, assistant, document, upload, analytics, map, and tracking paths may collect or return personal or sensitive-context data, depending on the route and configuration. Several are disabled by the production API gate; their complete retention, authorization, external-provider, and deletion behavior is not verified. Do not load real citizen information into demo paths. The detailed field inventory is in [`../compliance/DPDP_READINESS_MATRIX.md`](../compliance/DPDP_READINESS_MATRIX.md).

## Private case evidence

Evidence intake is implemented behind the staff MFA and case authorization
middleware, but `EVIDENCE_VAULT_ENABLED` defaults to false and the evidence
routes remain outside the production API allowlist. Uploads are size-capped,
restricted to PDF/PNG/JPEG signatures, hashed, staged privately, scanned with
ClamAV INSTREAM, and promoted only after a clean result. Only metadata enters
the tenant-RLS table; the object key and client filename are not returned in
the response or audit event. Retrieval URLs are signed, short-lived, bound to
the current staff session and case, and return through the API for reauthorization
and access audit on every download. Expired deletion respects legal hold and
records failure unless the store confirms removal.

Local development uses a private filesystem store. Production requires a
private S3-compatible bucket with KMS encryption, a configured scanner socket,
and an authority-owned retention policy, none of which is configured or
verified for this candidate. No scheduled retention worker, orphan cleanup,
deletion-lag alert, or restore drill has been verified.

## External systems

No government connector, official status feed, identity broker, document vault, notification provider, or AI processor is verified as connected for this assessment. Browser geocoding/map providers are separately described in the privacy matrix; provider terms, location, and retention remain to be confirmed for deployment.
