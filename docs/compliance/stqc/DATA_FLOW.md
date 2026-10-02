# Data flow (assessment draft)

## Canonical issue flow

1. Browser collects title, description, category, optional coordinates/contact/media.
2. Flask validates selected fields, may save media and issue data, and persists it through SQLAlchemy.
3. Issue list/map/analytics/tracker may return the stored or seeded record to browser clients.
4. No government submission or official status feed is verified.

## Canonical assistant/document flow

1. Browser sends chat text or document form values to Flask.
2. AI engine/template generates a response; chat/document metadata and content may be persisted.
3. External provider usage depends on configuration and was not verified.
4. No legal validity, agency filing, or official reference is established.

## Source candidate route flow

1. Browser sends description only after explicit consent.
2. Deterministic rules execute; raw description is normalized in memory and excluded from route decision facts.
3. HMAC fingerprint, bounded facts, result, source/rule versions, idempotency hash and 30-day expiry are persisted.
4. An official handoff is emitted only if all source and registry gates pass; current source is unavailable, so route abstains.
5. Retention worker purges expired decisions and appends count-only audit metadata.

See `docs/compliance/DPDP_READINESS_MATRIX.md` for fields, purpose, storage, processors and lifecycle gaps. Verify this flow against production logs and schemas before assessment.
