# Object storage unavailable

## Symptoms

No production object-storage provider is configured. Upload and legacy download routes are disabled in production.

## Diagnosis

If a separate deployment has storage, identify its provider, bucket/container, region, encryption key, service account and health status from its approved inventory. Do not print signed URLs or credentials.

## Safe action

Keep uploads/downloads disabled. Do not switch to a public bucket or local container filesystem, and do not report successful retention/deletion without provider evidence.

## Verification

Before enabling a future store, verify private ACLs, malware scanning, content validation, access control, lifecycle/deletion, backup and audit behavior with synthetic files.

## Rollback / escalation

Escalate to the storage/security owner. Disable the upload feature server-side until access and object integrity are restored.

## Data-risk notes

Evidence files may contain high-risk personal data. Preserve chain-of-custody requirements and do not copy objects into unapproved recovery storage.
