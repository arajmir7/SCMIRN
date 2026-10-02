import { useEffect, useState } from 'react';
import { Button, Badge, JsonViewer } from '@/components/atoms';
import { apiGet } from '@/api/http';
import { getJsonValue } from '@/utils/json';

export function GamificationConsole() {
  const [score, setScore] = useState<unknown>(null);
  const [challenges, setChallenges] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setError(null);
    const scoreRes = await apiGet<unknown>('/api/v1/gamification/score?user_id=demo-user');
    if (!scoreRes.ok) {
      setError(scoreRes.error);
      setScore(scoreRes.details ?? null);
      return;
    }
    setScore(scoreRes.data);

    const currentScore = getJsonValue(scoreRes.data, 'reputation', 'current_score') ?? 420;
    const chalRes = await apiGet<unknown>(`/api/v1/gamification/challenges?user_id=demo-user&current_score=${encodeURIComponent(String(currentScore))}`);
    if (!chalRes.ok) {
      setError(chalRes.error);
      setChallenges(chalRes.details ?? null);
      return;
    }
    setChallenges(chalRes.data);
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <div className="console">
      <div className="console-grid">
        <p className="helper-text">Demo civic score, badges, and challenges from the prototype backend; no real reputation or rewards service is connected.</p>
        <div className="inline-actions">
          <Button onClick={refresh}>Refresh</Button>
          {error ? <Badge variant="danger">{error}</Badge> : null}
        </div>
        {score ? <JsonViewer value={score} /> : null}
        {challenges ? <JsonViewer value={challenges} collapsed /> : null}
      </div>
    </div>
  );
}

export default GamificationConsole;
