import { useCallback, useEffect, useMemo, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import { BarElement, CategoryScale, Chart as ChartJS, LinearScale, Tooltip } from 'chart.js';
import { apiGet } from '@/api/http';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

interface AnalyticsResponse {
  success: boolean;
  summary?: { total_reports?: number; critical_share?: number; predicted_sla?: string; top_bottleneck?: string };
  category_distribution?: Record<string, number>;
  status_distribution?: Record<string, number>;
  error?: string;
}

export function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    const result = await apiGet<AnalyticsResponse>('/api/analytics/summary', signal);
    if (signal?.aborted) return;
    if (!result.ok) {
      setError(result.error);
      setData(null);
    } else if (!result.data?.success) {
      setError(result.data?.error ?? 'Unable to load analytics.');
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
  const categoryChart = useMemo(() => ({
    labels: Object.keys(data?.category_distribution ?? {}),
    datasets: [{ label: 'Count', data: Object.values(data?.category_distribution ?? {}), borderRadius: 8, backgroundColor: 'rgba(6, 182, 212, 0.75)' }],
  }), [data?.category_distribution]);
  const statusChart = useMemo(() => ({
    labels: Object.keys(data?.status_distribution ?? {}),
    datasets: [{ label: 'Count', data: Object.values(data?.status_distribution ?? {}), borderRadius: 8, backgroundColor: 'rgba(15, 23, 42, 0.75)' }],
  }), [data?.status_distribution]);
  const options = useMemo(() => ({ responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }), []);
  const summary = data?.summary ?? {};

  return (
    <section className="py-5 bg-light">
      <div className="container py-5">
        <div className="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
          <div><h1 className="display-6 fw-bold mb-1">Demo Record Summary</h1><p className="text-muted mb-0">Descriptive summaries from sample SCMIRN records; no outcome prediction or agency feed.</p></div>
          <button type="button" className="btn btn-dark" onClick={() => void refresh()} disabled={loading}><i className="fas fa-chart-line me-2" aria-hidden="true" />{loading ? 'Refreshing...' : 'Refresh Insights'}</button>
        </div>
        {error ? <div className="alert alert-danger" role="alert">{error}</div> : null}
        <div className="row g-3 mb-4">
          {[
            ['Total Reports', String(summary.total_reports ?? 0)],
            ['Critical Share', `${summary.critical_share ?? 0}%`],
            ['Predicted SLA', 'Not available'],
            ['Bottleneck', 'Not verified'],
          ].map(([label, value]) => <div className="col-md-3" key={label}><div className="tracker-kpi"><div className="tracker-kpi-label">{label}</div><div className="tracker-kpi-value">{loading ? '…' : value}</div></div></div>)}
        </div>
        <div className="row g-4">
          <div className="col-lg-6"><section className="card border-0 shadow-sm h-100"><div className="card-header bg-white border-0 py-3"><h2 className="h5 fw-bold mb-0">Category Distribution</h2></div><div className="card-body">{Object.keys(data?.category_distribution ?? {}).length ? <Bar data={categoryChart} options={options} height={240} aria-label="Category distribution chart" /> : <p className="text-muted">{loading ? 'Loading analytics...' : 'No category data available.'}</p>}</div></section></div>
          <div className="col-lg-6"><section className="card border-0 shadow-sm h-100"><div className="card-header bg-white border-0 py-3"><h2 className="h5 fw-bold mb-0">Status Distribution</h2></div><div className="card-body">{Object.keys(data?.status_distribution ?? {}).length ? <Bar data={statusChart} options={options} height={240} aria-label="Status distribution chart" /> : <p className="text-muted">{loading ? 'Loading analytics...' : 'No status data available.'}</p>}</div></section></div>
        </div>
      </div>
    </section>
  );
}

export default AnalyticsPage;
