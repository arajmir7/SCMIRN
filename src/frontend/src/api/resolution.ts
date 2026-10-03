import { apiGet, apiPost, type ApiResult } from '@/api/http';

export type ResolutionOutcome =
  | 'OFFICIAL_HANDOFF_ONLY'
  | 'ROUTE_UNCERTAIN'
  | 'JURISDICTION_AMBIGUOUS'
  | 'URGENT_HUMAN_HELP_REQUIRED';

export interface ResolutionSource {
  source_id: string;
  version: number;
  source_type: string;
  title: string;
  authority: string;
  canonical_url: string;
  document_hash: string | null;
  verification_status: string;
  verified_at: string | null;
  reviewed_on?: string | null;
  verified_on?: string | null;
}

export interface ResolutionResult {
  decision_id: string;
  created_at: string;
  retention_until: string;
  outcome: ResolutionOutcome;
  issue_type: string;
  urgency: 'LOW' | 'NORMAL' | 'HIGH' | 'CRITICAL' | 'UNASSESSED';
  urgency_signal: 'NONE_DETECTED' | 'POSSIBLE_IMMEDIATE_DANGER';
  urgent_human_help_required: boolean;
  explanation: string;
  route_rule_version: string;
  service_registry_version: string;
  model_version: string | null;
  authority: { authority_id: string; name: string; level: string } | null;
  service: {
    service_id: string;
    version: number;
    name: string;
    status: string;
    integration_mode: string;
    official_url: string;
    application_channel: string | null;
    grievance_channel: string | null;
    required_evidence: unknown[];
    recommended_evidence: unknown[];
    optional_evidence: unknown[];
  } | null;
  official_handoff: { url: string | null; phone: string | null; message: string } | null;
  submission_status: 'NOT_SUBMITTED';
  official_reference: null;
  sources: ResolutionSource[];
}

export interface ServiceSummary {
  service_id: string;
  version: number;
  canonical_name: string;
  description: string | null;
  authority: string | null;
  authority_level: string;
  jurisdiction: Record<string, unknown>;
  eligibility: string | null;
  exclusions: string[];
  issue_types: string[];
  required_evidence: unknown[];
  recommended_evidence: unknown[];
  optional_evidence: unknown[];
  application_channel: string | null;
  grievance_channel: string | null;
  official_url: string;
  integration_mode: string;
  identity_assurance_required: string;
  official_sla: Record<string, unknown> | null;
  source_ids: string[];
  sources: ResolutionSource[];
  effective_from: string | null;
  effective_until: string | null;
  last_verified: string | null;
  last_verified_on: string | null;
  status: string;
}

export interface EvidenceCheck {
  service_id: string;
  service_version?: number;
  status: 'READY' | 'INCOMPLETE' | 'UNCONFIGURED' | 'SOURCE_UNVERIFIED' | 'SERVICE_UNAVAILABLE';
  requirements: Array<Record<string, unknown>>;
  missing_required: string[];
}

export const resolutionApi = {
  triage(payload: { description: string; state?: string; district?: string; consent_to_process: true }, idempotencyKey: string): Promise<ApiResult<ResolutionResult>> {
    return apiPost<ResolutionResult>('/api/v1/triage', payload, undefined, { 'Idempotency-Key': idempotencyKey });
  },
  services(signal?: AbortSignal): Promise<ApiResult<{ items: ServiceSummary[]; count: number }>> {
    return apiGet('/api/v1/services', signal);
  },
  evidence(serviceId: string, providedEvidenceIds: string[] = []): Promise<ApiResult<EvidenceCheck>> {
    return apiPost('/api/v1/evidence/check', { service_id: serviceId, provided_evidence_ids: providedEvidenceIds });
  },
};

const sha256Pattern = /^[0-9a-f]{64}$/;

export function canRenderOfficialHandoff(result: ResolutionResult): boolean {
  if (result.outcome !== 'OFFICIAL_HANDOFF_ONLY' || !result.official_handoff?.url) return false;
  if (!isHttpsUrl(result.official_handoff.url)) return false;
  const targetHost = new URL(result.official_handoff.url).hostname.toLowerCase();
  const sourcesAreVerified = result.sources.length > 0 && result.sources.every((source) => (
    source.verification_status === 'VERIFIED'
    && Boolean(source.verified_at || source.verified_on)
    && typeof source.document_hash === 'string'
    && sha256Pattern.test(source.document_hash)
    && isHttpsUrl(source.canonical_url)
  ));
  if (!sourcesAreVerified) return false;
  const sourceHosts = new Set(result.sources.map((source) => new URL(source.canonical_url).hostname.toLowerCase()));
  if (!sourceHosts.has(targetHost)) return false;
  return result.official_handoff.phone == null || /^tel:\+?[0-9][0-9 ().-]{2,30}$/.test(result.official_handoff.phone);
}

function isHttpsUrl(value: string): boolean {
  try {
    const parsed = new URL(value);
    return parsed.protocol === 'https:'
      && parsed.username === ''
      && parsed.password === ''
      && (parsed.port === '' || parsed.port === '443');
  } catch {
    return false;
  }
}
