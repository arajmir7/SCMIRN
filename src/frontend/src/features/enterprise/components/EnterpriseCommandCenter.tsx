import { Suspense, lazy, useState } from 'react';
import { apiGet, apiPost } from '@/api/http';
import { Badge, Button, JsonViewer } from '@/components/atoms';
import type { RiskRadarNode } from './RiskRadarGlobe';
import { asJsonObject } from '@/utils/json';

const RiskRadarGlobe = lazy(() => import('./RiskRadarGlobe'));

type ResultMap = Record<string, unknown>;
type ErrorMap = Record<string, string | null>;
type LoadingMap = Record<string, boolean>;

const crisisSample = {
  city_id: 'metro-demo',
  events: [
    { event_type: 'EARTHQUAKE', intensity: 0.72, duration_hours: 10 },
    { event_type: 'CYBERATTACK', intensity: 0.64, duration_hours: 8 },
  ],
  population_exposed: 850000,
};

const roiSample = {
  horizon_years: 5,
  discount_rate: 0.08,
  baseline_losses: {
    infrastructure_failures: 55000000,
    emergency_response_overrun: 21000000,
    compliance_penalties: 9000000,
  },
  investments: [
    {
      initiative: 'Predictive Maintenance Upgrade',
      capex: 22000000,
      opex_annual: 2600000,
      expected_loss_reduction_percent: 24,
      implementation_months: 6,
    },
    {
      initiative: 'Automated Incident Orchestration',
      capex: 12000000,
      opex_annual: 1500000,
      expected_loss_reduction_percent: 18,
      implementation_months: 4,
    },
  ],
};

const workflowSample = {
  issue_id: 'ISS-ENT-1002',
  title: 'Repeated transformer trips in flood-prone corridor',
  category: 'power',
  district: 'Central',
  severity: 'HIGH',
  affected_citizens: 3400,
  legal_keywords: ['liability', 'service-level agreement'],
};

const legalSample = {
  legal_domain: 'Public Infrastructure Liability',
  case_facts:
    'A city contractor repeatedly delayed transformer maintenance in a high-risk area. Service outages caused hospital disruptions and triggered citizen claims.',
  judge_name: 'Hon. Justice Sharma',
  jurisdiction: 'IN',
};

const policySample = {
  policy_name: 'Dynamic Emergency Maintenance SLA',
  target_districts: ['Central', 'North', 'East'],
  horizon_months: 24,
  variant_a: { dispatch_priority: 'critical-only', budget_shift_percent: 12 },
  variant_b: { dispatch_priority: 'critical-and-high', budget_shift_percent: 18, citizen_alerts: true },
};

export function EnterpriseCommandCenter() {
  const [cityId, setCityId] = useState<string>('metro-demo');
  const [district, setDistrict] = useState<string>('Central');
  const [connectorId, setConnectorId] = useState<string>('salesforce');
  const [briefingRecipients, setBriefingRecipients] = useState<string>('ceo@scmirn.local,ciso@scmirn.local');
  const [killNodes, setKillNodes] = useState<string>('substation-11,iot-gateway-22');

  const [crisisText, setCrisisText] = useState<string>(JSON.stringify(crisisSample, null, 2));
  const [roiText, setRoiText] = useState<string>(JSON.stringify(roiSample, null, 2));
  const [workflowText, setWorkflowText] = useState<string>(JSON.stringify(workflowSample, null, 2));
  const [legalText, setLegalText] = useState<string>(JSON.stringify(legalSample, null, 2));
  const [policyText, setPolicyText] = useState<string>(JSON.stringify(policySample, null, 2));

  const [results, setResults] = useState<ResultMap>({});
  const [errors, setErrors] = useState<ErrorMap>({});
  const [loading, setLoading] = useState<LoadingMap>({});
  const radar = asJsonObject(results.radar);
  const radarNodes: RiskRadarNode[] = Array.isArray(radar?.nodes)
    ? (radar.nodes as RiskRadarNode[])
    : [];

  const setBusy = (key: string, value: boolean) => setLoading((prev) => ({ ...prev, [key]: value }));
  const setError = (key: string, value: string | null) => setErrors((prev) => ({ ...prev, [key]: value }));
  const setResult = (key: string, value: unknown) => setResults((prev) => ({ ...prev, [key]: value }));

  async function runGet(key: string, path: string) {
    setBusy(key, true);
    setError(key, null);
    const res = await apiGet<unknown>(path);
    setBusy(key, false);
    if (!res.ok) {
      setError(key, res.error);
      setResult(key, res.details ?? null);
      return;
    }
    setResult(key, res.data);
  }

  async function runPost(key: string, path: string, payload: unknown) {
    setBusy(key, true);
    setError(key, null);
    const res = await apiPost<unknown>(path, payload);
    setBusy(key, false);
    if (!res.ok) {
      setError(key, res.error);
      setResult(key, res.details ?? null);
      return;
    }
    setResult(key, res.data);
  }

  function parseJson(text: string): unknown | null {
    try {
      return JSON.parse(text);
    } catch {
      return null;
    }
  }

  function parseEmails(text: string): string[] {
    return text
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function parseNodes(text: string): string[] {
    return text
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return (
    <div className="console">
      <div className="console-grid city-grid">
        <div className="feature-card">
          <h3>Executive War Room</h3>
          <p>Demo KPI stack using sample records; no agency feed, predictive validation, or live operations connection.</p>
          <div className="console-grid city-inline-3">
            <div className="field">
              <label>City ID</label>
              <input className="input" value={cityId} onChange={(e) => setCityId(e.target.value)} />
            </div>
            <div className="field">
              <label>District</label>
              <input className="input" value={district} onChange={(e) => setDistrict(e.target.value)} />
            </div>
            <div className="field">
              <label>Connector Focus</label>
              <select className="select" value={connectorId} onChange={(e) => setConnectorId(e.target.value)}>
                <option value="salesforce">salesforce</option>
                <option value="sap_erp">sap_erp</option>
                <option value="oracle_erp">oracle_erp</option>
                <option value="slack">slack</option>
                <option value="teams">teams</option>
              </select>
            </div>
          </div>
          <div className="inline-actions">
            <Button onClick={() => runGet('health', `/api/v1/enterprise/executive/city-health-score?city_id=${encodeURIComponent(cityId)}`)} disabled={loading.health}>
              {loading.health ? 'Loading...' : 'Load City Health'}
            </Button>
            <Button variant="ghost" onClick={() => runGet('radar', `/api/v1/enterprise/executive/risk-radar?city_id=${encodeURIComponent(cityId)}`)} disabled={loading.radar}>
              {loading.radar ? 'Loading...' : 'Load Risk Radar'}
            </Button>
            <Button
              variant="ghost"
              onClick={() =>
                runGet(
                  'sentiment',
                  `/api/v1/enterprise/executive/sentiment-pulse?city_id=${encodeURIComponent(cityId)}&district=${encodeURIComponent(district)}`
                )
              }
              disabled={loading.sentiment}
            >
              {loading.sentiment ? 'Loading...' : 'Load Sentiment'}
            </Button>
            {errors.health ? <Badge variant="danger">{errors.health}</Badge> : null}
            {errors.radar ? <Badge variant="danger">{errors.radar}</Badge> : null}
            {errors.sentiment ? <Badge variant="danger">{errors.sentiment}</Badge> : null}
          </div>
          <div className="risk-globe-block">
            {radarNodes.length > 0 ? (
              <Suspense fallback={<p className="helper-text">Loading 3D globe...</p>}>
                <RiskRadarGlobe nodes={radarNodes} />
              </Suspense>
            ) : (
              <p className="helper-text">Run "Load Risk Radar" to render the 3D globe forecast visualization.</p>
            )}
          </div>
          {results.health ? <JsonViewer value={results.health} collapsed /> : null}
          {results.radar ? <JsonViewer value={results.radar} collapsed /> : null}
          {results.sentiment ? <JsonViewer value={results.sentiment} collapsed /> : null}
        </div>

        <div className="feature-card">
          <h3>Crisis Sandbox + ROI + Executive Briefing</h3>
          <p>War game scenarios, enterprise cost-benefit, and automated daily briefing generation.</p>
          <div className="field">
            <label>Crisis simulation payload (JSON)</label>
            <textarea className="textarea resize-none" value={crisisText} onChange={(e) => setCrisisText(e.target.value)} />
          </div>
          <div className="field">
            <label>ROI calculator payload (JSON)</label>
            <textarea className="textarea resize-none" value={roiText} onChange={(e) => setRoiText(e.target.value)} />
          </div>
          <div className="field">
            <label>Briefing recipients (comma-separated)</label>
            <input className="input" value={briefingRecipients} onChange={(e) => setBriefingRecipients(e.target.value)} />
          </div>
          <div className="inline-actions">
            <Button
              onClick={() => {
                const parsed = parseJson(crisisText);
                if (!parsed) {
                  setError('crisis', 'Invalid crisis JSON payload.');
                  return;
                }
                void runPost('crisis', '/api/v1/enterprise/executive/crisis-sandbox/simulate', parsed);
              }}
              disabled={loading.crisis}
            >
              {loading.crisis ? 'Running...' : 'Run Crisis Simulation'}
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                const parsed = parseJson(roiText);
                if (!parsed) {
                  setError('roi', 'Invalid ROI JSON payload.');
                  return;
                }
                void runPost('roi', '/api/v1/enterprise/executive/roi-calculate', parsed);
              }}
              disabled={loading.roi}
            >
              {loading.roi ? 'Running...' : 'Run ROI'}
            </Button>
            <Button
              variant="ghost"
              onClick={() =>
                runPost('briefing', '/api/v1/enterprise/executive/briefings/generate', {
                  city_id: cityId,
                  recipients: parseEmails(briefingRecipients),
                  include_pdf: true,
                  include_recommendations: true,
                })
              }
              disabled={loading.briefing}
            >
              {loading.briefing ? 'Generating...' : 'Generate Briefing PDF'}
            </Button>
            {errors.crisis ? <Badge variant="danger">{errors.crisis}</Badge> : null}
            {errors.roi ? <Badge variant="danger">{errors.roi}</Badge> : null}
            {errors.briefing ? <Badge variant="danger">{errors.briefing}</Badge> : null}
          </div>
          {results.crisis ? <JsonViewer value={results.crisis} collapsed /> : null}
          {results.roi ? <JsonViewer value={results.roi} collapsed /> : null}
          {results.briefing ? <JsonViewer value={results.briefing} collapsed /> : null}
        </div>

        <div className="feature-card">
          <h3>Enterprise Integration Hub</h3>
          <p>Top connector catalog with OAuth 2.0 and SSO bootstrap.</p>
          <div className="inline-actions">
            <Button onClick={() => runGet('connectors', '/api/v1/enterprise/integrations/connectors')} disabled={loading.connectors}>
              {loading.connectors ? 'Loading...' : 'List Connectors'}
            </Button>
            <Button
              variant="ghost"
              onClick={() =>
                runPost(`auth_${connectorId}`, `/api/v1/enterprise/integrations/connectors/${encodeURIComponent(connectorId)}/authorize`, {
                  tenant_id: cityId,
                  redirect_uri: 'https://enterprise.scmirn.local/oauth/callback',
                  scopes: ['read', 'write', 'admin:alerts'],
                })
              }
              disabled={loading[`auth_${connectorId}`]}
            >
              {loading[`auth_${connectorId}`] ? 'Authorizing...' : `Authorize ${connectorId}`}
            </Button>
            {errors.connectors ? <Badge variant="danger">{errors.connectors}</Badge> : null}
            {errors[`auth_${connectorId}`] ? <Badge variant="danger">{errors[`auth_${connectorId}`]}</Badge> : null}
          </div>
          {results.connectors ? <JsonViewer value={results.connectors} collapsed /> : null}
          {results[`auth_${connectorId}`] ? <JsonViewer value={results[`auth_${connectorId}`]} collapsed /> : null}
        </div>

        <div className="feature-card">
          <h3>AI Automation + Legal Intelligence</h3>
          <p>Smart routing, escalation prediction, and legal precedent analysis.</p>
          <div className="field">
            <label>Workflow routing payload (JSON)</label>
            <textarea className="textarea resize-none" value={workflowText} onChange={(e) => setWorkflowText(e.target.value)} />
          </div>
          <div className="field">
            <label>Legal precedent payload (JSON)</label>
            <textarea className="textarea resize-none" value={legalText} onChange={(e) => setLegalText(e.target.value)} />
          </div>
          <div className="inline-actions">
            <Button onClick={() => runGet('multimodal', '/api/v1/enterprise/ai/multimodal/capabilities')} disabled={loading.multimodal}>
              {loading.multimodal ? 'Loading...' : 'Load AI Capabilities'}
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                const parsed = parseJson(workflowText);
                if (!parsed) {
                  setError('workflow', 'Invalid workflow JSON payload.');
                  return;
                }
                void runPost('workflow', '/api/v1/enterprise/automation/workflow/route-issue', parsed);
              }}
              disabled={loading.workflow}
            >
              {loading.workflow ? 'Routing...' : 'Route Issue'}
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                const parsed = parseJson(legalText);
                if (!parsed) {
                  setError('legal', 'Invalid legal JSON payload.');
                  return;
                }
                void runPost('legal', '/api/v1/enterprise/legal/precedent-analysis', parsed);
              }}
              disabled={loading.legal}
            >
              {loading.legal ? 'Analyzing...' : 'Run Precedent Analysis'}
            </Button>
            {errors.multimodal ? <Badge variant="danger">{errors.multimodal}</Badge> : null}
            {errors.workflow ? <Badge variant="danger">{errors.workflow}</Badge> : null}
            {errors.legal ? <Badge variant="danger">{errors.legal}</Badge> : null}
          </div>
          {results.multimodal ? <JsonViewer value={results.multimodal} collapsed /> : null}
          {results.workflow ? <JsonViewer value={results.workflow} collapsed /> : null}
          {results.legal ? <JsonViewer value={results.legal} collapsed /> : null}
        </div>

        <div className="feature-card">
          <h3>Trust, Security, Ops, and Scale</h3>
          <p>Blockchain trust layer, kill switch drills, policy playground, and multi-tenant operations data.</p>
          <div className="field">
            <label>Kill switch node IDs (comma-separated)</label>
            <input className="input" value={killNodes} onChange={(e) => setKillNodes(e.target.value)} />
          </div>
          <div className="field">
            <label>Policy playground payload (JSON)</label>
            <textarea className="textarea resize-none" value={policyText} onChange={(e) => setPolicyText(e.target.value)} />
          </div>
          <div className="inline-actions">
            <Button onClick={() => runGet('trust', '/api/v1/enterprise/blockchain/trust-layer/status')} disabled={loading.trust}>
              {loading.trust ? 'Loading...' : 'Load Trust Layer'}
            </Button>
            <Button
              variant="ghost"
              onClick={() =>
                runPost('kill', '/api/v1/enterprise/security/kill-switch', {
                  node_ids: parseNodes(killNodes),
                  compromise_type: 'MALWARE',
                  preserve_services: ['EMERGENCY_DISPATCH', 'PUBLIC_ALERTING', 'HOSPITAL_POWER'],
                })
              }
              disabled={loading.kill}
            >
              {loading.kill ? 'Activating...' : 'Activate Kill Switch'}
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                const parsed = parseJson(policyText);
                if (!parsed) {
                  setError('policy', 'Invalid policy JSON payload.');
                  return;
                }
                void runPost('policy', '/api/v1/enterprise/insights/policy-playground/simulate', parsed);
              }}
              disabled={loading.policy}
            >
              {loading.policy ? 'Simulating...' : 'Run Policy Playground'}
            </Button>
            <Button variant="ghost" onClick={() => runGet('ops', '/api/v1/enterprise/operations/sla')} disabled={loading.ops}>
              {loading.ops ? 'Loading...' : 'Load Ops SLA'}
            </Button>
            <Button
              variant="ghost"
              onClick={() => runGet('tenant', '/api/v1/enterprise/multi-tenant/templates')}
              disabled={loading.tenant}
            >
              {loading.tenant ? 'Loading...' : 'Load Tenant Templates'}
            </Button>
            <Button
              variant="ghost"
              onClick={() => runGet('revenue', '/api/v1/enterprise/revenue/model?citizens=2500000&cities=25')}
              disabled={loading.revenue}
            >
              {loading.revenue ? 'Loading...' : 'Load Revenue Model'}
            </Button>
            {errors.trust ? <Badge variant="danger">{errors.trust}</Badge> : null}
            {errors.kill ? <Badge variant="danger">{errors.kill}</Badge> : null}
            {errors.policy ? <Badge variant="danger">{errors.policy}</Badge> : null}
            {errors.ops ? <Badge variant="danger">{errors.ops}</Badge> : null}
            {errors.tenant ? <Badge variant="danger">{errors.tenant}</Badge> : null}
            {errors.revenue ? <Badge variant="danger">{errors.revenue}</Badge> : null}
          </div>
          {results.trust ? <JsonViewer value={results.trust} collapsed /> : null}
          {results.kill ? <JsonViewer value={results.kill} collapsed /> : null}
          {results.policy ? <JsonViewer value={results.policy} collapsed /> : null}
          {results.ops ? <JsonViewer value={results.ops} collapsed /> : null}
          {results.tenant ? <JsonViewer value={results.tenant} collapsed /> : null}
          {results.revenue ? <JsonViewer value={results.revenue} collapsed /> : null}
        </div>
      </div>
    </div>
  );
}

export default EnterpriseCommandCenter;
