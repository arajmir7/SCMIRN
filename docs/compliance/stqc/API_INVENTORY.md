# API inventory (code-derived draft)

Canonical active route families include:

- Health: `/api/health`.
- Civic reports/issues: `/api/issues`, `/api/report-issue`, `/api/issues/{id}`, nearby/map/stats routes; donation endpoints are not a verified payment integration.
- Assistant/legal: `/api/ai-assistant`, `/api/rights/analyze` and AI suggestions.
- Documents: generation/list/download paths.
- Office, tracker and analytics summaries.
- Advanced simulation families: `/api/v1/iot`, `/blockchain`, `/ai`, `/gamification`, `/resilience`, `/twin`, `/city-brain`, `/enterprise`, `/scmirn`.
- Upload serving route; access/storage controls need assessment.

Source candidate routes are listed in `docs/merge/API_CONTRACT_MATRIX.md`. The source archive also contains disabled 410/503 endpoints and unmounted agent/Fastify APIs; these are excluded from active route count.

Generate an exact route table from the final deployed Flask URL map and compare it to OpenAPI before external assessment. OpenAPI completeness and live API auth/error behavior are not verified.
