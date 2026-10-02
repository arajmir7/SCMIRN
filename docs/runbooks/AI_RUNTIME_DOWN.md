# AI runtime unavailable

## Symptoms

The source-gated production triage flow is deterministic and has no model runtime. Legacy AI endpoints are disabled by the production gate.

## Diagnosis

Confirm the request route and production release. If an AI provider has been added externally, use that provider's operator runbook and confirm its feature flag, model version and data boundary.

## Safe action

Keep AI generation disabled. The supported fallback is a clear unavailable/abstention result; do not return cached or fabricated answers as current legal guidance.

## Verification

Test that unsupported and urgent scenarios safely abstain, and that no model call occurs in the deterministic route. Any future model requires the approved golden evaluation and prompt-injection gates.

## Rollback / escalation

Escalate to the model/provider owner only if a separately approved runtime exists. Otherwise no provider action is available.

## Data-risk notes

Never copy citizen statements into an external model prompt during incident diagnosis. No production AI provider is approved by this repository.
