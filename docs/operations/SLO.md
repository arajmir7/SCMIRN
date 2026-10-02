# Service level objectives — proposed, unmeasured

These are planning targets only. No historical production telemetry exists in this workspace, so there are no measured values or pass/fail results.

| Service indicator | Proposed objective | Measurement / alert | Current |
|---|---|---|---|
| Public frontend availability | 99.5% monthly after pilot | External synthetic check; alert on 5xx/error budget | Not measured |
| API availability | 99.5% monthly after pilot | `/ready` + route probes, excluding planned maintenance | Not measured |
| Triage API latency | p95 < 1.5 s, excluding client network | histogram by outcome; alert on sustained breach | Not measured |
| Error rate | < 1% server errors over rolling 30 min | request ID/correlation metrics without raw prompt | Not measured |
| Retention purge lag | expired route decisions purged within 24 h | oldest expired row age, count and job heartbeat | Job not scheduled in canonical deployment |
| Source freshness | verified sources reviewed by expiry/effective date | registry expiry gauge; disable route on stale source | No verified service source |
| Recovery point / recovery time | RPO <= 24 h / RTO <= 8 h, provisional | restore drill and signed evidence | Not tested |

Before adopting these targets, the service owner must approve them and the operator must collect a baseline. Do not publish proposed targets as measured service guarantees.
