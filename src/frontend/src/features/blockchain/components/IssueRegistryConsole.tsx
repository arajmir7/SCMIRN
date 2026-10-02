import { useState } from 'react';
import { Button, Badge, JsonViewer } from '@/components/atoms';
import { apiPost } from '@/api/http';

const sample = {
  issue_data: {
    issue_id: 'd3b98db3-3c87-4aa1-9c63-000000000001',
    reporter_id: 'b7a8e4f1-5c1a-41b4-8ce0-000000000001',
    category: 'INFRASTRUCTURE',
    description_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    location: { lat: 28.6139, lng: 77.209, ward: 'WARD-11' },
    media_hashes: [],
    timestamp: new Date().toISOString(),
    priority: 'HIGH',
  },
  contract_address: '0x0000000000000000000000000000000000000000',
};

export function IssueRegistryConsole() {
  const [payloadText, setPayloadText] = useState<string>(JSON.stringify(sample, null, 2));
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  async function submit() {
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
    const res = await apiPost<unknown>('/api/v1/blockchain/register-issue', parsed);
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
          Simulation only. A synthetic payload is hashed in memory; no blockchain network, transaction, or persistent record is created.
        </p>

        <div className="field">
          <label>Issue registry request (JSON)</label>
          <textarea className="textarea resize-none" value={payloadText} onChange={(e) => setPayloadText(e.target.value)} />
        </div>

        <div className="inline-actions">
          <Button onClick={submit} disabled={loading}>
            {loading ? 'Recording…' : 'Register Issue Hash'}
          </Button>
          {error ? <Badge variant="danger">{error}</Badge> : null}
        </div>

        {result ? <JsonViewer value={result} /> : null}
      </div>
    </div>
  );
}

export default IssueRegistryConsole;
