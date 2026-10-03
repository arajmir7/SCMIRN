# Locally verifiable evidence status

No current release-completion manifests are stored here. A blocker stays
`OPEN` until the required artifact is generated from a clean, exact commit and
its evidence manifest names that commit. Do not add a synthetic passing
manifest to satisfy the checker.

| Area | Current repository evidence | Still required |
|---|---|---|
| Tenant boundary | Disposable PostgreSQL role/RLS integration and client-supplied tenant ID denial tests | Ownership migration for quarantined data; worker, signed URL, and full nested-resource adversarial coverage |
| Authorization | Default-deny policy evaluator, machine-readable matrix, matrix-driven unit cases | Assignable complete roles, explicit endpoint coverage, identity-bound department/jurisdiction/service and supervisory/delegation attributes |
| Evidence vault | Private dev store, KMS-configured S3-compatible adapter, signature/MIME/size checks, ClamAV INSTREAM, session/case-bound retrieval, hold-aware deletion | Deployed approved store/scanner, bounded runtime/health, scheduler/retries/orphans/lag alerts, restore and independent review |
| Security scans | [Dated 2026-10-03 partial candidate scan](security-release.json); [backend image CycloneDX SBOM](images/backend-51260c1.cdx.json); [frontend image CycloneDX SBOM](images/frontend-51260c1.cdx.json) | Published exact-release scan across all images, vulnerability disposition, DAST, trusted registry approval, signed provenance |
| Accessibility | Selected responsive/keyboard browser flows | Route-wide automated coverage and manual keyboard, screen reader, zoom/reflow, map/chart/document review |
| Resilience | Disposable PostgreSQL migration/RLS tests and local image build | Encrypted backup, destructive restore/DR, object checksum recovery, rollback rehearsal, measured durations |
| Service resolution | Dated reviewed official sources; four handoff-only candidates; deterministic, source-gated resolver | Source drift/review lifecycle, complete eligibility/evidence/fee/SLA/escalation/appeal graph, citizen cases, official connectors/receipts/status |
| Exact candidate gate | [Commit-bound local gate record](candidate-gate-20261003-8c9863f.json): 117 backend passes with disposable PostgreSQL 16, 15 browser passes, build/typecheck, governance and OpenAPI parity | Gate remains nonzero for 12 engineering controls and eight external dependencies; no production deployment or exact-commit security scan |

Retain raw scanner reports privately if they may contain source snippets or
secret matches. Publish only redacted reports with tool version, commit/image
digest, scope, date, exit code, finding counts, and evidence hash.

The two image SBOMs are package inventories for local ARM64 candidate images at
`51260c1`; they contain no vulnerability analysis and are not signed. The
backend image scan has open findings; the frontend scan reported none. See the
JSON report for image IDs, digests, tool versions, finding counts, and SHA-256
digests. These records do not close the security release blocker.
