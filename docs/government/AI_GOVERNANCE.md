# AI governance boundary

The canonical policy is [`../ai/AI_GOVERNANCE_AND_EVALUATION.md`](../ai/AI_GOVERNANCE_AND_EVALUATION.md).

The production-allowlisted source-routing path is deterministic and does not call an LLM. Its phrase classifier returns `UNASSESSED` urgency; a narrow urgent phrase can produce only a possible-immediate-danger signal. Legacy assistant/legal features are not grounded in a reviewed official source corpus and are gated from the production route set. No personal model training is enabled or evidenced.

**State:** `PARTIAL` governance controls; no production model evaluation or grounded answer service is available. Unknown or unsupported official/legal claims must abstain.

