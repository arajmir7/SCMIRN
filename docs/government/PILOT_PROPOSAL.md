# Government pilot proposal (draft)

**Status:** proposal only. SCMIRN is not ready for a production-data pilot.

## Proposed bounded scope

- One consenting department and one jurisdiction.
- Five to ten explicitly reviewed service definitions.
- Synthetic-data engineering and agency-approved sandbox work before any personal data.
- Source-backed route guidance and citizen-controlled official handoff only.
- Status federation only if an authorized API, receipt contract, and agency owner are supplied.

## Entry conditions

1. Signed pilot charter, data-sharing terms, purpose, lawful basis, records ownership, and grievance contact.
2. Named agency service/source owners and legal reviewer; approved, dated source captures and publication/review process.
3. Approved identity model, staff MFA, authorization roles, tenant isolation, audit access, and revocation tests.
4. Approved deployment, data residency, secrets/KMS, monitoring, encrypted backup, tested restore and rollback.
5. Independent security testing, accessibility review, privacy review, and approved incident contacts.
6. Verified connector authorization and sandbox contract for each integration in scope.

## Measures

Instrument, without preset success claims: routing accuracy, first-time completeness, handoff success, time to responsible authority, rework, citizen abandonment, evidence deficiency, official acknowledgement rate, and opt-out/complaint rates. Publish no metric until its denominator, source, sampling method, and privacy review are documented.

## Current decision

`NOT READY — INTERNAL AND EXTERNAL GATES OPEN`. Four public official handoffs pass current source checks, but no service is connected and no filing or receipt is created. Staff MFA, authorization, tenant RLS, secure evidence storage, production operations, restore, complete security testing, and accessibility gates remain open. A synthetic-data evaluation can continue locally; a citizen-data pilot cannot start.
