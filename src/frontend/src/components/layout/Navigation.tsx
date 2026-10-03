import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useCivicUi } from '@/app/UiContext';

export function Navigation() {
  const { openAssistant } = useCivicUi();
  const location = useLocation();
  const staffSurface = location.pathname === '/staff';
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
            {!staffSurface ? <button type="button" className="nav-link-custom" onClick={() => openAssistant()}>Civic Guide</button> : null}
            {!staffSurface ? <button type="button" className="nav-link-custom" onClick={() => goToSection('rights')}>Route Check</button> : null}
            {!staffSurface ? <Link to="/services" className="nav-link-custom">Service Directory</Link> : null}
            <Link to="/labs" className="nav-link-custom">Labs · Demo</Link>
            <Link to="/staff" className="nav-link-custom">Staff</Link>
          </div>

          <Link to="/labs" className="btn-primary-civic text-decoration-none"><i className="fas fa-flask me-2" aria-hidden="true" />Open Labs</Link>
        </div>
        <div className="d-flex d-md-none gap-3 py-2 border-top mt-2">
          {!staffSurface ? <Link to="/services" className="nav-link-custom">Service Directory</Link> : null}
          <Link to="/labs" className="nav-link-custom">Labs · Demo</Link>
          <Link to="/staff" className="nav-link-custom">Staff workspace</Link>
        </div>
      </div>
    </nav>
  );
}

export default Navigation;
