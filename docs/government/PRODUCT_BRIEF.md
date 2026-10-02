# SCMIRN product brief

## Position

SCMIRN is being developed as a citizen-resolution and government-service interoperability platform. It aims to help a person describe a problem, identify a responsible service from current official evidence, understand required materials, and reach the official channel. SCMIRN complements agency platforms; it does not replace them.

## Current product state

The React home page begins with “What happened?” and offers consent-gated deterministic route guidance. The Flask source-routing API records a bounded decision and emits a handoff only when service, authority, source hash/status, date, geography, and host checks pass. Four currently verified public handoffs cover NCH consumer grievances, CPGRAMS service-delivery grievances, Central-authority RTI, and NALSA/Tele-Law access. These links do not submit information or create an official acknowledgement. The cybercrime candidate remains hidden until its public endpoint passes TLS/source review.

Other legacy workspaces remain demo or draft capabilities. They do not constitute live government records, case tracking, legal advice, or connected agency services. See [integration status](INTEGRATION_MATRIX.md) and [pilot readiness](PILOT_PROPOSAL.md).

An opt-in staff-only API supports password+TOTP login, tenant roles, session revocation, and bounded metadata-only case status workflows. A new `/staff` workspace provides a browser UI for this limited API; it does not add citizen-record linkage, evidence upload, agency submission, assignment queues, or official status federation. The UI is locally exercised with mocked browser responses, and the API/RLS path has disposable PostgreSQL evidence. Neither the staff API nor its deployment identity/database configuration has been verified in production; staff routes remain disabled by default.

The `/labs` workspace collects legacy office, heatmap, tracker, analytics, document, and platform demonstrations under explicit prototype disclosures. These screens still rely on sample/demo capabilities and are not live government services. Older direct routes redirect into the disclosed Labs area.

## Users and intended value

- Citizens seeking a plain-language explanation of an official process.
- Assisted-service staff helping people navigate public services.
- Department and agency owners who may later publish reviewed service and source records.
- Government implementation partners operating an approved, isolated deployment.

## Product boundaries

- No claim of legal representation, emergency response, agency filing, or official case status.
- No LLM as final authority for jurisdiction or legal procedure.
- No government mark or endorsement claim.
- No citizen data in demos or model training by default.
- No connector activation from configuration alone.

## Pilot shape, if prerequisites are met

A future pilot should be limited to one jurisdiction, one participating department, and five to ten services, with written scope, reviewed sources, accountable owners, secure identity and data boundaries, accessibility review, and an approved operating environment. This repository does not currently meet those prerequisites and has no measured pilot outcome.
