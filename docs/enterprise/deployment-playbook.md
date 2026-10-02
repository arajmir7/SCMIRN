# SCMIRN Enterprise Deployment Playbook

## Targets
1. Kubernetes multi-region active-active.
2. Cloud-agnostic posture across AWS, Azure, and GCP.
3. 99.999% control-plane uptime target with progressive delivery.

## Environment Topology
1. `dev`: single region sandbox.
2. `staging`: dual-region pre-production with chaos tests.
3. `prod`: multi-region active-active with global traffic manager.

## Kubernetes Assets
1. `infrastructure/kubernetes/enterprise-api-deployment.yaml`
2. `infrastructure/kubernetes/enterprise-briefing-cronjob.yaml`
3. Existing ingress and baseline backend/frontend manifests in `infrastructure/kubernetes/`.

## Terraform Assets
1. `infrastructure/terraform/enterprise/main.tf`
2. `infrastructure/terraform/enterprise/variables.tf`
3. `infrastructure/terraform/enterprise/outputs.tf`

## CI/CD Pipeline
1. Workflow: `.github/workflows/enterprise-ci-cd.yml`
2. Stages:
- static checks and unit tests
- container build and vulnerability scan
- deploy to staging
- smoke test and synthetic checks
- controlled production rollout (canary)

## Rollout Strategy
1. Canary release starts at 1% traffic.
2. Automatic rollback on:
- error-rate threshold breach
- latency SLO breach
- security signal escalation

## Secrets and Identity
1. Use external secret manager (Vault/SM/KeyVault/Secret Manager).
2. Rotate service credentials every 30 days.
3. Use workload identity instead of static cloud keys.
4. Configure outbound executive briefing email:
- `EMAIL_PROVIDER=sendgrid` with `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`
- or `EMAIL_PROVIDER=ses` with `SES_FROM_EMAIL`, AWS identity and `AWS_REGION`

## Runbook Checklist
1. Pre-deploy:
- database migration dry-run
- feature-flag gating plan
- rollback manifest validated
2. Deploy:
- canary traffic shift
- KPI watch (error, latency, queue lag, threat alerts)
3. Post-deploy:
- compliance snapshot archived
- executive briefing health check passes
- connector heartbeat checks green
