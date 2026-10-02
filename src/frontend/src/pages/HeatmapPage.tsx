import { CivicIssueMap } from '@/components/map/CivicIssueMap';
import { useCivicUi } from '@/app/UiContext';
import { useIssues } from '@/hooks/useIssues';

export function HeatmapPage() {
  const { issuesRevision, setUserLocation } = useCivicUi();
  const { issues, loading, error, refresh } = useIssues(issuesRevision);

  return (
    <section className="py-5 bg-light">
      <div className="container py-5">
        <CivicIssueMap
          title="Civic Issue Map · Demo Records"
          description="Sample SCMIRN records for map interaction; not live or independently verified."
          issues={issues}
          loading={loading}
          error={error}
          onRefresh={() => { void refresh(); }}
          onLocation={setUserLocation}
        />
      </div>
    </section>
  );
}

export default HeatmapPage;
