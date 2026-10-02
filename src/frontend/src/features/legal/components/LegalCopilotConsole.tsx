import { useMemo, useState } from 'react';
import { Button, Badge, JsonViewer } from '@/components/atoms';
import { apiPost } from '@/api/http';
import { getJsonValue } from '@/utils/json';

export function LegalCopilotConsole() {
  const [query, setQuery] = useState<string>('My landlord is trying to evict me tomorrow and refuses to return my deposit.');
  const [city, setCity] = useState<string>('New Delhi');
  const [state, setState] = useState<string>('Delhi');
  const [monthlyRent, setMonthlyRent] = useState<number>(12000);
  const [depositAmount, setDepositAmount] = useState<number>(24000);
  const [noticeGiven, setNoticeGiven] = useState<number>(2);
  const [writtenAgreement, setWrittenAgreement] = useState<boolean>(true);

  const [classification, setClassification] = useState<unknown>(null);
  const [rights, setRights] = useState<unknown>(null);
  const [document, setDocument] = useState<unknown>(null);
  const [quality, setQuality] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const classifiedIntent = useMemo(() => {
    const dom = getJsonValue(classification, 'classification', 'primary_domain') ?? 'HOUSING';
    const sub = getJsonValue(classification, 'classification', 'sub_domain') ?? 'Eviction';
    const urg = getJsonValue(classification, 'classification', 'urgency') ?? 'URGENT';
    return { domain: dom, sub_domain: sub, urgency: urg, location: { city, state } };
  }, [classification, city, state]);

  async function runClassify() {
    setError(null);
    setLoading(true);
    setClassification(null);
    const res = await apiPost<unknown>('/api/v1/ai/classify-intent', { user_query: query, conversation_context: [] });
    setLoading(false);
    if (!res.ok) {
      setError(res.error);
      setClassification(res.details ?? null);
      return;
    }
    setClassification(res.data);
  }

  async function runRights() {
    setError(null);
    setLoading(true);
    setRights(null);
    const res = await apiPost<unknown>('/api/v1/ai/rights-calculate', {
      classified_intent: classifiedIntent,
      user_facts: {
        tenant_since: null,
        monthly_rent: monthlyRent,
        deposit_amount: depositAmount,
        notice_period_given: noticeGiven,
        written_agreement: writtenAgreement,
        issue_description: query,
      },
    });
    setLoading(false);
    if (!res.ok) {
      setError(res.error);
      setRights(res.details ?? null);
      return;
    }
    setRights(res.data);
  }

  async function runDocument() {
    setError(null);
    setLoading(true);
    setDocument(null);
    const res = await apiPost<unknown>('/api/v1/ai/document-generate', {
      document_request: {
        template_type: 'LEGAL_NOTICE',
        jurisdiction: { city, state, court: null },
        user_profile: { name: 'Citizen', address: 'Ward 11, ' + city, contact: '+91-XXXXXXXXXX' },
        extracted_facts: {
          issue_summary: query,
          monthly_rent: monthlyRent,
          deposit_amount: depositAmount,
          notice_days_given: noticeGiven,
        },
        rights_analysis: rights ?? {},
      },
    });
    setLoading(false);
    if (!res.ok) {
      setError(res.error);
      setDocument(res.details ?? null);
      return;
    }
    setDocument(res.data);
  }

  async function runQuality() {
    setError(null);
    setLoading(true);
    setQuality(null);
    const content = document ? JSON.stringify(document, null, 2) : (rights ? JSON.stringify(rights, null, 2) : query);
    const res = await apiPost<unknown>('/api/v1/ai/quality-check', {
      content_to_evaluate: {
        type: document ? 'DOCUMENT' : (rights ? 'RIGHTS_ANALYSIS' : 'CHAT_RESPONSE'),
        content,
        context: { user_type: 'citizen', urgency: classifiedIntent.urgency },
      },
    });
    setLoading(false);
    if (!res.ok) {
      setError(res.error);
      setQuality(res.details ?? null);
      return;
    }
    setQuality(res.data);
  }

  return (
    <div className="console">
      <div className="console-grid">
        <p className="helper-text">
          This runs the full Legal Co‑Pilot stack: intent routing → rights calculation → document generation → quality scoring.
        </p>

        <div className="field">
          <label>User query</label>
          <textarea className="textarea resize-none" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>

        <div className="console-grid" style={{ gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12 }}>
          <div className="field">
            <label>City</label>
            <input className="input" value={city} onChange={(e) => setCity(e.target.value)} />
          </div>
          <div className="field">
            <label>State</label>
            <input className="input" value={state} onChange={(e) => setState(e.target.value)} />
          </div>
          <div className="field">
            <label>Monthly rent (₹)</label>
            <input className="input" type="number" value={monthlyRent} onChange={(e) => setMonthlyRent(Number(e.target.value))} />
          </div>
          <div className="field">
            <label>Deposit (₹)</label>
            <input className="input" type="number" value={depositAmount} onChange={(e) => setDepositAmount(Number(e.target.value))} />
          </div>
          <div className="field">
            <label>Notice given (days)</label>
            <input className="input" type="number" value={noticeGiven} onChange={(e) => setNoticeGiven(Number(e.target.value))} />
          </div>
          <div className="field">
            <label>Written agreement?</label>
            <select className="select" value={writtenAgreement ? 'yes' : 'no'} onChange={(e) => setWrittenAgreement(e.target.value === 'yes')}>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </div>
        </div>

        <div className="inline-actions">
          <Button onClick={runClassify} disabled={loading}>Classify Intent</Button>
          <Button variant="ghost" onClick={runRights} disabled={loading}>Compute Rights</Button>
          <Button variant="ghost" onClick={runDocument} disabled={loading}>Generate Document</Button>
          <Button variant="ghost" onClick={runQuality} disabled={loading}>Quality Check</Button>
          {error ? <Badge variant="danger">{error}</Badge> : null}
        </div>

        {classification ? <JsonViewer value={classification} collapsed /> : null}
        {rights ? <JsonViewer value={rights} collapsed /> : null}
        {document ? <JsonViewer value={document} /> : null}
        {quality ? <JsonViewer value={quality} collapsed /> : null}
      </div>
    </div>
  );
}

export default LegalCopilotConsole;
