# SCMIRN Illustrative Enterprise Target Architecture

> **Status (2026-10-01): target-state proposal, not the deployed system.** The diagram below describes a possible future architecture; WAF/API gateway, SSO broker, workflow workers, feature store, analytics warehouse, Hyperledger, SOC controls, and listed third-party connectors are not established by repository evidence. Do not use this document to claim a government deployment or enterprise production readiness.

## Current implementation boundary

- Canonical web client: React/Vite in `src/frontend`.
- Canonical API: Flask in `src/backend`; the new source-gated triage API is under `/api/v1`.
- Development persistence: SQLite. Production configuration requires PostgreSQL via Psycopg 3 and TLS Redis, but no PostgreSQL deployment or production startup has been tested.
- The route catalog is empty because the candidate official source is unavailable and has no content hash. Triage abstains and never submits a filing.
- Existing enterprise and simulation APIs are blocked by the production readiness gate. Their UI workspaces are demos, not connectors or operational controls.
- The routing/audit migration creates only the seven route-schema tables. It is not a baseline migration for every legacy model.

The engineering boundaries and evidence are tracked in [`../merge/GOVERNMENT_READINESS_MATRIX.md`](../merge/GOVERNMENT_READINESS_MATRIX.md) and [`../merge/TEST_EVIDENCE_MATRIX.md`](../merge/TEST_EVIDENCE_MATRIX.md).

## Scope
This architecture extends SCMIRN into an enterprise deployment model for large governments and Fortune 500 city operators.

## Microservices & Data Flow
```mermaid
flowchart LR
    subgraph Clients
      A1[Executive War Room UI]
      A2[Citizen Super App]
      A3[Department Ops Console]
      A4[Partner Integrations]
    end

    subgraph Edge_and_Security
      B1[Global Load Balancer]
      B2[WAF + API Gateway]
      B3[Zero Trust Policy Engine]
      B4[SSO Identity Broker SAML/OIDC]
    end

    subgraph Core_Control_Plane
      C1[Enterprise API Flask]
      C2[Workflow Orchestrator]
      C3[AI Decision Service]
      C4[Policy Playground Service]
      C5[Executive Briefing Worker]
    end

    subgraph Data_and_Intelligence
      D1[(PostgreSQL)]
      D2[(Redis Cache)]
      D3[(Object Storage)]
      D4[(Feature Store)]
      D5[(Analytics Warehouse)]
      D6[(Digital Twin Simulation)]
    end

    subgraph Trust_and_Compliance
      E1[Hyperledger Fabric]
      E2[Compliance Monitor SOC2/ISO/GDPR/CCPA]
      E3[Audit Ledger + Forensic Vault]
    end

    subgraph Integration_Hub
      F1[SAP/Oracle ERP]
      F2[Salesforce/HubSpot]
      F3[ArcGIS/AutoCAD]
      F4[Slack/Teams]
      F5[Power BI/Tableau]
      F6[Twilio/SendGrid]
      F7[AWS/Azure/GCP]
    end

    A1 --> B1 --> B2 --> B3 --> C1
    A2 --> B1
    A3 --> B1
    A4 --> B2
    B4 --> C1

    C1 --> C2
    C1 --> C3
    C1 --> C4
    C1 --> C5

    C2 --> D1
    C2 --> D2
    C3 --> D4
    C3 --> D5
    C4 --> D6
    C5 --> D3

    C1 --> E1
    C1 --> E2
    C1 --> E3

    C1 --> F1
    C1 --> F2
    C1 --> F3
    C1 --> F4
    C1 --> F5
    C1 --> F6
    C1 --> F7
```

## Security Layers
1. Identity: SSO with SAML/OIDC + adaptive MFA.
2. Access: Zero-trust policy checks on every API request.
3. Workload: Signed images, runtime posture checks, namespace isolation.
4. Data: Encryption at rest, envelope encryption, audit chains on Hyperledger.
5. Incident response: Automated kill switch to isolate compromised nodes while preserving critical services.

## Reliability Strategy
1. Multi-region active-active with traffic failover.
2. SLO target: 99.999% control-plane uptime.
3. Autoscaling for 10x emergency spikes.
4. Chaos drills for service, database, and network fault injection.

## Enterprise KPIs
1. Real-time city health score (0-100).
2. Forecast risk coverage (7/30/90 days).
3. Crisis response time and resolution SLA attainment.
4. Prevented-loss ROI and payback period.
