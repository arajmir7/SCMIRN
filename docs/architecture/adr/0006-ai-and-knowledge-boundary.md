# ADR-0006: AI and knowledge boundary

**Status:** Accepted fail-closed rule; production AI runtime deferred  
**Date:** 2026-10-01

## CONTEXT

The prototype contains legacy AI and legal-analysis code, but it lacks a verified production model, prompt/RAG controls, evaluated golden corpus, source citation verification and legal review.

## OPTIONS

1. Use an LLM as authority for legal rights, jurisdiction or filing.
2. Keep routing deterministic and disable legacy generation APIs in production.
3. Select an AI provider and grounding architecture before defining evaluation and privacy controls.

## DECISION

Production routing remains deterministic; no LLM decides jurisdiction, official status, access control or submission. Legacy AI endpoints remain gated. No production AI provider or retrieval system is selected.

## WHY

No current source/evaluation evidence supports a safe model-backed legal workflow.

## SECURITY IMPACT

Prompt injection, cross-user retrieval, citation fabrication, PII exposure and unsupported legal claims remain relevant before any model is enabled.

## OPERABILITY IMPACT

There is no AI runtime dependency or model-health service to operate in the production allowlist.

## MIGRATION IMPACT

Any future model requires a versioned evaluation corpus, schema validation, abstention thresholds, data handling review and kill switch.

## REVERSIBILITY

High while no production model is selected or active.

## STATUS

Deterministic routing accepted; production generative AI/search/RAG decisions deferred.
