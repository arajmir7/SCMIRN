import { useCallback, useEffect, useState } from 'react';
import { apiGet } from '@/api/http';

interface TrackerItem {
  public_id?: string;
  title: string;
  status: string;
  priority_tier: string;
  category: string;
  eta_days: number;
  escalation_ready: boolean;
}

interface TrackerResponse {
  success: boolean;
  kpis?: { open_cases?: number; due_escalations?: number; avg_eta_days?: number; avg_funded_progress?: number };
  items?: TrackerItem[];
  error?: string;
}

function statusClass(status: string): string {
  if (status === 'resolved') return 'status-pill status-pill-resolved';
  if (status === 'in_progress' || status === 'funded') return 'status-pill status-pill-progress';
  return 'status-pill status-pill-open';
}

export function TrackerPage() {
  const [data, setData] = useState<TrackerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    const result = await apiGet<TrackerResponse>('/api/tracker/summary?limit=30', signal);
    if (signal?.aborted) return;
    if (!result.ok) {
      setError(result.error);
      setData(null);
    } else if (!result.data?.success) {
      setError(result.data?.error ?? 'Unable to load tracker.');
      setData(null);
    } else {
      setError('');
      setData(result.data);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void refresh(controller.signal);
    return () => controller.abort();
  }, [refresh]);

  const kpis = data?.kpis ?? {};
  return (
    <section className="py-5 bg-light">
      <div className="container py-5">
        <div className="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
          <div><h1 className="display-6 fw-bold mb-1">SCMIRN Record Tracker</h1><p className="text-muted mb-0">Local demo records only. Not connected to official complaints or case status feeds.</p></div>
          <button type="button" className="btn btn-dark" onClick={() => void refresh()} disabled={loading}><i className="fas fa-rotate me-2" aria-hidden="true" />{loading ? 'Refreshing...' : 'Refresh'}</button>
        </div>
        <div className="row g-3 mb-4">
          {[
            ['Open Demo Records', String(kpis.open_cases ?? 0)],
            ['Escalation Status', 'Not tracked'],
            ['Official ETA', 'Not available'],
            ['Funding', 'Not available'],
          ].map(([label, value]) => <div className="col-md-3" key={label}><div className="tracker-kpi"><div className="tracker-kpi-label">{label}</div><div className="tracker-kpi-value">{value}</div></div></div>)}
        </div>
        <div className="card border-0 shadow-sm">
          <div className="card-header bg-white border-0 py-3"><h2 className="h5 fw-bold mb-0">Sample Record Queue</h2></div>
          <div className="card-body p-0"><div className="table-responsive">
            <table className="table align-middle mb-0">
              <thead className="table-light"><tr><th scope="col">Record</th><th scope="col">SCMIRN Status</th><th scope="col">Sample Priority</th><th scope="col">Category</th><th scope="col">ETA</th><th scope="col">Escalation</th></tr></thead>
              <tbody>
                {loading ? <tr><td colSpan={6} className="text-center text-muted py-4">Loading tracker data...</td></tr> : null}
                {!loading && error ? <tr><td colSpan={6} className="text-center text-danger py-4" role="alert">{error}</td></tr> : null}
                {!loading && !error && !data?.items?.length ? <tr><td colSpan={6} className="text-center text-muted py-4">No cases found.</td></tr> : null}
                {!loading && !error ? (data?.items ?? []).map((item, index) => {
                  const priorityClass = item.priority_tier === 'critical' ? 'danger' : item.priority_tier === 'high' ? 'warning' : 'info';
                  return <tr key={item.public_id ?? `${item.title}-${index}`}>
                    <td><div className="fw-semibold">{item.title}</div><small className="text-muted">{item.public_id || 'N/A'}</small></td>
                    <td><span className={statusClass(item.status)}>{item.status}</span></td>
                    <td><span className={`badge bg-${priorityClass} ${priorityClass === 'warning' || priorityClass === 'info' ? 'text-dark' : ''}`}>{item.priority_tier}</span></td>
                    <td className="text-capitalize">{item.category}</td><td>Not available</td>
                    <td>Not tracked</td>
                  </tr>;
                }) : null}
              </tbody>
            </table>
          </div></div>
        </div>
      </div>
    </section>
  );
}

export default TrackerPage;
