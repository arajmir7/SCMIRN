# SCMIRN threat model

**Scope:** canonical public React client, Flask API, SQLite development datastore, upload/document paths, geocoder/AI-provider boundaries, and source-derived consented triage/audit components. No production network or external system was tested.

## Assets and trust boundaries

- Citizen issue descriptions, phone/contact, coordinates, uploaded images, generated documents and chat content.
- Source registry facts and route versions; route decision fingerprints; audit metadata and signing secrets.
- User/admin credentials, session tokens, service/database credentials, mail/AI/geocoding provider credentials.
- Trust boundaries: browser ↔ API; API ↔ database/filesystem; API ↔ external providers; public citizen ↔ staff/admin; one tenant ↔ another; build pipeline ↔ ZIP/dependency artifacts.

## STRIDE-style threats

| Threat | Example | Existing evidence | Required mitigation / status |
|---|---|---|---|
| Spoofing | Attacker submits reports as a citizen or impersonates staff | Staff password + TOTP, one-use challenge, lockout and hashed session path have unit tests; login/MFA also passed on disposable PostgreSQL 16 using a non-owner, non-BYPASSRLS role. Citizen identity and deployment auth remain unverified | Add deployment SSO if required, independent auth review and MFA recovery controls. `PARTIAL`. |
| Tampering | Change source/rule, issue state, payment counter, audit event | Source registry ORM version hook and hash chain; canonical data endpoints are broader | Immutable reviewed registry versions, database constraints, audit privileged writes, independent tamper tests. |
| Repudiation | Deny staff action or claim a government submission occurred | Source uses `NOT_SUBMITTED`; current canonical copy can overstate status | Record minimal actor/action metadata; never synthesize official references or status. |
| Information disclosure | Leak report/chat/phone/document or exact location | Canonical models persist user input; access control and retention are incomplete | Data minimization, private storage, tenant authorization, encryption, redacted logs, TTL and erasure. |
| Denial of service | Spam public triage, upload oversized files, expensive AI/map calls | Some rate limits and upload cap; source triage lacks route limiter | Shared rate limits, quotas, timeouts, upload limits, bot/abuse monitoring and backpressure. |
| Elevation of privilege | Exploit IDOR or tenant selection to access cases/admin tools | Staff roles, explicit tenant filters, forced staff RLS and cross-tenant read/write denials passed against disposable PostgreSQL 16 with a non-owner, non-BYPASSRLS role; other records lack tenant policy | Validate deployment role/configuration and authorization on every object/action; design and test tenant migration for legacy data. |

## Additional abuse cases

- Malicious prompt asks assistant to invent a law, government status or another citizen’s data.
- User claims an urgent emergency using ambiguous or negated wording; classifier incorrectly routes or fails to warn.
- Stale/phishing source URL is presented as official; unsafe redirect or visually similar domain captures citizen data.
- Upload contains malware/polyglot, oversized payload, active content or path traversal filename.
- Replay of route/report/donation request creates duplicate entries or false fund totals.
- Seed/demo records are exposed as real citizen or government activity.
- Operator changes route terms or deletes audit rows with database-owner access.
- Geocoding and maps leak precise home/work coordinates to an external provider.
- Dependency/package artifact includes malicious code or a ZIP `.env` secret is reused.

## Risk priority

P0 before production: staff/admin authorization, tenant isolation, secret handling, data exposure/retention, fake government claims, demo-data isolation, safe upload handling and migration/restore control. P1: verified vulnerability scans, abuse throttling, audited incident process, accessibility, source freshness and monitoring. No risk acceptance is self-approved by this document.
