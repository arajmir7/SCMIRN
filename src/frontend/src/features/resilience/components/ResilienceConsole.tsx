import { useState } from 'react';
import { Button, Badge, JsonViewer } from '@/components/atoms';
import { apiGet, apiPost } from '@/api/http';

const sampleAid = {
  aid_request: {
    requester_id: 'demo-requester',
    location: { lat: 28.6139, lng: 77.209 },
    need_category: 'MEDICAL',
    description: 'Need first-aid assistance for an elderly neighbor.',
    urgency: 'HIGH',
    time_window: 'NOW-2H',
  },
  volunteer_pool: [
    { volunteer_id: 'vol-1', location: { lat: 28.6145, lng: 77.2102 }, skills: ['first aid', 'medic'], availability: 'FLEXIBLE', verification_status: 'VERIFIED', rating: 4.7 },
    { volunteer_id: 'vol-2', location: { lat: 28.6098, lng: 77.204 }, skills: ['driver'], availability: 'FLEXIBLE', verification_status: 'UNVERIFIED', rating: 4.4 },
    { volunteer_id: 'vol-3', location: { lat: 28.621, lng: 77.224 }, skills: ['general helper'], availability: 'FLEXIBLE', verification_status: 'VERIFIED', rating: 4.2 },
  ],
};

export function ResilienceConsole() {
  const [hub, setHub] = useState<unknown>(null);
  const [aidText, setAidText] = useState<string>(JSON.stringify(sampleAid, null, 2));
  const [aidResult, setAidResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  async function loadHub() {
    setError(null);
    const res = await apiGet<unknown>('/api/v1/resilience/hub-status');
    if (!res.ok) {
      setError(res.error);
      setHub(res.details ?? null);
      return;
    }
    setHub(res.data);
  }

  async function matchAid() {
    setError(null);
    setLoading(true);
    setAidResult(null);
    let parsed: unknown;
    try {
      parsed = JSON.parse(aidText);
    } catch {
      setError('Invalid JSON payload.');
      setLoading(false);
      return;
    }
    const res = await apiPost<unknown>('/api/v1/resilience/request-aid', parsed);
    setLoading(false);
    if (!res.ok) {
      setError(res.error);
      setAidResult(res.details ?? null);
      return;
    }
    setAidResult(res.data);
  }

  return (
    <div className="console">
      <div className="console-grid">
        <p className="helper-text">Resilience hub operational decision + mutual aid matching engine.</p>
        <div className="inline-actions">
          <Button onClick={loadHub}>Load Hub Status</Button>
          <Button variant="ghost" onClick={matchAid} disabled={loading}>{loading ? 'Matching…' : 'Match Aid Request'}</Button>
          {error ? <Badge variant="danger">{error}</Badge> : null}
        </div>
        {hub ? <JsonViewer value={hub} collapsed /> : null}

        <div className="field">
          <label>Mutual aid request (JSON)</label>
          <textarea className="textarea resize-none" value={aidText} onChange={(e) => setAidText(e.target.value)} />
        </div>
        {aidResult ? <JsonViewer value={aidResult} /> : null}
      </div>
    </div>
  );
}

export default ResilienceConsole;
