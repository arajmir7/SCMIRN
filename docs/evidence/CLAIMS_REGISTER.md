# Public claims register

**Rule:** a feature existing in source code or a screenshot is not evidence that a public performance, deployment, government connection or legal outcome claim is true.

The release-owner view with claim surface, accountable owner, verification method and allowed status is maintained in [`../governance/PUBLIC_CLAIMS_REGISTER.md`](../governance/PUBLIC_CLAIMS_REGISTER.md).

**Implementation update (2026-10-01):** unsupported homepage metrics and live/official claims were removed. The current copy identifies the app as a prototype, distinguishes demo data, states that no request is filed and labels document output as unreviewed. No performance metrics were substituted.

| Existing public claim | Evidence at baseline | Status | Approved wording/action |
|---|---|---|---|
| “World’s First AI-Driven Civic Intelligence System” | No comparative market evidence or independent substantiation | Unsupported | Remove “World’s First”; describe the product plainly as a civic guidance prototype/platform. |
| “500,000+ Citizens Helped” | No verified production analytics or source | Unsupported metric | Remove; publish only measured, dated and independently checked totals. |
| “78% Resolution Rate” | No defined denominator, time window, data source or audited outcomes | Unsupported metric | Remove; do not substitute a synthetic number. |
| “24/7 AI Legal Aid” | No service SLO, staffed support or verified legal-advice system | Unsupported | Use “Self-service tools may be available; not legal representation” only if backed by actual uptime. |
| “Live System Active / queries across 28 states” | No deployment telemetry or state coverage dataset | Unsupported | Replace with truthful demo/service availability status. |
| “Combines ChatGPT, Google Maps, Legal AI, Government Data” | Runtime provider/data configuration not verified; source says no active government connectors | Unsupported | Name integrations only when configured, authorized, running and tested. |
| “Instant access to laws / legal rights without lawyer fees” | Canonical AI engine lacks source/version/legal reviewer trace | Unsupported/high risk | Qualify as general information; show cited current sources and a non-lawyer notice only after grounding is implemented. |
| “Legally valid documents / court-ready” | Current templates and API tests do not demonstrate legal validity or acceptance | Unsupported/high risk | Say “draft template” and require qualified review; no validity claim. |
| “Live officer database / optimal visit strategies” | Seeded office entries; source freshness not verified | Unsupported | Mark directory entries and timestamps; remove live claim. |
| “Real-time civic accountability / official case tracking” | No government status connector; internal records only | Unsupported | State “SCMIRN record status; no official agency status feed.” |
| “Funds raised / crowdfunding” | Donation API has no verified payment provider or settlement evidence | Unsupported/high risk | Label test simulation or disable funds collection until payment, refund and compliance controls are live. |
| “Blockchain transparency / immutable records” | Canonical module is explicitly a deterministic hashing simulation; no chain/network verified | Unsupported | Label demonstration/simulation; do not claim blockchain or immutability. |
| “IoT predictive maintenance / live sensor data” | Local endpoints accept readings and calculate outputs; no verified device identity or production feed | Unsupported | Label synthetic/demo data until device and operations evidence exists. |
| “AI predicts success or resolution time” | No calibrated model/evaluation set verified | Unsupported | Remove predictive promise or label experimental simulation. |
| “Government-ready / GIGW compliant / certified / secure” | Internal matrices only; no external assessment | Prohibited | Do not publish. Use “readiness evidence prepared” only where accurate. |
| Source-gated route check | Canonical deterministic API and tests; official source candidate unavailable and service registry empty | Bounded prototype capability | State that the service abstains when no verified source exists; do not claim government service integration or legal advice. |

Use `docs/merge/CANONICAL_FEATURE_INVENTORY.md` for code path evidence and append measured proof before making claims public.
