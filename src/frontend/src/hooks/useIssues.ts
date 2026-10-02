import { useCallback, useEffect, useState } from 'react';
import { apiGet } from '@/api/http';
import { normalizeIssue, type CivicIssue, type IssueApiRecord } from '@/types/issue';

interface IssuesResponse {
  success: boolean;
  issues?: IssueApiRecord[];
  error?: string;
}

export function useIssues(revision = 0) {
  const [issues, setIssues] = useState<CivicIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    const result = await apiGet<IssuesResponse>('/api/issues?limit=100', signal);
    if (signal?.aborted) return;
    if (!result.ok) {
      setError(result.error);
      setLoading(false);
      return;
    }
    if (!result.data?.success) {
      setError(result.data?.error ?? 'Unable to load civic issues.');
      setLoading(false);
      return;
    }
    setIssues((result.data.issues ?? []).map(normalizeIssue));
    setError(null);
    setLoading(false);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void refresh(controller.signal);
    return () => controller.abort();
  }, [refresh, revision]);

  return { issues, loading, error, refresh };
}
