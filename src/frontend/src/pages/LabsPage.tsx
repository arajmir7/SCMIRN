import { Link, Outlet } from 'react-router-dom';
import { useCivicUi } from '@/app/UiContext';

const labs = [
  { path: 'offices', title: 'Office directory · Demo', detail: 'Sample office listings. No verified agency directory feed is connected.' },
  { path: 'heatmap', title: 'Issue map · Demo', detail: 'Map views use sample or development records, not live agency reports.' },
  { path: 'tracker', title: 'SCMIRN records · Demo', detail: 'Local prototype statuses are not official complaint or application status.' },
  { path: 'analytics', title: 'Analytics · Demo', detail: 'Descriptive summaries only. No predictions or measured public outcomes.' },
  { path: 'documents', title: 'Draft templates · Demo', detail: 'Unreviewed drafts are not legal advice and are not submitted to an authority.' },
  { path: 'platform', title: 'Platform showcase · Demo', detail: 'Concept workspaces are not connected to government operations.' },
];

export function LabsLayout() {
  return (
    <div className="container py-4 py-lg-5 mt-5">
      <div className="alert alert-warning border mb-4" role="note">
        <strong>Labs · demonstration only.</strong> These workspaces may use sample or development data. Do not enter personal, confidential, or real case information. No agency service connection or official case status is provided here.
      </div>
      <Outlet />
    </div>
  );
}

export function LabsPage() {
  const { openReport } = useCivicUi();
  return (
    <section aria-labelledby="labs-title">
      <header className="d-flex flex-column flex-md-row justify-content-between align-items-md-end gap-3 mb-4">
        <div>
          <p className="text-uppercase small fw-semibold text-primary mb-2">Prototype workspaces</p>
          <h1 id="labs-title" className="display-6 fw-bold mb-2">SCMIRN Labs</h1>
          <p className="text-muted mb-0">Explore interface concepts and sample workflows. They are separate from the source-reviewed public service directory and the authenticated staff API.</p>
        </div>
        <button type="button" className="btn btn-outline-primary" onClick={openReport}>Create a sample record</button>
      </header>
      <div className="row g-3">
        {labs.map((lab) => (
          <div className="col-md-6 col-xl-4" key={lab.path}>
            <article className="card h-100 border shadow-sm">
              <div className="card-body d-flex flex-column">
                <span className="badge text-bg-warning align-self-start mb-3">Demo</span>
                <h2 className="h5 fw-bold">{lab.title}</h2>
                <p className="text-muted flex-grow-1">{lab.detail}</p>
                <Link className="btn btn-outline-dark align-self-start" to={`/labs/${lab.path}`}>Open demo workspace</Link>
              </div>
            </article>
          </div>
        ))}
      </div>
      <p className="small text-muted mt-4 mb-0">Use the <Link to="/staff">staff workspace</Link> only if your organization has provisioned an account and enabled staff authentication. Access remains subject to the server’s tenant, role, and MFA checks.</p>
    </section>
  );
}

export default LabsPage;
