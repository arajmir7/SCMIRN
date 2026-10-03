import { Link } from 'react-router-dom';

export function Footer() {
  return (
    <footer className="bg-white border-top py-5 mt-5" id="footer">
      <div className="container">
        <div className="row g-4">
          <div className="col-lg-4">
            <h2 className="h4 fw-bold mb-3">🏛️ SCMIRN</h2>
            <p className="text-muted">A civic technology prototype for source-gated route guidance. Not a government service, legal adviser, or filing channel.</p>
          </div>
          <div className="col-lg-2">
            <h3 className="h6 fw-bold mb-3">Platform</h3>
            <ul className="list-unstyled text-muted small">
              <li className="mb-2"><Link to="/services" className="text-decoration-none text-muted">Public Service Directory</Link></li>
              <li className="mb-2"><Link to="/#features" className="text-decoration-none text-muted">Problem Solver</Link></li>
              <li className="mb-2"><Link to="/labs" className="text-decoration-none text-muted">Labs · Demo Workspaces</Link></li>
              <li className="mb-2"><Link to="/labs/offices" className="text-decoration-none text-muted">Office Directory · Demo</Link></li>
              <li className="mb-2"><Link to="/labs/documents" className="text-decoration-none text-muted">Draft Templates · Demo</Link></li>
              <li className="mb-2"><Link to="/labs/heatmap" className="text-decoration-none text-muted">Issue Map · Demo</Link></li>
            </ul>
          </div>
          <div className="col-lg-2">
            <h3 className="h6 fw-bold mb-3">Resources</h3>
            <ul className="list-unstyled text-muted small">
              <li className="mb-2"><Link to="/#rights" className="text-decoration-none text-muted">Route Check Limits</Link></li>
              <li className="mb-2"><Link to="/staff" className="text-decoration-none text-muted">Staff workspace</Link></li>
              <li className="mb-2"><Link to="/labs/platform" className="text-decoration-none text-muted">Platform Showcase · Demo</Link></li>
              <li className="mb-2"><Link to="/labs/tracker" className="text-decoration-none text-muted">SCMIRN Records · Demo</Link></li>
            </ul>
          </div>
          <div className="col-lg-4">
            <h3 className="h6 fw-bold mb-3">Updates</h3>
            <p className="text-muted small">Newsletter signup is not available in this prototype.</p>
          </div>
        </div>
        <hr className="my-4" />
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-3">
          <small className="text-muted">© 2026 SCMIRN. Prototype only · no government affiliation.</small>
          <div className="d-flex gap-4 small text-muted">
            <span>No public privacy policy published</span>
            <span>No support channel configured</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
