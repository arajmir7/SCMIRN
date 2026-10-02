import { lazy, Suspense, useState } from 'react';
import { DocumentCard } from '@/features/documents/components/DocumentCard';

const CivicMap = lazy(() => import('@/features/maps/components/CivicMap'));
const IoTConsole = lazy(() => import('@/features/iot/components/IoTConsole'));
const IssueRegistryConsole = lazy(() => import('@/features/blockchain/components/IssueRegistryConsole'));
const LegalCopilotConsole = lazy(() => import('@/features/legal/components/LegalCopilotConsole'));
const GamificationConsole = lazy(() => import('@/features/gamification/components/GamificationConsole'));
const ResilienceConsole = lazy(() => import('@/features/resilience/components/ResilienceConsole'));
const DigitalTwinConsole = lazy(() => import('@/features/twin/components/DigitalTwinConsole'));
const CityOrganismConsole = lazy(() => import('@/features/future/components/CityOrganismConsole'));
const EnterpriseCommandCenter = lazy(() => import('@/features/enterprise/components/EnterpriseCommandCenter'));

const workspaces = [
  { id: 'map', label: 'Civic Map · Demo Records', detail: 'Sample issue locations; no live feed or funding', component: CivicMap },
  { id: 'iot', label: 'IoT Predictive Maintenance · Simulation', detail: 'Synthetic sensor payloads and sample asset health', component: IoTConsole },
  { id: 'blockchain', label: 'Blockchain Registry · Simulation', detail: 'Local hash demonstration; no blockchain network', component: IssueRegistryConsole },
  { id: 'legal', label: 'Legal Co-Pilot · Experimental', detail: 'Unreviewed information; not legal advice', component: LegalCopilotConsole },
  { id: 'gamification', label: 'Civic Score & Challenges · Demo', detail: 'Sample scores and badges; no reputation service', component: GamificationConsole },
  { id: 'resilience', label: 'Resilience & Mutual Aid · Simulation', detail: 'No real volunteer dispatch or aid matching', component: ResilienceConsole },
  { id: 'twin', label: 'Digital Twin · Simulation', detail: 'Synthetic scenario inputs and outputs', component: DigitalTwinConsole },
  { id: 'city-brain', label: 'City Organism · Simulation', detail: 'Concept demonstrations only', component: CityOrganismConsole },
  { id: 'enterprise', label: 'Enterprise Command Center · Demo', detail: 'Sample analytics; not connected to agency operations', component: EnterpriseCommandCenter },
] as const;

function DocumentLookup() {
  const [documentId, setDocumentId] = useState('');
  const [activeId, setActiveId] = useState('');
  const [downloadError, setDownloadError] = useState('');

  async function download(id: string) {
    setDownloadError('');
    try {
      const response = await fetch(`/api/documents/${encodeURIComponent(id)}/download`);
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        setDownloadError(data?.error ?? `PDF download is unavailable (HTTP ${response.status}).`);
        return;
      }
      const file = await response.blob();
      const url = URL.createObjectURL(file);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${id}.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch {
      setDownloadError('Unable to download this document.');
    }
  }

  return (
    <div className="platform-workspace">
      <p className="helper-text mb-3">Prototype lookup only. Use synthetic data; stored drafts may contain personal information. PDF delivery is not available in production.</p>
      <form className="input-group mb-3" noValidate onSubmit={(event) => { event.preventDefault(); const id = documentId.trim(); if (!id) { setDownloadError('Enter a document ID.'); event.currentTarget.querySelector<HTMLInputElement>('#stored-document-id')?.focus(); return; } setDownloadError(''); setActiveId(id); }}>
        <label className="visually-hidden" htmlFor="stored-document-id">Document ID</label>
        <input id="stored-document-id" className="form-control" value={documentId} onChange={(event) => setDocumentId(event.target.value)} placeholder="Document ID" required />
        <button type="submit" className="btn btn-dark">Load Document</button>
      </form>
      {activeId ? <DocumentCard documentId={activeId} onDownload={(id) => void download(id)} /> : null}
      {downloadError ? <div className="alert alert-warning mt-3" role="alert">{downloadError}</div> : null}
    </div>
  );
}

export function PlatformPage() {
  const [active, setActive] = useState<string | null>(null);
  const chosen = workspaces.find((workspace) => workspace.id === active);
  const ActiveWorkspace = chosen?.component;

  return (
    <section className="platform-route py-5 bg-light">
      <div className="container py-5">
        <header className="platform-route-heading mb-4">
          <span className="badge bg-warning bg-opacity-10 text-dark mb-3">Prototype · Simulated and sample data</span>
          <h1 className="display-5 fw-bold">Prototype Workspaces</h1>
          <p className="lead text-muted mb-0">These experimental workspaces are not connected to government systems. Production APIs are disabled pending review.</p>
        </header>

        {!chosen ? (
          <div className="row g-4">
            {workspaces.map((workspace) => <div className="col-md-6 col-lg-4" key={workspace.id}>
              <article className="feature-civic platform-workspace-card h-100">
                <div className="icon-circle"><i className="fas fa-layer-group" aria-hidden="true" /></div>
                <h2 className="h4">{workspace.label}</h2>
                <p className="text-muted">{workspace.detail}</p>
                <button type="button" className="btn btn-sm btn-dark" onClick={() => setActive(workspace.id)}>Open Workspace</button>
              </article>
            </div>)}
            <div className="col-md-6 col-lg-4">
              <article className="feature-civic platform-workspace-card h-100">
                <div className="icon-circle"><i className="fas fa-file-alt" aria-hidden="true" /></div>
                <h2 className="h4">Document Intelligence</h2>
                <p className="text-muted">Review a stored document and request its PDF download.</p>
                <button type="button" className="btn btn-sm btn-dark" onClick={() => setActive('documents')}>Open Workspace</button>
              </article>
            </div>
          </div>
        ) : (
          <section className="platform-active-workspace">
            <div className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
              <div><h2 className="h3 fw-bold mb-1">{chosen?.label ?? 'Document Intelligence'}</h2><p className="text-muted mb-0">{chosen?.detail ?? 'Document lookup and delivery'}</p></div>
              <button type="button" className="btn btn-outline-dark" onClick={() => setActive(null)}><i className="fas fa-arrow-left me-2" aria-hidden="true" />All Workspaces</button>
            </div>
            <div className="card border-0 shadow-sm"><div className="card-body p-4">
              {ActiveWorkspace ? <Suspense fallback={<p className="text-muted" role="status">Loading workspace...</p>}><ActiveWorkspace /></Suspense> : <DocumentLookup />}
            </div></div>
          </section>
        )}
      </div>
    </section>
  );
}

export default PlatformPage;
