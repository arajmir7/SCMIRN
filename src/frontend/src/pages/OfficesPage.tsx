import { useEffect, useState } from 'react';
import { apiGet } from '@/api/http';

interface Office {
  id: number;
  name: string;
  department: string;
  address: string;
  phone?: string | null;
  timings?: string | null;
  services?: string | null;
  rating?: number | null;
}

interface OfficesResponse { success: boolean; offices?: Office[]; error?: string }

export function OfficesPage() {
  const [offices, setOffices] = useState<Office[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    void apiGet<OfficesResponse>('/api/offices', controller.signal).then((result) => {
      if (controller.signal.aborted) return;
      if (!result.ok) setError(result.error);
      else if (!result.data?.success) setError(result.data?.error ?? 'Unable to load offices.');
      else setOffices(result.data.offices ?? []);
      setLoading(false);
    });
    return () => controller.abort();
  }, []);

  return (
    <section className="py-5">
      <div className="container py-5">
        <div className="row justify-content-center text-center mb-4"><div className="col-lg-8">
          <h1 className="display-5 fw-bold">Office Directory Demo</h1>
          <p className="lead text-muted">Sample office records. Details are not confirmed as current or officially connected.</p>
        </div></div>
        {loading ? <p className="text-center text-muted" role="status">Loading sample directory records...</p> : null}
        {error ? <div className="alert alert-danger" role="alert">{error}</div> : null}
        {!loading && !error && !offices.length ? <p className="text-center text-muted">No offices available yet.</p> : null}
        <div className="row g-4">
          {offices.map((office) => <div className="col-md-6 col-lg-4" key={office.id}>
            <article className="card h-100 border-0 shadow-sm"><div className="card-body">
              <h2 className="h5 fw-bold mb-1">{office.name}</h2>
              <div className="text-muted small mb-2">{office.department}</div>
              <div className="small mb-2"><i className="fas fa-map-marker-alt me-2 text-muted" aria-hidden="true" />{office.address}</div>
              <div className="small mb-2"><i className="fas fa-phone me-2 text-muted" aria-hidden="true" />{office.phone || 'N/A'}</div>
              <div className="small mb-2"><i className="fas fa-clock me-2 text-muted" aria-hidden="true" />{office.timings || 'N/A'}</div>
              <div className="small text-muted">{office.services || 'General services'}</div>
            </div></article>
          </div>)}
        </div>
      </div>
    </section>
  );
}

export default OfficesPage;
