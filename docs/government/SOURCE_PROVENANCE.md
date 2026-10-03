# Official source provenance and routing registry

This record tracks internal engineering provenance only. It is not legal review, agency approval, a government integration, or a claim that an agency will accept or resolve a submission.

## Capture and review method

On 2026-10-02 the catalog pages were fetched over HTTPS with standard TLS certificate validation, an exact host allowlist, same-allowlist HTTPS redirects, and a 2 MB response cap. Each `document_hash` is SHA-256 over the exact fetched response bytes. Full page bodies are not copied into this repository. Source facts and current states are recorded in [`official_source_catalog.json`](../../src/backend/app/source_routing/official_source_catalog.json).

`VERIFIED` means the internal reviewer checked official-site provenance and the bounded facts used by the listed handoff. It does not approve the legal interpretation or the service behavior. `DRAFT` sources are excluded from public service listing and routing. `SUPERSEDED` and `REVOKED` sources are excluded by the same runtime gate. A reviewed change requires a new version; the deterministic importer does not overwrite existing versions.

| Source | State | Handoff fact reviewed | SHA-256 |
|---|---|---|---|
| [MHA / I4C cybercrime page](https://www.mha.gov.in/en/divisionofmha/cyber-and-information-security-cis-division) | `VERIFIED` | MHA identifies I4C and the National Cybercrime Reporting Portal. | `3a9a4fecde1367c1b6c564561d39e4d3a4cea8303a3a144bcffe799729ee9411` |
| [National Cyber Crime Reporting Portal](https://www.cybercrime.gov.in/) | `DRAFT` | The public portal could not be fetched with valid TLS on review date; it is not an eligible route source. | No digest; TLS certificate validation failed. |
| [National Consumer Helpline about page](https://consumerhelpline.gov.in/public/index.php/about) | `VERIFIED` | NCH describes consumer grievance handling as pre-litigation and does not guarantee a remedy. | `99fe655a24d754b30e770938b01919990afc687b2152caaa82051e17f6dcd327` |
| [National Consumer Helpline contact page](https://consumerhelpline.gov.in/public/index.php/contact) | `VERIFIED` | NCH contact and portal channels. | `7b5fd492c492b0ea015dbd7176afc430a4784987273ccb4789564e57f01c39e4` |
| [CPGRAMS](https://pgportal.gov.in/?lang=en) | `VERIFIED` | Public-authority service-delivery scope, exclusions, registration tracking, and appeal facility. | `7bf66fe5a6d919a90da40e4bb403c545d51bd3b118a7a5a54065ef7e5409592d` |
| [RTI Online FAQ](https://rtionline.gov.in/faq.php) | `VERIFIED` | Central public authorities only; State authority requests, including NCT Delhi, are outside the portal's scope. | `dad93630d6468ab979a02aed85db001ffc4d0fef678efd2e6697a1d6fe374d5d` |
| [NALSA legal services FAQ](https://nalsa.gov.in/faqs/) | `VERIFIED` | Official application paths, listed eligibility categories, and helpline 15100; competent institutions decide the application. | `456b6cd17ca1facda26359cae7bd0d8e1174e0f719c0841ad698f24daa8bc4d4` |
| [Tele-Law scheme overview](https://www.tele-law.in/overview-of-tele-law.html) | `VERIFIED` | Tele-Law describes access to legal information and advice through panel lawyers using CSC facilities. | `72fba644b3dd5f3c991d68c0860cd232224f4c12eaab6b8ab8dc3c8db75d19d0` |
| [Tele-Law terms](https://www.tele-law.in/terms-conditions.html) | `VERIFIED` | Terms caution that portal content can change and official law/instruments prevail. | `552f44849b47135dfce553273e0a2f768981dec18a67aa18bc406b961d8caa5b` |

The catalog records an internal review date of 2026-10-02. These hashes and
statuses are static catalog evidence; the request path does not fetch the pages,
and there is no scheduled drift monitor or maker-checker publication workflow.
They do not establish currentness, legal approval, or agency endorsement.
| [Tele-Law privacy policy](https://www.tele-law.in/privacy-policy.html) | `VERIFIED` | The destination describes applicant data collected by its own service; SCMIRN does not collect or forward those fields. | `cfb5f5d4ca881c05345012ea8f7f7439762b9c5359090a83b8561fc57c63a3b3` |

## Active handoff candidates

The importer seeds exactly five service records. Four pass the verified-source and same-host checks and may be shown as links. All records use `OFFICIAL_HANDOFF_ONLY`, and no government connector is configured.

| Candidate | Current scope | Boundary |
|---|---|---|
| National Consumer Helpline | Consumer grievance handoff | Pre-litigation channel; outcome is not promised. |
| CPGRAMS | Public-authority service-delivery grievance | RTI, court-related/sub judice, religious, and specified employee-service matters are excluded by the official page. |
| RTI Online | RTI requests to Central Ministries, Departments, and Central Public Authorities listed by the portal | State/UT requests, including NCT Delhi, must not be sent to this portal. |
| NALSA / Tele-Law | Links to legal services and legal-advice channels | SCMIRN does not determine eligibility, provide advice, send an application, or collect applicant documents. |
| National cybercrime portal | Online financial cyber fraud candidate | Hidden until the portal's TLS and source content can be reviewed successfully. |

The public service API suppresses services unless every linked source has catalog status `VERIFIED`, a valid 64-character digest, a recorded review or verification date, is within its effective window, and all web channels share an official source host. The request path does not fetch official pages or establish live freshness. This yields four visible handoff candidates from the checked-in catalog. Route rules are deterministic phrase matches and remain subject to abstention; a match is not an official filing.

## Still required

- Recheck the cybercrime portal after its certificate is valid; review the public page and create a new immutable source version before enabling that handoff.
- Add an authenticated reviewer workflow, dual review for publication/revocation, and expiry alerts. The existing static importer is not a staff publication console.
- Have qualified counsel review legal scope, language, and required evidence before production use.
- Obtain written agency authorization and technical specifications before building any connected filing/status connector.
