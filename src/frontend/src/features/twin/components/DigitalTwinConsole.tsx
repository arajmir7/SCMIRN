import { useState } from 'react';
import { Button, Badge, JsonViewer } from '@/components/atoms';
import { apiPost } from '@/api/http';

const sample = {
  simulation_request: {
    twin_id: 'demo-twin-ward-11',
    scenario_type: 'EXTREME_WEATHER',
    parameters: {
      event_magnitude: 'HIGH',
      duration_hours: 36,
      affected_area_percent: 30,
      iterations: 2000,
    },
    kpis: ['SERVICE_CONTINUITY', 'COST_IMPACT', 'POPULATION_AFFECTED', 'RECOVERY_TIME'],
  },
};

export function DigitalTwinConsole() {
  const [payloadText, setPayloadText] = useState<string>(JSON.stringify(sample, null, 2));
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  async function simulate() {
    setError(null);
    setLoading(true);
    setResult(null);
    let parsed: unknown;
    try {
      parsed = JSON.parse(payloadText);
    } catch {
      setError('Invalid JSON payload.');
      setLoading(false);
      return;
    }
    const res = await apiPost<unknown>('/api/v1/twin/simulate', parsed);
    setLoading(false);
    if (!res.ok) {
      setError(res.error);
      setResult(res.details ?? null);
      return;
    }
    setResult(res.data);
  }

  return (
    <div className="console">
      <div className="console-grid">
        <p className="helper-text">
          Run a scenario simulation (Monte Carlo baseline) against a digital twin and get KPIs with confidence intervals.
        </p>
        <div className="field">
          <label>Simulation request (JSON)</label>
          <textarea className="textarea resize-none" value={payloadText} onChange={(e) => setPayloadText(e.target.value)} />
        </div>
        <div className="inline-actions">
          <Button onClick={simulate} disabled={loading}>
            {loading ? 'Simulating…' : 'Run Simulation'}
          </Button>
          {error ? <Badge variant="danger">{error}</Badge> : null}
        </div>
        {result ? <JsonViewer value={result} /> : null}
      </div>
    </div>
  );
}

export default DigitalTwinConsole;
