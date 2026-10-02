# DPDP data inventory

This is an engineering inventory, not a legal determination of applicability or compliance. The detailed field-level source of truth is [`../compliance/DPDP_READINESS_MATRIX.md`](../compliance/DPDP_READINESS_MATRIX.md); gaps and legal-review needs are preserved there.

| Data class | Examples in code paths | Intended purpose | Current control/evidence | Open work |
|---|---|---|---|---|
| `PUBLIC` | Published source/service metadata | Explain reviewed public processes | Ten source records are cataloged; nine have standard-TLS response hashes. Four public `OFFICIAL_HANDOFF_ONLY` service records pass current checks. | Authenticated review/publication, scheduled recapture/expiry, legal review and source-owner accountability. |
| `INTERNAL` | Operational IDs, request IDs, source review metadata | Operate and audit the service | Safe exception logging and metadata audit prototype | Production access, retention, SIEM and residency. |
| `PERSONAL` | Contact details, account identifiers, newsletter address if later added | Follow-up/account function where enabled | Legacy paths exist; no complete account or rights workflow verified | Purpose, minimization, lawful basis, access, correction/export/deletion. |
| `SENSITIVE_CONTEXT` | Free-text civic issue, location, chat and draft-document fields | Help citizen describe a problem | Source triage excludes raw description from persisted facts; other legacy routes are not equivalent | Per-route notice/consent, minimization, provider mapping, retention and access tests. |
| `HIGH_RISK` | Identity documents, evidence files, legal/financial documents | Potential future evidence readiness | No verified private evidence vault or malware scanning; production upload path is blocked | Do not collect until secure storage, scanning, authorization, deletion and processor review pass. |

No lawful basis, retention period, deletion right, or cross-border conclusion is inferred from this inventory. Obtain accountable privacy/legal review for the deployment.
