import { useCivicUi } from '@/app/UiContext';
import { CivicIssueMap } from '@/components/map/CivicIssueMap';
import { useIssues } from '@/hooks/useIssues';

export function CivicMap() {
  const { issuesRevision, setUserLocation } = useCivicUi();
  const { issues, loading, error, refresh } = useIssues(issuesRevision);
  return (
    <CivicIssueMap
      title="Civic Issue Map · Demo Records"
      description="Sample SCMIRN records for map interaction; not live or independently verified"
      issues={issues}
      loading={loading}
      error={error}
      onRefresh={() => { void refresh(); }}
      onLocation={setUserLocation}
      showRecentReports
    />
  );
}

export default CivicMap;
