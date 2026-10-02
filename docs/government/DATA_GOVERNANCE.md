# Government data governance

## Ownership and controls required

| Data domain | Proposed steward | Required controls | Current state |
|---|---|---|---|
| Official legal/service sources | Named legal/content reviewer and agency owner | Source URL, hash, captured date, effective window, reviewer, supersession, expiry alert | Candidate cyber source is unavailable; owner unassigned. |
| Citizen cases/reports | Citizen service owner | Purpose, classification, access model, retention, correction/deletion and grievance | Canonical schema stores report text/contact; governance incomplete. |
| Government status/agency records | Participating agency data owner | Agreement, schema, transfer frequency, lineage and error correction | No live feeds verified. |
| IoT/asset telemetry | Infrastructure owner | Device identity, signed ingestion, retention, safety, data quality and access | Demo/code paths exist; production source not verified. |
| Analytics/aggregates | Data protection and service owners | De-identification, minimum cell sizes, provenance, bias and publication review | Current demo stats are unverified; not publishable as facts. |
| Audit/operational logs | Security/SRE owner | Minimize PII, restrict access, retention, integrity, alerting and export | Source chain prototype exists; operations unverified. |

## Governance rules

- Catalog dataset, source owner, legal basis, sensitivity, quality, geographic/time coverage, refresh and retention.
- Keep demo fixtures synthetic and isolated; production seed command must reject demo datasets.
- Preserve lineage and review versions for legal/service content; stale/unknown sources block routing.
- Restrict raw case data from analytics; publish only reviewed, aggregated data with re-identification assessment.
- Use written agreements and an accountable agency sponsor before data exchange.
