import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCivicUi } from '@/app/UiContext';
import { CivicIssueMap } from '@/components/map/CivicIssueMap';
import { useIssues } from '@/hooks/useIssues';

const pillars = [
  {
    id: 'problem_solver', icon: 'fa-route', title: '🧭 Civic Guide',
    copy: 'Describe a civic problem and check for a route supported by a current, verified source. Unverified cases return no official handoff.',
    points: ['Source-linked route checks', 'Consent before processing', 'No government filing'],
  },
  {
    id: 'office_locator', icon: 'fa-map-marked-alt', title: '🏛️ Office Directory · Demo',
    copy: 'Explore the local office directory demo. Entries are not confirmed as current or officially connected.',
    points: ['Sample directory records', 'No live agency feed', 'Verify details independently'],
  },
  {
    id: 'rights_engine', icon: 'fa-gavel', title: '⚖️ Source-Verified Route Guidance',
    copy: 'Review source-gated route guidance. SCMIRN does not provide legal advice or determine your rights.',
    points: ['Official sources required', 'No legal conclusions', 'Human advice may be needed'],
  },
  {
    id: 'document_gen', icon: 'fa-file-alt', title: '📝 Draft Document Templates',
    copy: 'Inspect draft document templates for completeness. Drafts are not legally reviewed and are not filed for you.',
    points: ['Clearly marked drafts', 'Review before use', 'No agency submission'],
  },
  {
    id: 'heatmap', icon: 'fa-fire', title: '📊 Issue Map · Demo',
    copy: 'View sample civic issue records on a map. Records and locations are not independently verified or live agency data.',
    points: ['Sample records', 'Map visualization', 'No resolution prediction'],
  },
  {
    id: 'tracker', icon: 'fa-tasks', title: '🔔 SCMIRN Records · Demo',
    copy: 'Review SCMIRN demo records. They are not linked to official complaints, applications, or case status feeds.',
    points: ['Local record status', 'No agency connection', 'No escalation alerts'],
  },
  {
    id: 'predictive', icon: 'fa-chart-line', title: '📊 Demo Analytics',
    copy: 'Explore descriptive summaries generated from local demo records. SCMIRN does not predict outcomes or corruption.',
    points: ['Sample aggregates', 'No success prediction', 'No strategic legal advice'],
  },
];

const documentCards = [
  { type: 'rti', color: 'info', icon: 'fa-file-alt', title: 'RTI Draft Template', copy: 'Unreviewed draft template. Check the current official process, fees, and rules before use.' },
  { type: 'fir', color: 'danger', icon: 'fa-exclamation-triangle', title: 'FIR Draft Template', copy: 'Unreviewed draft template. It does not submit or register a police complaint.' },
  { type: 'consumer', color: 'success', icon: 'fa-balance-scale', title: 'Consumer Draft Template', copy: 'Unreviewed draft template. Verify current forum rules and seek qualified advice.' },
  { type: 'pension', color: 'warning', icon: 'fa-wallet', title: 'Pension Grievance', copy: 'Unreviewed draft template. It is not sent to a pension authority.' },
  { type: 'cybercrime', color: 'primary', icon: 'fa-shield-halved', title: 'Cybercrime Complaint', copy: 'Unreviewed draft template. For urgent fraud, contact your bank and official cybercrime channels.' },
  { type: 'electricity', color: 'secondary', icon: 'fa-bolt', title: 'Electricity Grievance', copy: 'Unreviewed draft template. Verify the current provider complaint process before use.' },
] as const;

const impactItems = [
  { title: 'For Citizens', tone: 'primary', copy: 'Check whether a described civic issue has a route backed by a verified official source. Guidance is not legal advice.' },
  { title: 'For Government', tone: 'success', copy: 'Explore a technical prototype. It has no government deployment, agency feed, or operational service connection.' },
  { title: 'For Media', tone: 'info', copy: 'Review local demo records and their limitations. No report is independently verified or live.' },
  { title: 'For Investors', tone: 'warning', copy: 'Assess a pre-deployment prototype. No adoption, impact, revenue, or return metrics are verified.' },
];

export function HomePage() {
  const { openAssistant, openDocument, issuesRevision, setUserLocation } = useCivicUi();
  const navigate = useNavigate();
  const [rightsQuery, setRightsQuery] = useState('');
  const { issues, loading: issuesLoading, error: issuesError, refresh: refreshIssueList } = useIssues(issuesRevision);

  function continueToSourceCheck(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = rightsQuery.trim();
    if (!query) return;
    openAssistant(query);
  }

  function launchPillar(id: string) {
    if (id === 'problem_solver') {
      openAssistant('Help me solve my civic issue step by step');
    } else if (id === 'office_locator') {
      navigate('/offices');
    } else if (id === 'rights_engine') {
      document.getElementById('rights')?.scrollIntoView({ behavior: 'smooth' });
    } else if (id === 'document_gen') {
      openDocument('rti');
    } else if (id === 'heatmap') {
      navigate('/heatmap');
    } else if (id === 'tracker') {
      navigate('/tracker');
    } else if (id === 'predictive') {
      navigate('/analytics');
    }
  }

  return (
    <>
      <section className="hero-civic text-white pt-5" id="home">
        <div className="hero-grid" />
        <div className="container position-relative pt-5 mt-5">
          <div className="row align-items-center min-vh-100">
            <div className="col-lg-7">
              <div className="badge bg-white bg-opacity-10 text-white mb-4 px-3 py-2 rounded-pill border border-white border-opacity-20">
                Citizen-resolution guidance · Prototype
              </div>
              <h1 className="display-2 fw-bold mb-4 glow-text" style={{ lineHeight: 1.1 }}>
                What happened?<br /><span className="hero-accent">Find the next step.</span>
              </h1>
              <p className="lead mb-4 opacity-90 hero-lead">
                Describe the problem in your own words. SCMIRN checks for a currently verified official service and explains when it cannot confirm a route. It does not file a request.
              </p>
              <form onSubmit={continueToSourceCheck} noValidate className="bg-white text-dark rounded-4 p-3 p-md-4 shadow-sm mb-4" aria-label="Start with your problem">
                <label className="form-label fw-semibold" htmlFor="home-problem-query">What happened?</label>
                <textarea id="home-problem-query" className="form-control mb-2 resize-none" rows={3} maxLength={8000}
                  placeholder="Describe the issue. Leave out account numbers, Aadhaar, passwords and OTPs."
                  value={rightsQuery} onChange={(event) => setRightsQuery(event.target.value)} />
                <div className="small text-muted mb-3">Nothing is processed until you review the consent step. No agency submission is made.</div>
                <button type="submit" className="btn btn-primary fw-semibold" disabled={!rightsQuery.trim()}>
                  Find the next step
                </button>
              </form>
              <div className="d-flex flex-wrap gap-3 mb-5">
                <button type="button" className="btn btn-light btn-lg px-4 fw-bold" onClick={() => openAssistant()}>
                  <i className="fas fa-route me-2 text-primary" aria-hidden="true" />Open Civic Guide
                </button>
                <button type="button" className="btn btn-outline-light btn-lg px-4" onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}>Explore Features</button>
              </div>
              <div className="row g-4 mt-2">
                <div className="col-md-4"><div className="floating-card"><div className="h3 fw-bold text-info mb-1">Consent</div><small className="opacity-75">Required before route check</small></div></div>
                <div className="col-md-4"><div className="floating-card" style={{ animationDelay: '1s' }}><div className="h3 fw-bold text-warning mb-1">Source</div><small className="opacity-75">Verified before handoff</small></div></div>
                <div className="col-md-4"><div className="floating-card" style={{ animationDelay: '2s' }}><div className="h3 fw-bold text-success mb-1">No filing</div><small className="opacity-75">You remain in control</small></div></div>
              </div>
            </div>
            <div className="col-lg-5">
              <div className="position-relative">
                <img src="/images/hero-civic.jpg" alt="Citizens working together on civic technology" className="img-fluid rounded-4 shadow-lg hero-photo" />
                <div className="position-absolute bottom-0 start-0 m-3 p-3 bg-white rounded-3 shadow-lg text-dark hero-status-card">
                  <div className="d-flex align-items-center gap-2 mb-2"><div className="bg-warning rounded-circle hero-status-dot" /><small className="fw-bold text-warning">Prototype · Source Check Required</small></div>
                  <small className="text-muted">Some routes have verified public sources. Each handoff is checked at request time.</small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-5 bg-white">
        <div className="container py-5">
          <div className="row justify-content-center text-center mb-5"><div className="col-lg-8">
            <h2 className="display-5 fw-bold mb-4">What is SCMIRN?</h2>
            <p className="lead text-muted"><strong>Smart Civic Micro-Infrastructure Resilience Network</strong> is a prototype for helping people find source-grounded public-service next steps.</p>
          </div></div>
          <div className="row g-4 mb-5">
            <div className="col-md-4 text-center"><div className="bg-primary bg-opacity-10 rounded-4 p-4 mb-3 d-inline-block"><i className="fas fa-route fa-2x text-primary" aria-hidden="true" /></div><h3 className="h4">Source-Gated Routing</h3><p className="text-muted">Unverified sources do not produce an official handoff</p></div>
            <div className="col-md-4 text-center"><div className="bg-warning bg-opacity-10 rounded-4 p-4 mb-3 d-inline-block"><i className="fas fa-scale-balanced fa-2x text-warning" aria-hidden="true" /></div><h3 className="h4">Clear Boundaries</h3><p className="text-muted">Route guidance is not legal advice or emergency response</p></div>
            <div className="col-md-4 text-center"><div className="bg-success bg-opacity-10 rounded-4 p-4 mb-3 d-inline-block"><i className="fas fa-file-lines fa-2x text-success" aria-hidden="true" /></div><h3 className="h4">Draft Templates</h3><p className="text-muted">Unreviewed samples are not submitted to agencies</p></div>
          </div>
        </div>
      </section>

      <section id="rights" className="py-5 bg-light">
        <div className="container py-5"><div className="row align-items-center g-4">
          <div className="col-lg-6">
            <h2 className="display-5 fw-bold mb-3">Source-Gated Route Check</h2>
            <p className="lead text-muted mb-4">Check for a source-supported public-service route. The prototype does not decide legal rights or escalation deadlines.</p>
            <div className="d-flex flex-column gap-3">
              <div className="p-3 rounded-3 bg-white border"><div className="fw-semibold mb-1">Source Verification</div><small className="text-muted">Only a currently verified official source can support a handoff.</small></div>
              <div className="p-3 rounded-3 bg-white border"><div className="fw-semibold mb-1">Conservative Routing</div><small className="text-muted">The service abstains when no verified source supports a route.</small></div>
              <div className="p-3 rounded-3 bg-white border"><div className="fw-semibold mb-1">User-Controlled Next Step</div><small className="text-muted">SCMIRN does not submit requests or provide legal advice.</small></div>
            </div>
          </div>
          <div className="col-lg-6"><div className="bg-white border rounded-4 p-4 shadow-sm">
            <h3 className="h5 fw-bold mb-3">Check for a Verified Route</h3>
            <p className="small text-muted mb-3">Your description is sent for a consented, source-gated route check. SCMIRN does not analyze legal rights.</p>
            <form onSubmit={continueToSourceCheck} noValidate>
              <label className="visually-hidden" htmlFor="rights-query">Describe an issue to check for a verified route</label>
              <textarea id="rights-query" className="form-control mb-3 resize-none" rows={4} placeholder="Describe the civic issue. Do not include account numbers, Aadhaar, passwords, or OTPs." value={rightsQuery} onChange={(event) => setRightsQuery(event.target.value)} />
              <button type="submit" className="btn btn-dark w-100 mb-3" disabled={!rightsQuery.trim()}><i className="fas fa-route me-2" aria-hidden="true" />Continue to Route Check</button>
            </form>
            <div className="small text-muted">Consent is required before processing. Your description is not stored by the route-check service.</div>
          </div></div>
        </div></div>
      </section>

      <section id="features" className="py-5 bg-light">
        <div className="container py-5">
          <div className="text-center mb-5"><h2 className="display-5 fw-bold">Available capabilities</h2><p className="text-muted lead">Live route guidance is limited; other workspaces are labelled demos or draft tools</p></div>
          <div className="row g-4">
            {pillars.map((pillar) => <div className="col-md-6 col-lg-4" key={pillar.id}>
              <article className="feature-civic">
                <div className="icon-circle"><i className={`fas ${pillar.icon}`} aria-hidden="true" /></div>
                <h3 className="h4">{pillar.title}</h3>
                <p className="text-muted">{pillar.copy}</p>
                <ul className="list-unstyled mt-3 small text-muted">{pillar.points.map((point) => <li key={point}><i className="fas fa-check text-success me-2" aria-hidden="true" />{point}</li>)}</ul>
                <button type="button" className="btn btn-sm btn-dark mt-2" onClick={() => launchPillar(pillar.id)}>Open Workspace</button>
              </article>
            </div>)}
          </div>
        </div>
      </section>

      <section className="py-5 bg-white">
        <div className="container"><div className="row align-items-center">
          <div className="col-lg-5 mb-4 mb-lg-0">
            <h2 className="display-5 fw-bold mb-4">Civic Guide</h2>
            <p className="lead text-muted mb-4">A consent-based, source-gated route checker. It does not provide legal advice or contact government agencies.</p>
            <div className="d-flex flex-column gap-3">
              <div className="d-flex align-items-start gap-3"><div className="bg-primary bg-opacity-10 p-2 rounded"><i className="fas fa-route text-primary" aria-hidden="true" /></div><div><h3 className="h6 fw-bold mb-1">Source-Gated Route Check</h3><small className="text-muted">An unverified source results in abstention</small></div></div>
              <div className="d-flex align-items-start gap-3"><div className="bg-success bg-opacity-10 p-2 rounded"><i className="fas fa-shield-alt text-success" aria-hidden="true" /></div><div><h3 className="h6 fw-bold mb-1">Privacy Notice</h3><small className="text-muted">Avoid sensitive identifiers; consent is required</small></div></div>
              <div className="d-flex align-items-start gap-3"><div className="bg-warning bg-opacity-10 p-2 rounded"><i className="fas fa-hand-paper text-warning" aria-hidden="true" /></div><div><h3 className="h6 fw-bold mb-1">No Agency Submission</h3><small className="text-muted">You choose any next step outside this prototype</small></div></div>
            </div>
            <button type="button" className="btn-primary-civic mt-4" onClick={() => openAssistant()}><i className="fas fa-route me-2" aria-hidden="true" />Check a Route</button>
          </div>
          <div className="col-lg-7"><div className="bg-dark rounded-4 p-4 shadow-lg">
            <div className="d-flex align-items-center gap-2 mb-3 border-bottom border-secondary pb-2"><div className="bg-warning rounded-circle hero-status-dot" /><small className="text-light">Example · No live agency connection</small></div>
            <div className="bg-secondary bg-opacity-25 rounded-3 p-3 mb-3"><div className="text-info small mb-1"><i className="fas fa-user me-1" aria-hidden="true" />Example input</div><div className="text-light">"I need help with an online payment I did not authorize."</div></div>
            <div className="bg-primary bg-opacity-25 rounded-3 p-3 mb-3 ms-4"><div className="text-primary small mb-1 text-end">Consent</div><div className="text-light text-end">Required before route matching</div></div>
            <div className="bg-secondary bg-opacity-25 rounded-3 p-3"><div className="text-info small mb-1"><i className="fas fa-route me-1" aria-hidden="true" />Safe default</div><div className="text-light small"><strong>No verified source available</strong><br />The service abstains from recommending an official destination.<br /><br /><strong>No submission is made.</strong></div></div>
          </div></div>
        </div></div>
      </section>

      <section id="map-section" className="py-5 bg-light">
        <div className="container py-5">
          <CivicIssueMap title="Civic Issue Map · Demo Records" description="Sample SCMIRN records for map interaction; not live or independently verified"
            issues={issues} loading={issuesLoading} error={issuesError} onRefresh={() => { void refreshIssueList(); }} onLocation={setUserLocation} showRecentReports />
        </div>
      </section>

      <section id="docs" className="py-5 bg-white">
        <div className="container py-5">
          <div className="text-center mb-5"><h2 className="display-5 fw-bold">Draft Document Templates</h2><p className="lead text-muted">Unreviewed examples only · not legal advice or agency filings</p></div>
          <div className="row g-4">
            {documentCards.map((card) => <div className="col-md-4" key={card.type}>
              <div className="card h-100 border-0 shadow-sm"><div className="card-body">
                <div className="d-flex align-items-center gap-3 mb-3"><div className={`bg-${card.color} bg-opacity-10 p-3 rounded-3`}><i className={`fas ${card.icon} text-${card.color} fa-lg`} aria-hidden="true" /></div><h3 className="h5 fw-bold mb-0">{card.title}</h3></div>
                <p className="text-muted small">{card.copy}</p>
                <button type="button" className={`btn btn-outline-${card.color} btn-sm w-100`} onClick={() => openDocument(card.type)}>Open Generator</button>
              </div></div>
            </div>)}
          </div>
        </div>
      </section>

      <section id="impact" className="py-5 bg-dark text-white">
        <div className="container py-5">
          <div className="row"><div className="col-lg-8 mb-5"><h2 className="display-4 fw-bold mb-4">A Civic Technology<br />Prototype</h2><p className="lead opacity-75">SCMIRN explores source-gated civic route guidance. It is not deployed with a government agency and does not submit or track official cases.</p></div></div>
          <div className="impact-grid mb-5">{impactItems.map((item) => <div className="impact-item bg-white text-dark" key={item.title}><h3 className={`h4 fw-bold text-${item.tone} mb-2`}>{item.title}</h3><p className="text-muted mb-0">{item.copy}</p></div>)}</div>
          <div className="row g-4 text-center">
            <div className="col-md-3"><div className="stat-number">1</div><p className="opacity-75">Explicit consent before route matching</p></div>
            <div className="col-md-3"><div className="stat-number">0</div><p className="opacity-75">Government submissions by SCMIRN</p></div>
            <div className="col-md-3"><div className="stat-number">30d</div><p className="opacity-75">Route decision metadata retention limit</p></div>
            <div className="col-md-3"><div className="stat-number">Source</div><p className="opacity-75">Verified before an official handoff</p></div>
          </div>
        </div>
      </section>
    </>
  );
}

export default HomePage;
