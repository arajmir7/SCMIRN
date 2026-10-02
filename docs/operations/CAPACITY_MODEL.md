# Capacity model — assumptions only

**Status:** no production or load-test measurements exist. Values below define scenarios for planning; they are not tested capacity or an availability promise.

## Workload assumptions

| Scenario | Citizens/day | Peak requests/s | New route decisions/day | Evidence files/day | Generated documents/day | Worker concurrency |
|---|---:|---:|---:|---:|---:|---:|
| Small pilot planning | 500 | 5 | 100 | 0 (uploads disabled) | 0 (legacy production route disabled) | 0 background jobs |
| Expected pilot planning | 5,000 | 25 | 1,000 | 0 | 0 | 0 |
| Large event planning | 50,000 | 100 | 10,000 | 0 | 0 | 0 |

These are scenario inputs chosen for test design, not an endorsed forecast. The active public routing endpoint currently stores bounded metadata and has no verified tenant identity. Other legacy workflows remain disabled in production.

## Storage assumptions

- At 1,000 route decisions/day and 30-day retention, upper-bound active decision count is 30,000 before purge lag.
- Average row size and index amplification have not been measured; no byte estimate is asserted.
- Evidence storage growth is zero for the current production allowlist because upload is disabled. Any enabling requires a separate object-storage, malware-scanning, retention and backup model.
- Audit metadata growth and cleanup/retention policy require measurement before a production target.

## Capacity status

| Measure | Baseline capacity | Tested capacity | Safety margin |
|---|---|---|---|
| API throughput / p50,p95,p99 | Not measured | Not tested | Unknown |
| PostgreSQL connection/query capacity | Compose defaults only | Migration/health smoke, no load profile | Unknown |
| Redis throughput/availability | TLS ping only | Local dependency smoke | Unknown |
| Frontend bundle/LCP/CLS/INP | Build artifact exists; no current metric | No browser performance audit | Unknown |
| Restore capacity | No backup plan verified | Not tested | Unknown |

Before pilot sizing, run a documented synthetic workload at small/expected/stress levels, capture CPU/memory, request percentiles, DB query plans, connection pool behavior, error rate and restore throughput, and obtain an operator-approved safety margin.
