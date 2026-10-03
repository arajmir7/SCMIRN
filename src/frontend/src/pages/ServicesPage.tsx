import { useEffect, useMemo, useState } from 'react';
import { resolutionApi, type ServiceSummary } from '@/api/resolution';

const pageTitle = 'Service Directory | SCMIRN';
const pageDescription = 'Browse source-reviewed government service handoffs with review dates and content hashes. SCMIRN does not submit requests or create government references.';
const sha256Pattern = /^[0-9a-f]{64}$/;

function safeHttpsUrl(value: string | null | undefined): URL | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:' || !url.hostname || url.username || url.password || (url.port && url.port !== '443')) return null;
    return url;
  } catch {
    return null;
  }
}

function sourceSupportsHost(source: ServiceSummary['sources'][number], hostname: string): boolean {
  const sourceUrl = safeHttpsUrl(source.canonical_url);
  return source.verification_status === 'VERIFIED'
    && Boolean(source.verified_at || source.verified_on)
    && typeof source.document_hash === 'string'
    && sha256Pattern.test(source.document_hash)
    && sourceUrl?.hostname.toLowerCase() === hostname.toLowerCase();
}

function safeHandoff(service: ServiceSummary): string | null {
  if (service.integration_mode !== 'OFFICIAL_HANDOFF_ONLY') return null;
  const destination = safeHttpsUrl(service.application_channel || service.official_url);
  if (!destination || !service.sources?.some((source) => sourceSupportsHost(source, destination.hostname))) return null;
  return destination.toString();
}

function useServiceDirectoryMetadata() {
  useEffect(() => {
    const previousTitle = document.title;
    let description = document.querySelector<HTMLMetaElement>('meta[name="description"]');
    const createdDescription = !description;
    if (!description) {
      description = document.createElement('meta');
      description.name = 'description';
      document.head.append(description);
    }
    const previousDescription = description.content;
    document.title = pageTitle;
    description.content = pageDescription;
    return () => {
      document.title = previousTitle;
      if (createdDescription) description?.remove();
      else if (description) description.content = previousDescription;
    };
  }, []);
}

function sourceReviewDate(source: ServiceSummary['sources'][number]): string {
  if (source.verified_on) return source.verified_on;
  if (source.verified_at) return source.verified_at.slice(0, 10);
  return 'Date not recorded';
}

function ServiceCard({ service }: { service: ServiceSummary }) {
  const handoff = safeHandoff(service);
  const phone = service.grievance_channel && /^tel:\+?[0-9][0-9 ().-]{2,30}$/.test(service.grievance_channel)
    ? service.grievance_channel
    : null;

  return (
    <article className="card h-100 shadow-sm" aria-labelledby={`service-${service.service_id}`}>
      <div className="card-body d-flex flex-column">
        <div className="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-3">
          <h2 className="h4 mb-0" id={`service-${service.service_id}`}>{service.canonical_name}</h2>
          <span className="badge text-bg-secondary">Official handoff only</span>
        </div>
        <p className="text-body-secondary">{service.description || 'No service description is recorded in the catalogue.'}</p>

        <dl className="row small mb-3">
          <dt className="col-sm-4">Authority</dt>
          <dd className="col-sm-8">{service.authority || 'Not recorded'}</dd>
          <dt className="col-sm-4">Review date</dt>
          <dd className="col-sm-8">{service.last_verified_on || 'Not recorded'}</dd>
          <dt className="col-sm-4">Official deadline</dt>
          <dd className="col-sm-8">{service.official_sla ? 'See the official source; this catalogue does not calculate a deadline.' : 'Not verified in this catalogue.'}</dd>
          <dt className="col-sm-4">Evidence checklist</dt>
          <dd className="col-sm-8">{service.required_evidence.length ? 'Requirements are listed in the source-linked service record.' : 'Not configured in this catalogue. Check the official service before applying.'}</dd>
        </dl>

        {service.eligibility ? <section className="mb-3">
          <h3 className="h6">Scope recorded in the catalogue</h3>
          <p className="small mb-1">{service.eligibility}</p>
        </section> : null}
        {service.exclusions.length ? <section className="mb-3">
          <h3 className="h6">Limits and exclusions</h3>
          <ul className="small mb-0">{service.exclusions.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul>
        </section> : null}

        <section className="border-top pt-3 mb-3">
          <h3 className="h6">Source record</h3>
          <p className="small text-body-secondary">SCMIRN's internal source review is dated; it does not certify the agency, guarantee acceptance, or confirm that the official page has not changed since review.</p>
          {service.sources?.length ? <ul className="list-unstyled mb-0">
            {service.sources.map((source) => {
              const sourceUrl = safeHttpsUrl(source.canonical_url);
              return <li className="small border-top pt-2 mt-2" key={`${source.source_id}-${source.version}`}>
                {sourceUrl ? <a href={sourceUrl.toString()} target="_blank" rel="noopener noreferrer">{source.title}<span className="visually-hidden"> (opens official source in a new tab)</span></a> : <span>{source.title}</span>}
                <div className="text-body-secondary">Source version {source.version} · internal review date {sourceReviewDate(source)}</div>
                <details className="mt-1">
                  <summary>View source URL and content hash</summary>
                  <dl className="mt-2 mb-0">
                    <dt>Canonical URL</dt><dd className="text-break">{source.canonical_url}</dd>
                    <dt>SHA-256 content hash</dt><dd><code className="text-break">{source.document_hash || 'Not recorded'}</code></dd>
                  </dl>
                </details>
              </li>;
            })}
          </ul> : <p className="small text-body-secondary">Source metadata is unavailable, so no handoff link is shown.</p>}
        </section>

        <div className="alert alert-info small mt-auto mb-0">
          <strong>Nothing has been filed.</strong> SCMIRN does not send your information, create a government reference, or receive an official status update.
          <div className="d-flex flex-wrap gap-3 mt-2">
            {handoff ? <a href={handoff} target="_blank" rel="noopener noreferrer">Open official service channel<span className="visually-hidden"> (opens in a new tab)</span></a> : <span>No destination passes this record’s source, hash, status, date, and host checks.</span>}
            {phone ? <a href={phone}>Call listed number {phone.slice(4)}</a> : null}
          </div>
        </div>
      </div>
    </article>
  );
}

export default function ServicesPage() {
  useServiceDirectoryMetadata();
  const [services, setServices] = useState<ServiceSummary[]>([]);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    void resolutionApi.services(controller.signal).then((response) => {
      if (controller.signal.aborted) return;
      if (!response.ok) {
        setServices([]);
        setError('The service catalogue could not be loaded. Try again later, or use an official source you already trust.');
        return;
      }
      if (!response.data || !Array.isArray(response.data.items)) {
        setServices([]);
        setError('The service catalogue returned an unreadable response. No handoff link is available.');
        return;
      }
      setServices(response.data.items);
    }).finally(() => {
      if (!controller.signal.aborted) setLoading(false);
    });
    return () => controller.abort();
  }, [reload]);

  const filteredServices = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    if (!normalized) return services;
    return services.filter((service) => [
      service.canonical_name,
      service.description,
      service.authority,
      service.eligibility,
      ...service.issue_types,
      ...service.exclusions,
    ].filter(Boolean).join(' ').toLocaleLowerCase().includes(normalized));
  }, [query, services]);

  return (
    <div className="bg-light min-vh-100 pt-5">
      <div className="container py-5">
        <header className="row justify-content-center mb-4">
          <div className="col-lg-9">
            <p className="text-uppercase small fw-semibold text-primary mb-2">Public service directory · prototype</p>
            <h1 className="display-5 fw-bold">Browse service handoffs</h1>
            <p className="lead text-body-secondary">Review a small catalogue of public services and the source records behind each handoff. SCMIRN does not decide eligibility or file an application.</p>
            <div className="alert alert-warning mb-0" role="note">
              Source review dates and hashes are shown for transparency. They are not live verification or an official endorsement. Check the destination page for current scope, fees, evidence, deadlines, and instructions.
            </div>
          </div>
        </header>

        <section aria-labelledby="directory-results-heading">
          <div className="row align-items-end g-3 mb-3">
            <div className="col-md-8 col-lg-6">
              <label className="form-label fw-semibold" htmlFor="service-search">Search services</label>
              <input id="service-search" className="form-control" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Name, authority, or issue type" />
              <div className="form-text">Search stays in this browser; it is not sent to SCMIRN.</div>
            </div>
            <div className="col-md-4 col-lg-6 text-md-end">
              <button type="button" className="btn btn-outline-secondary" onClick={() => setReload((value) => value + 1)} disabled={loading}>
                <i className="fas fa-rotate me-2" aria-hidden="true" />Refresh directory
              </button>
            </div>
          </div>

          <h2 className="visually-hidden" id="directory-results-heading">Service directory results</h2>
          {loading ? <p className="py-4" role="status">Loading source-reviewed service records…</p> : null}
          {!loading && error ? <div className="alert alert-danger" role="alert">{error}</div> : null}
          {!loading && !error && services.length === 0 ? <div className="card"><div className="card-body"><h2 className="h5">No handoffs are currently listed</h2><p className="mb-0">The catalogue has no service with a complete source record. This does not mean that no official service exists.</p></div></div> : null}
          {!loading && !error && services.length > 0 ? <p className="small text-body-secondary" role="status">Showing {filteredServices.length} of {services.length} catalogue entries.</p> : null}
          {!loading && !error && services.length > 0 && filteredServices.length === 0 ? <p className="py-3">No catalogue entry matches “{query}”. Try a broader search.</p> : null}
          <div className="row g-4">
            {filteredServices.map((service) => <div className="col-12 col-lg-6" key={`${service.service_id}-${service.version}`}><ServiceCard service={service} /></div>)}
          </div>
        </section>
      </div>
    </div>
  );
}
