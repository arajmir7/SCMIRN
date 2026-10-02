export interface IssueApiRecord {
  id: number | string;
  public_id?: string;
  title: string;
  description: string;
  category: string;
  location?: { lat?: number | null; lng?: number | null } | null;
  lat?: number | null;
  lon?: number | null;
  priority_tier?: string;
  status?: string;
  fund_target?: number;
  fund_collected?: number;
  media_files?: Array<string | { url?: string; type?: string }> | string;
  created_at?: string | null;
}

export interface CivicIssue {
  id: string;
  numericId: number | null;
  publicId: string;
  title: string;
  description: string;
  category: string;
  lat: number | null;
  lng: number | null;
  priority: 'critical' | 'high' | 'medium' | 'low';
  status: string;
  fundTarget: number;
  fundCollected: number;
  photos: string[];
  createdAt: string | null;
}

function issuePhotos(value: IssueApiRecord['media_files']): string[] {
  let files: Array<string | { url?: string }> = [];
  if (Array.isArray(value)) files = value;
  else if (typeof value === 'string') {
    try {
      const parsed: unknown = JSON.parse(value);
      if (Array.isArray(parsed)) files = parsed;
    } catch {
      files = [];
    }
  }
  return files
    .map((file) => (typeof file === 'string' ? file : file?.url ?? ''))
    .filter(Boolean);
}

export function normalizeIssue(issue: IssueApiRecord): CivicIssue {
  const numericId = Number(issue.id);
  const latValue = issue.location?.lat ?? issue.lat;
  const lngValue = issue.location?.lng ?? issue.lon;
  const lat = latValue == null ? null : Number(latValue);
  const lng = lngValue == null ? null : Number(lngValue);
  const priority = String(issue.priority_tier ?? 'medium').toLowerCase();

  return {
    id: String(issue.id),
    numericId: Number.isFinite(numericId) ? numericId : null,
    publicId: issue.public_id ?? String(issue.id),
    title: issue.title ?? '',
    description: issue.description ?? '',
    category: issue.category ?? 'other',
    lat: lat != null && Number.isFinite(lat) ? lat : null,
    lng: lng != null && Number.isFinite(lng) ? lng : null,
    priority: priority === 'critical' || priority === 'high' || priority === 'low' ? priority : 'medium',
    status: issue.status ?? 'reported',
    fundTarget: Number(issue.fund_target ?? 0),
    fundCollected: Number(issue.fund_collected ?? 0),
    photos: issuePhotos(issue.media_files),
    createdAt: issue.created_at ?? null,
  };
}
