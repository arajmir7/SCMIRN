# Redis unavailable

## Symptoms

- `/api/ready` returns 503 because its Redis ping failed.
- Backend readiness/Compose health remains unhealthy; cache or rate-limit calls may also fail.

## Diagnosis

1. Check backend logs and Redis provider status without exposing URL credentials.
2. Verify DNS, port, network policy, Redis CA mount, `ssl_cert_reqs=required`, and `ssl_check_hostname=true`.
3. Confirm the configured Redis service identity matches the certificate hostname.

## Safe action

Keep traffic out of rotation while readiness fails. Do not replace the URL with plaintext Redis, disable certificate checks, or silently fall back to in-memory rate limiting.

## Verification

After the Redis operator restores service, verify TLS hostname validation and `/api/ready` from the backend path. Confirm shared rate limits are active before reopening traffic.

## Rollback / escalation

Escalate to the Redis operator. Roll back an application image only if a release regression caused the failure and data compatibility is reviewed.

## Data-risk notes

Redis contents are cache/rate-limit state; no case submission or official action is queued there. Do not claim durable job delivery.
