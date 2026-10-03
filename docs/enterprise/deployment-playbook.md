# Enterprise Deployment Assets and Readiness

## Current status

These files are deployment templates for review. SCMIRN has no approved cloud account, pilot authority, production image digests, deployment credentials, or completed restore and operations exercises. Do not treat this folder as a production deployment plan or as evidence that the target state is running.

The prior claims of multi-region active-active deployment, cloud-agnostic operation, 99.999% control-plane availability, canary rollout, and an existing enterprise CI/CD workflow were not supported by repository or environment evidence and have been removed.

## Reviewed templates

- `infrastructure/kubernetes/namespace.yaml` enables the Kubernetes restricted Pod Security profile for `scmirn-prod`.
- `infrastructure/kubernetes/backend-deployment.yaml`, `enterprise-api-deployment.yaml`, and `frontend-deployment.yaml` use non-root identities, read-only container filesystems, resource bounds, health probes where implemented, and temporary writable volumes.
- All image references ending in `release-placeholder` are deliberately unusable placeholders. Before deployment, replace each with the approved registry image pinned by digest and verify provenance and scan results for that exact image.
- `infrastructure/kubernetes/enterprise-briefing-cronjob.yaml` is intentionally suspended. Its previous hard-coded demonstration location and recipient list have been removed. Keep it suspended until an accountable service owner approves the real data sources, recipients, operating identity, and workflow.
- `infrastructure/terraform/enterprise/main.tf` describes a private EKS API endpoint, encrypted Kubernetes secrets, immutable ECR tags with push scanning, S3 public-access blocks, KMS encryption for briefing artifacts, TLS-only access, and an S3 access-log destination.
- S3 access logs use SSE-S3 on the destination bucket because AWS S3 server-access logging does not support SSE-KMS destinations reliably; briefing artifacts use the customer-managed KMS key.

## Required before any deployment

1. Obtain the approved pilot authority, geography, service catalogue, hosting operator, and data-owner decisions in `docs/release/production-blockers.yaml`.
2. Supply and review the real VPC, private subnet, IAM role, DNS, ingress/TLS, identity, secret-store, backup, retention, and monitoring configuration.
3. Build the candidate containers from the reviewed source, publish them to the approved immutable registry, pin them by digest, and attach signed provenance, SBOM, and scan results for those exact digests.
4. Validate the Terraform plan against an authorized account and review the IAM permissions needed for EKS KMS encryption, ECR KMS encryption, and log delivery. No Terraform apply has been performed.
5. Render and policy-check the Kubernetes manifests with the approved digests and environment values; then conduct runtime, readiness, authorization, tenant-isolation, restore, rollback, and incident exercises in an authorized non-production environment.
6. Record deployment approval and independently reviewed evidence. Local configuration scans and repository tests do not close these requirements.

## Local checks

Run `bash scripts/release_gate.sh --mode candidate` for the repository candidate gate. The gate is expected to fail while engineering blockers remain open and reports `NOT PRODUCTION READY`; passing local checks does not authorize a deployment.
