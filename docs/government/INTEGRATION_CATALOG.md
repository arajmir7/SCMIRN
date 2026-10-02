# Government integration catalog

No live or sandbox government integration is verified in this workspace. Four public official links are supported as `OFFICIAL_HANDOFF_ONLY`; they do not create a filing, send citizen data, or return a government reference. Detailed status is maintained in [`INTEGRATION_MATRIX.md`](INTEGRATION_MATRIX.md). Adapter contracts may be developed behind disabled flags, but production must fail closed without written authorization, credentials, a current official contract, sandbox validation and operator ownership.

| Integration | Present evidence | Production state | Entry conditions |
|---|---|---|---|
| Cybercrime financial-fraud official handoff | MHA identifies the portal, but direct portal TLS validation failed on 2026-10-02; candidate content hash is absent. | Source `DRAFT`; service handoff hidden | Recheck only after normal TLS verification succeeds; inspect current page and create a new immutable source version. |
| National Consumer Helpline public handoff | Official NCH about/contact pages hashed; pre-litigation scope is disclosed. | `OFFICIAL_HANDOFF_ONLY` | No application submission; outcome is not guaranteed. |
| CPGRAMS public handoff | Official CPGRAMS page hashed; scope and exclusions recorded. | `OFFICIAL_HANDOFF_ONLY` | No application submission or case-status federation. |
| RTI Online Central-authority handoff | Official DoPT FAQ hashed; Central-only scope recorded. | `OFFICIAL_HANDOFF_ONLY` | State/UT public authorities including NCT Delhi are excluded from this portal. |
| NALSA / Tele-Law public handoff | Official NALSA FAQ and Tele-Law overview/terms/privacy pages hashed. | `OFFICIAL_HANDOFF_ONLY` | No eligibility decision, legal advice, application submission, or evidence collection by SCMIRN. |
| DigiLocker | No client, scopes or credentials verified | `PLANNED` | Agency onboarding, approved scopes, sandbox, privacy and retention review. |
| Government SSO / OIDC / SAML | Local password+TOTP staff auth and tenant role guards exist; no IdP contract or federation adapter | `PLANNED` | Identity-provider contract, role mapping, revocation, recovery, independent review and PostgreSQL authorization tests. |
| Aadhaar identity | No integration or authorization | `UNAVAILABLE` | Do not collect Aadhaar as a workaround. Any future proposal needs explicit lawful basis and official authorization. |
| Department grievance/case APIs | No live connector; source legacy case APIs return unavailable | `PLANNED` | API contract, data-sharing agreement, test tenant, idempotency and official receipt verification. |
| Government datasets / geospatial | Current map/geocoder uses mixed local/demo/external data | `UNAVAILABLE` | Dataset license, authoritative provenance, refresh SLA, privacy and source owner. |
| Translation | No reviewed service integration | `PLANNED` | Official content owners, bilingual QA, versioning and approved processor. |
| Email/SMS/notification | Provider configuration is not evidence of verified delivery | `PLANNED` | Provider agreement, opt-in, sender authorization, retry/abuse policy, audit and unsubscribe. |
| Document/eSign | Local draft generation only; no external signing | `PLANNED` | Approved document templates, eSign contract and legal acceptance testing. |
| Payments | Donation counter exists without verified gateway settlement | `UNAVAILABLE` | Authorized payment provider, reconciliation/refunds, security and legal review. |

The supported catalog modes are `CONNECTED`, `SANDBOX_CONNECTED`, `CONNECTOR_IMPLEMENTED_NOT_AUTHORISED`, `OFFICIAL_HANDOFF_ONLY`, `PLANNED`, and `UNAVAILABLE`. A configured URL or credential is not evidence of connectivity or authorization. Never infer `CONNECTED` from configuration alone.
