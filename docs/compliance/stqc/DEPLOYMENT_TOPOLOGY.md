# Deployment topology (target draft)

```mermaid
flowchart TB
  Client[Citizen / staff clients] --> Edge[WAF + HTTPS proxy]
  Edge --> Web[React static frontend]
  Edge --> App[Flask API replicas]
  App --> DB[(Private PostgreSQL)]
  App --> ObjectStore[Private object storage + scanning]
  App --> Approved[Approved external providers]
  Migration[Short-lived migration job] --> DB
  App --> Metrics[Metrics / alerts / SIEM]
  DB --> Backup[Encrypted isolated backup]
  App -. future authorized connector .-> Agency[Government service]
```

Current canonical deployment is not established by this diagram. The local baseline uses SQLite and Vite dev/test commands; the ZIP Compose stack was not run. Supply actual cluster/container inventory, deployment YAML, network controls, storage/region, backup and recovery evidence for STQC review.
