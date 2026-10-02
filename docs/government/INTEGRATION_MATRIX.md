# Government integration matrix

**Assessment date:** 2026-10-02. Public official webpages were read and hashed; no government system was logged into or API-called. `Authorized?`, `Live?`, and `Sandbox?` below refer to connected integrations and remain **No / not evidenced**. An official public link is not a connector or an agency approval.

| Platform / capability | Mode | Authorized? | Live? | Sandbox? | Handoff? | Evidence and boundary |
|---|---|---:|---:|---:|---:|---|
| API Setu | `PLANNED` | No | No | No | No verified handoff | No approved consumer/publisher registration, API contract, credentials, or sandbox evidence. |
| CPGRAMS | `OFFICIAL_HANDOFF_ONLY` | No connected integration | No | No | Yes | Public service-delivery handoff is source/hash gated; RTI, court-related/sub judice, and listed exclusions are not routed. |
| ServicePlus | `PLANNED` | No | No | No | No verified handoff | No connector, credentials, contract, or sandbox evidence. |
| UMANG | `PLANNED` | No | No | No | No verified handoff | No connector or authorized service handoff. |
| myScheme | `PLANNED` | No | No | No | No verified handoff | No live eligibility/service-data connection or source review workflow. |
| DigiLocker | `PLANNED` | No | No | No | No verified handoff | No client, scopes, credentials, or sandbox evidence. |
| MeriPehchaan / government identity broker | `PLANNED` | No | No | No | Not applicable | No identity provider integration, role mapping, MFA evidence, or authorization. |
| BHASHINI / approved translation | `PLANNED` | No | No | No | Not applicable | No verified language service, processor agreement, or reviewed translation pipeline. |
| Government eSign workflow | `PLANNED` | No | No | No | No verified handoff | Local drafts only; no signing provider or legal acceptance evidence. |
| National Consumer Helpline | `OFFICIAL_HANDOFF_ONLY` | No connected integration | No | No | Yes | NCH public consumer grievance portal; pre-litigation process, no guaranteed remedy. |
| National Cyber Crime Reporting ecosystem | `DRAFT` | No | No | No | No | Portal page did not pass TLS validation on 2026-10-02; candidate remains hidden. |
| RTI Online | `OFFICIAL_HANDOFF_ONLY` | No connected integration | No | No | Yes | Central Ministries/Departments and Central Public Authorities only; State/UT requests including NCT Delhi are outside the portal scope. |
| eCourts-related services | `PLANNED` | No | No | No | No verified handoff | No verified data/API contract; no legal advice or court filing capability. |
| NALSA / Tele-Law | `OFFICIAL_HANDOFF_ONLY` | No connected integration | No | No | Yes | Handoff to official legal-services/advice channels; no SCMIRN eligibility decision or legal advice. |
| DIGIT / UPYOG / municipal platforms | `PLANNED` | No | No | No | No verified handoff | No participating ULB, authorized environment, or case/status integration. |
| State-specific grievance/service systems | `PLANNED` | No | No | No | No verified handoff | No state owner, service catalog, contracts, or credentials. |
| Government SSO / OIDC / SAML | `PLANNED` | No | No | No | Not applicable | JWT library support is not an identity integration; no verified login/MFA/role boundary. |
| Aadhaar identity | `UNAVAILABLE` | No | No | No | Not applicable | No integration or authorization. Do not collect Aadhaar as an identity workaround. |
| Government datasets / geospatial boundaries | `UNAVAILABLE` | No | No | No | Not applicable | Current map/geocoder data is not a verified authoritative jurisdiction dataset. |
| Government status federation / official acknowledgement | `PLANNED` | No | No | No | No | No verified receipt schema, callback, status API, or agency owner. |

## Activation evidence required

Before changing a row's mode, retain current official API/source documentation, written authorization, owner and data-sharing scope, sandbox evidence, credential and callback handling design, privacy/security review, tests for idempotency and receipts, operational ownership, and a dated approval. Set `OFFICIAL_HANDOFF_ONLY` only for a currently reviewed source and validated official destination. Never label a handoff as a submission or acknowledgement.
