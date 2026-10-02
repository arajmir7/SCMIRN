# AI governance and evaluation plan

## Current inventory

- Canonical `ai_engine` implements civic chat and rights analysis; current legal outputs are not bound to a reviewed/versioned authoritative source set.
- Canonical AI/enterprise workspaces and sample chat copy include simulated or hard-coded outputs.
- SCMIRN(3) triage is deterministic phrase/rule matching, not generative AI; it stores no description but detects only a narrow possible-immediate-danger phrase set. That signal is not an assessed severity. Without a reviewed severity policy, the API returns `UNASSESSED` even when a service rule matches.
- No model card, reviewed evaluation set, Hindi/local-language benchmark, bias assessment, human escalation operations or prompt-injection evidence was present in the reviewed project.

## Safety classes

| Output | Permitted description | Gate |
|---|---|---|
| Information | General service explanations | Cite source/version/date; label uncertainty. |
| Guidance | A suggested next step | Require current source/route provenance; abstain when uncertain; never imply official advice. |
| Draft | User-editable template | Clearly marked draft, identify missing fields, review warning, no validity claim. |
| Official action | Submission, payment, filing or case status | Disabled until authorized connector, consent, confirmation, idempotency, official receipt and audit are tested. |

## Evaluation gates before any AI legal feature is described as deployed

- Versioned test set reviewed by qualified legal and language reviewers.
- Correct source citation, stale-source detection, jurisdiction, effective date and abstention scored separately.
- Prompt injection, secret exfiltration, cross-user retrieval, fabricated law/status and unsafe document tests.
- English and Hindi/local-language performance, negation, spelling, code-switching, dialect and accessibility evaluation.
- Human review, escalation route, model/provider version, data retention and incident process documented.
- Thresholds and acceptance owners approved before test; results reproducible and dated.

Until then, use deterministic source-gated routing for official handoff and describe generative features as experimental or unavailable. No model output is a lawyer, agency decision or emergency response.
