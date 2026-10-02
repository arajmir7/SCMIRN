# ADR-0007: Source provenance and government connectors

**Status:** Accepted fail-closed handoff boundary; connector deferred  
**Date:** 2026-10-01

## CONTEXT

Routing depends on curated source metadata, effective versions and source hashes. The candidate government source is unavailable and no authorized submission API, sandbox or credentials exist.

## OPTIONS

1. Infer official authority from connector existence or a URL.
2. Use a source-verified registry and user-controlled information link; abstain without current evidence.
3. Add agency submission only after written authority and protocol details are supplied.

## DECISION

Only verified/effective sources may populate the service catalog. Route results are `NOT_SUBMITTED`. No connector can submit, report receipt, or expose official status. Future connector capabilities must be declared independently and include idempotency, acknowledgement verification and unknown-remote-state reconciliation.

## WHY

There is no authorized or verifiable service source available.

## SECURITY IMPACT

The current API is public and lacks user/tenant authorization. It remains narrow, rate-limited, consent-gated and fails closed for unsupported routes.

## OPERABILITY IMPACT

No connector health, retry, receipt or reconciliation process exists.

## MIGRATION IMPACT

External integrations require reviewed contracts, source versions, privacy/legal basis, test tenant and separately approved data retention.

## REVERSIBILITY

High while integrations are disabled. Submission history would require durable idempotency and reconciliation controls.

## STATUS

Fail-closed source and handoff boundary accepted; government connector is not implemented and remains blocked pending agency authorization.
