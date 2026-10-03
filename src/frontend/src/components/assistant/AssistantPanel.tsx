import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { apiGet } from '@/api/http';
import { resolutionApi, type ResolutionResult, type ServiceSummary, canRenderOfficialHandoff } from '@/api/resolution';

interface AssistantPanelProps {
  open: boolean;
  initialPrompt?: string;
  onClose: () => void;
}

function newRequestKey() {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `route-${Date.now()}-${Math.floor(Math.random() * 1_000_000)}`;
}

export function AssistantPanel({ open, initialPrompt, onClose }: AssistantPanelProps) {
  const [description, setDescription] = useState('');
  const [consent, setConsent] = useState(false);
  const [requestKey, setRequestKey] = useState(newRequestKey);
  const [result, setResult] = useState<ResolutionResult | null>(null);
  const [services, setServices] = useState<ServiceSummary[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [servicesLoading, setServicesLoading] = useState(false);
  const [servicesError, setServicesError] = useState('');
  const descriptionRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!open) return;
    if (initialPrompt) setDescription(initialPrompt);
    descriptionRef.current?.focus();
  }, [open, initialPrompt]);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setServicesLoading(true);
    void apiGet<{ items?: ServiceSummary[] }>('/api/v1/services', controller.signal).then((response) => {
      if (controller.signal.aborted) return;
      if (!response.ok) {
        setServices([]);
        setServicesError('The service directory is unavailable right now.');
        return;
      }
      setServicesError('');
      setServices(response.data.items ?? []);
    }).finally(() => {
      if (!controller.signal.aborted) setServicesLoading(false);
    });
    return () => controller.abort();
  }, [open]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = description.trim();
    if (loading) return;
    if (!text) {
      setError('Enter a description before checking for a route.');
      descriptionRef.current?.focus();
      return;
    }
    if (!consent) {
      setError('Consent is required before the description is processed.');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);
    const response = await resolutionApi.triage({ description: text, consent_to_process: true }, requestKey);
    setLoading(false);
    if (!response.ok) {
      setError(response.error || 'We could not check this description. Please try again.');
      return;
    }
    setResult(response.data);
  }

  function clearDescription() {
    setDescription('');
    setConsent(false);
    setResult(null);
    setError('');
    setRequestKey(newRequestKey());
    descriptionRef.current?.focus();
  }

  return (
    <section className="chat-intelligence" style={{ display: open ? 'flex' : 'none' }} aria-label="SCMIRN source-linked problem solver" aria-hidden={!open}>
      <div className="chat-header">
        <div className="d-flex justify-content-between align-items-center">
          <div>
            <h2 className="h5 fw-bold mb-1"><i className="fas fa-brain me-2" aria-hidden="true" />Problem Solver</h2>
            <small className="opacity-75">Source-linked route guidance · no government filing</small>
          </div>
          <button type="button" onClick={onClose} className="btn btn-link text-white p-0" aria-label="Close problem solver">
            <i className="fas fa-times fa-lg" aria-hidden="true" />
          </button>
        </div>
      </div>

      <div className="chat-body p-3" aria-live="polite" aria-relevant="additions text">
        <p className="small text-muted">Describe what happened. SCMIRN uses deterministic rules and shows a service only when a dated internal source review supports a handoff. Check the official page for current instructions.</p>
        <form onSubmit={submit} noValidate>
          <label className="form-label fw-semibold" htmlFor="triage-description">Problem description</label>
          <textarea
            ref={descriptionRef}
            id="triage-description"
            className="form-control resize-none"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            rows={5}
            maxLength={8000}
            required
            aria-describedby="triage-privacy-note triage-character-count"
            placeholder="For example: I noticed an online payment I did not authorise."
          />
          <div className="d-flex justify-content-between gap-2 mt-1">
            <small id="triage-privacy-note" className="text-muted">Avoid Aadhaar, PAN, account numbers, passwords or OTPs.</small>
            <small id="triage-character-count" className="text-muted text-nowrap" aria-live="polite">{description.length}/8000</small>
          </div>
          <div className="form-check bg-light rounded-3 p-3 mt-3">
            <input
              id="triage-consent"
              className="form-check-input"
              type="checkbox"
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
            />
            <label htmlFor="triage-consent" className="form-check-label small">
              I agree to process this description for route matching. The description itself is not stored; SCMIRN records derived route facts and version metadata with a 30-day deletion deadline.
            </label>
          </div>
          <div className="d-flex flex-wrap gap-2 mt-3">
            <button className="btn btn-primary" type="submit" disabled={!consent || !description.trim() || loading}>
              {loading ? <><span className="spinner-border spinner-border-sm me-2" aria-hidden="true" />Checking route…</> : 'Find the correct action'}
            </button>
            {description || result ? <button className="btn btn-outline-secondary" type="button" onClick={clearDescription}>Clear</button> : null}
          </div>
        </form>

        {error ? <div role="alert" className="alert alert-danger mt-3 mb-0">{error}</div> : null}
        {result ? (
          <div className="message-ai mt-3" role="status" aria-live="polite">
            <div className="small fw-bold text-uppercase text-muted">Route result · {result.outcome.replace(/_/g, ' ')}</div>
            <h3 className="h6 fw-bold mt-2">{result.authority?.name ?? 'No responsible authority confirmed'}</h3>
            <p className="small mb-2">{result.explanation}</p>
            {result.urgent_human_help_required ? <p className="alert alert-danger py-2 small"><i className="fas fa-triangle-exclamation me-2" aria-hidden="true" />If someone is in immediate danger, contact local emergency services or a trusted person now.</p> : null}
            {result.official_handoff && canRenderOfficialHandoff(result) ? (
              <div className="alert alert-info py-2">
                <div className="fw-semibold">Continue with the official service</div>
                <div className="small">{result.official_handoff.message}</div>
                {result.official_handoff.url ? <a href={result.official_handoff.url} target="_blank" rel="noopener noreferrer" className="d-inline-block mt-2">Open official portal <i className="fas fa-arrow-up-right-from-square ms-1" aria-hidden="true" /></a> : null}
                {result.official_handoff.phone ? <a href={result.official_handoff.phone} className="d-inline-block mt-2 ms-3">Call official number</a> : null}
              </div>
            ) : null}
            <dl className="small row border-top pt-2 mb-1">
              <dt className="col-5">Route rule</dt><dd className="col-7">{result.route_rule_version}</dd>
              <dt className="col-5">Service registry</dt><dd className="col-7">{result.service_registry_version}</dd>
              <dt className="col-5">Submission status</dt><dd className="col-7">Not submitted</dd>
              <dt className="col-5">Decision deletion deadline</dt><dd className="col-7">{new Date(result.retention_until).toLocaleDateString()}</dd>
            </dl>
            {result.sources.map((source) => (
              <div key={`${source.source_id}-${source.version}`} className="small border-top pt-2 mt-2">
                <a href={source.canonical_url} target="_blank" rel="noopener noreferrer">{source.title}</a>
                <div className="text-muted">Version {source.version} · catalog status {source.verification_status} · internal review date {source.verified_on ?? source.reviewed_on ?? (source.verified_at ? new Date(source.verified_at).toLocaleDateString() : 'not recorded')} · {source.document_hash ? `SHA-256 ${source.document_hash}` : 'content hash unavailable'}</div>
              </div>
            ))}
          </div>
        ) : null}

        <div className="border-top mt-3 pt-3">
          <h3 className="h6 fw-bold">Services with source records</h3>
          <p className="small text-muted">The directory shows SCMIRN review dates and source hashes; it is not a live check of agency pages.</p>
          <Link className="small" to="/services">Browse the service directory</Link>
          {servicesLoading ? <p className="small text-muted" role="status">Checking the service registry…</p> : null}
          {servicesError ? <p role="alert" className="small text-danger">{servicesError} Open the directory later to retry.</p> : null}
          {!servicesLoading && !servicesError && services.length === 0 ? <p className="small text-muted mb-0">No service record with a complete source review is available.</p> : null}
          {services.map((service) => <div key={`${service.service_id}-${service.version}`} className="small border rounded p-2 mb-2"><strong>{service.canonical_name}</strong><div className="text-muted">{service.authority ?? 'Authority not listed'} · {service.integration_mode}</div><div className="text-muted">Internal source review date: {service.last_verified_on ?? 'not recorded'}</div></div>)}
        </div>
        <p className="small text-muted border-top mt-3 pt-3 mb-0">SCMIRN route guidance is not legal representation, an emergency response or a government filing.</p>
      </div>
    </section>
  );
}

export function AssistantOrb({ onClick, expanded }: { onClick: () => void; expanded: boolean }) {
  return (
    <button type="button" className="ai-orb" onClick={onClick} aria-label={expanded ? 'Close Problem Solver' : 'Open Problem Solver'} aria-expanded={expanded}>
      <i className="fas fa-robot" aria-hidden="true" />
    </button>
  );
}
