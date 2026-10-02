# SCMIRN Enterprise GraphQL and Webhook Spec

## GraphQL Endpoint
- URL: `POST /api/graphql` (gateway-mapped in enterprise deployments)
- Auth: OAuth2 access token with SSO-backed identity claims.

## GraphQL Schema (Core)
```graphql
type Query {
  cityHealthScore(cityId: ID!): CityHealthScore!
  riskRadar(cityId: ID!): RiskRadar!
  sentimentPulse(cityId: ID!, district: String): SentimentPulse!
  connectors(suite: String): [Connector!]!
  operationsSLA: OperationsSLA!
  revenueModel(citizens: Int!, cities: Int!): RevenueModel!
}

type Mutation {
  simulateCrisis(input: CrisisSimulationInput!): CrisisSimulationResult!
  calculateROI(input: ROIInput!): ROIResult!
  authorizeConnector(connectorId: ID!, input: ConnectorAuthInput!): ConnectorAuthorization!
  routeIssue(input: WorkflowRouteInput!): WorkflowRouteResult!
  analyzePrecedent(input: LegalAnalysisInput!): LegalAnalysisResult!
  activateKillSwitch(input: KillSwitchInput!): KillSwitchResult!
  simulatePolicy(input: PolicyPlaygroundInput!): PolicySimulationResult!
  generateBriefing(input: ExecutiveBriefingInput!): ExecutiveBriefingResult!
}
```

## Webhook Events
SCMIRN emits signed webhooks for enterprise integrations.

### Delivery Contract
1. Method: `POST`
2. Content type: `application/json`
3. Retries: exponential backoff up to 24 hours
4. Signature header: `X-SCMIRN-Signature` (HMAC SHA-256)

### Event Types
1. `executive.briefing.generated`
2. `risk.radar.threshold_breached`
3. `crisis.simulation.completed`
4. `workflow.issue.routed`
5. `security.kill_switch.activated`
6. `compliance.report.generated`

### Example Payload
```json
{
  "event_id": "evt_01J9...",
  "event_type": "risk.radar.threshold_breached",
  "occurred_at": "2026-02-17T22:30:00Z",
  "tenant_id": "city-of-demo",
  "data": {
    "district": "Central",
    "risk_type": "CYBER",
    "forecast_30d": 82,
    "threshold": 75
  }
}
```

## Webhook Security
1. Shared secret per tenant.
2. Reject payloads older than 5 minutes.
3. Replay protection via `event_id` dedupe window.
4. IP allow-list support for strict receivers.
