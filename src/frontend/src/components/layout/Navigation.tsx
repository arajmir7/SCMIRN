import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useCivicUi } from '@/app/UiContext';

export function Navigation() {
  const { openReport, openAssistant } = useCivicUi();
  const location = useLocation();
  const navigate = useNavigate();

  function goToSection(id: string) {
    if (location.pathname !== '/') {
      navigate(`/#${id}`);
      return;
    }
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  }

  return (
    <nav className="nav-scmirn" aria-label="Main navigation">
      <div className="container">
        <div className="d-flex justify-content-between align-items-center">
          <Link to="/" className="d-flex align-items-center gap-3 text-decoration-none" aria-label="SCMIRN home">
            <div className="display-font fw-bold fs-4 text-dark">🏛️ SCMIRN</div>
            <span className="badge bg-primary bg-opacity-10 text-primary d-none d-md-inline">Civic Technology Prototype</span>
          </Link>

          <div className="d-none d-md-flex align-items-center gap-4">
            <button type="button" className="nav-link-custom" onClick={() => openAssistant()}>Civic Guide</button>
            <button type="button" className="nav-link-custom" onClick={() => goToSection('rights')}>Route Check</button>
            <Link to="/heatmap" className="nav-link-custom">Issue Map · Demo</Link>
            <Link to="/tracker" className="nav-link-custom">SCMIRN Records · Demo</Link>
            <Link to="/analytics" className="nav-link-custom">Analytics · Demo</Link>
            <Link to="/documents" className="nav-link-custom">Draft Templates</Link>
          </div>

          <button type="button" className="btn-primary-civic" onClick={openReport}>
            <i className="fas fa-plus me-2" aria-hidden="true" />Create Demo Record
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navigation;
