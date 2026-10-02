import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { apiGet, apiPost, type ApiResult } from '@/api/http';

type StaffRole = 'TENANT_ADMIN' | 'CASE_OFFICER' | 'SOURCE_REVIEWER' | 'AUDITOR';
type CaseStatus = 'OPEN' | 'UNDER_REVIEW' | 'ACTION_REQUIRED' | 'RESOLVED' | 'CLOSED';
type CaseType = 'ROADS' | 'WATER' | 'WASTE' | 'ELECTRICITY' | 'PUBLIC_SERVICE';
type Priority = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';

interface StaffUser { id: string; email: string; display_name: string }
interface StaffCase {
  id: string;
  case_ref: string;
  case_type: CaseType;
  title: string;
  status: CaseStatus;
  priority: Priority;
  assigned_user_id: string | null;
  created_at: string;
  updated_at: string;
}
interface ApiErrorBody { code?: string; error?: string }
interface StaffIdentityResponse {
  success: boolean;
  user: StaffUser;
  roles: StaffRole[];
}
interface StaffLoginResponse { success: boolean; mfa_required: boolean; challenge: string; expires_in: number }
interface StaffMfaResponse extends StaffIdentityResponse { mfa_verified: boolean; session_expires_at: string }
interface StaffCasesResponse { success: boolean; cases: StaffCase[] }
interface StaffCaseResponse { success: boolean; case: StaffCase }

type PageState = 'checking' | 'disabled' | 'connection_error' | 'sign_in' | 'mfa' | 'workspace';
const CASE_TYPES: Array<{ value: CaseType; label: string }> = [
  { value: 'ROADS', label: 'Roads' }, { value: 'WATER', label: 'Water' },
  { value: 'WASTE', label: 'Waste' }, { value: 'ELECTRICITY', label: 'Electricity' },
  { value: 'PUBLIC_SERVICE', label: 'Public service' },
];
const PRIORITIES: Priority[] = ['LOW', 'NORMAL', 'HIGH', 'URGENT'];
const NEXT_STATUSES: Record<CaseStatus, CaseStatus[]> = {
  OPEN: ['UNDER_REVIEW', 'CLOSED'],
  UNDER_REVIEW: ['ACTION_REQUIRED', 'RESOLVED', 'CLOSED'],
  ACTION_REQUIRED: ['UNDER_REVIEW', 'RESOLVED', 'CLOSED'],
  RESOLVED: ['CLOSED', 'UNDER_REVIEW'],
  CLOSED: [],
};
const CASE_ACCESS_ROLES = new Set<StaffRole>(['TENANT_ADMIN', 'CASE_OFFICER', 'AUDITOR']);
const STAFF_ROLES = new Set<StaffRole>(['TENANT_ADMIN', 'CASE_OFFICER', 'SOURCE_REVIEWER', 'AUDITOR']);
const CASE_TYPE_VALUES = new Set<CaseType>(['ROADS', 'WATER', 'WASTE', 'ELECTRICITY', 'PUBLIC_SERVICE']);
const CASE_STATUS_VALUES = new Set<CaseStatus>(['OPEN', 'UNDER_REVIEW', 'ACTION_REQUIRED', 'RESOLVED', 'CLOSED']);
const PRIORITY_VALUES = new Set<Priority>(['LOW', 'NORMAL', 'HIGH', 'URGENT']);

function isStaffUser(value: unknown): value is StaffUser {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Partial<StaffUser>;
  return typeof candidate.id === 'string' && typeof candidate.email === 'string' && typeof candidate.display_name === 'string';
}

function isStaffRoles(value: unknown): value is StaffRole[] {
  return Array.isArray(value) && value.every((role) => STAFF_ROLES.has(role as StaffRole));
}

function isStaffCase(value: unknown): value is StaffCase {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Partial<StaffCase>;
  return typeof candidate.id === 'string'
    && typeof candidate.case_ref === 'string'
    && typeof candidate.title === 'string'
    && typeof candidate.case_type === 'string' && CASE_TYPE_VALUES.has(candidate.case_type as CaseType)
    && typeof candidate.status === 'string' && CASE_STATUS_VALUES.has(candidate.status as CaseStatus)
    && typeof candidate.priority === 'string' && PRIORITY_VALUES.has(candidate.priority as Priority)
    && typeof candidate.created_at === 'string'
    && typeof candidate.updated_at === 'string';
}

function apiCode(result: ApiResult<unknown>): string | undefined {
  if (result.ok || !result.details || typeof result.details !== 'object') return undefined;
  return (result.details as ApiErrorBody).code;
}

function csrfToken(): string {
  const pair = document.cookie.split(';').map((part) => part.trim()).find((part) => part.startsWith('scmirn_staff_csrf='));
  return pair ? decodeURIComponent(pair.slice('scmirn_staff_csrf='.length)) : '';
}

async function staffMutation<T>(path: string, payload: unknown): Promise<ApiResult<T>> {
  const token = csrfToken();
  if (!token) return { ok: false, error: 'The staff session token is missing. Sign in again before changing a case.' };
  return apiPost<T>(path, payload, undefined, { 'X-CSRF-Token': token });
}

function errorMessage(result: ApiResult<unknown>, fallback: string): string {
  return result.ok ? fallback : (result.error || fallback);
}

function formatCode(value: string): string { return value.replace(/_/g, ' '); }

export function StaffWorkspacePage() {
  const [pageState, setPageState] = useState<PageState>('checking');
  const [user, setUser] = useState<StaffUser | null>(null);
  const [roles, setRoles] = useState<StaffRole[]>([]);
  const [cases, setCases] = useState<StaffCase[]>([]);
  const [casesLoading, setCasesLoading] = useState(false);
  const [casesError, setCasesError] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [refreshAuth, setRefreshAuth] = useState(0);
  const [tenantSlug, setTenantSlug] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [challenge, setChallenge] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [authSubmitting, setAuthSubmitting] = useState(false);
  const [caseType, setCaseType] = useState<CaseType>('ROADS');
  const [priority, setPriority] = useState<Priority>('NORMAL');
  const [creating, setCreating] = useState(false);
  const [statusValues, setStatusValues] = useState<Record<string, CaseStatus>>({});
  const [updatingCase, setUpdatingCase] = useState<string | null>(null);
  const [mutationError, setMutationError] = useState('');

  const canReadCases = useMemo(() => roles.some((role) => CASE_ACCESS_ROLES.has(role)), [roles]);
  const canManageCases = useMemo(() => roles.some((role) => role === 'CASE_OFFICER' || role === 'TENANT_ADMIN'), [roles]);

  const loadCases = useCallback(async (signal?: AbortSignal) => {
    setCasesLoading(true);
    setCasesError('');
    const result = await apiGet<StaffCasesResponse>('/api/v1/staff/cases', signal);
    setCasesLoading(false);
    if (signal?.aborted) return;
    if (!result.ok) {
      if (apiCode(result) === 'STAFF_AUTH_DISABLED') { setPageState('disabled'); return; }
      if (result.details && typeof result.details === 'object' && (result.details as ApiErrorBody).code === 'AUTHENTICATION_REQUIRED') {
        setUser(null);
        setRoles([]);
        setPageState('sign_in');
        setMessage('Your staff session has ended. Sign in again to continue.');
        return;
      }
      setCasesError(result.error || 'The case list could not be loaded.');
      return;
    }
    if (!result.data || !Array.isArray(result.data.cases) || !result.data.cases.every(isStaffCase)) {
      setCasesError('The staff service returned an invalid case-list response. No case data was displayed.');
      return;
    }
    setCases(result.data.cases);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setPageState('checking');
    setError('');
    setMessage('');
    void apiGet<StaffIdentityResponse>('/api/v1/staff/auth/me', controller.signal).then((result) => {
      if (controller.signal.aborted) return;
      if (!result.ok) {
        if (apiCode(result) === 'STAFF_AUTH_DISABLED') setPageState('disabled');
        else if (controller.signal.aborted) return;
        else if (result.details && typeof result.details === 'object' && (result.details as ApiErrorBody).code === 'AUTHENTICATION_REQUIRED') setPageState('sign_in');
        else if (result.error.startsWith('HTTP 401')) setPageState('sign_in');
        else { setError('We could not reach the staff service. Retry when your connection is available.'); setPageState('connection_error'); }
        return;
      }
      if (!result.data || !isStaffUser(result.data.user) || !isStaffRoles(result.data.roles)) {
        setError('The staff service returned an invalid session response. No workspace data was loaded.');
        setPageState('connection_error');
        return;
      }
      setUser(result.data.user);
      setRoles(result.data.roles ?? []);
      setPageState('workspace');
      if ((result.data.roles ?? []).some((role) => CASE_ACCESS_ROLES.has(role))) void loadCases(controller.signal);
    });
    return () => controller.abort();
  }, [loadCases, refreshAuth]);

  async function startSignIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setMessage('');
    if (!tenantSlug.trim() || !email.trim() || !password) { setError('Enter your tenant, work email, and password.'); return; }
    setAuthSubmitting(true);
    const result = await apiPost<StaffLoginResponse>('/api/v1/staff/auth/login', {
      tenant_slug: tenantSlug.trim(), email: email.trim(), password,
    });
    setAuthSubmitting(false);
    if (!result.ok) {
      if (apiCode(result) === 'STAFF_AUTH_DISABLED') { setPageState('disabled'); return; }
      setPassword('');
      setError('Sign in could not be completed. Check the details or retry later.');
      return;
    }
    if (!result.data?.mfa_required || !result.data.challenge) { setError('The staff service did not return a valid verification challenge. Retry sign in.'); return; }
    setPassword('');
    setChallenge(result.data.challenge);
    setPageState('mfa');
    setMessage('Enter the current code from your enrolled authenticator app. The challenge expires in five minutes.');
  }

  async function verifyMfa(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setAuthSubmitting(true);
    const result = await apiPost<StaffMfaResponse>('/api/v1/staff/auth/mfa', { challenge, code: mfaCode.trim() });
    setAuthSubmitting(false);
    if (!result.ok) {
      if (apiCode(result) === 'STAFF_AUTH_DISABLED') { setPageState('disabled'); return; }
      setMfaCode('');
      setError('The verification code was not accepted. Enter a current code or restart sign in.');
      return;
    }
    if (!result.data?.mfa_verified || !isStaffUser(result.data.user) || !isStaffRoles(result.data.roles)) {
      setError('The staff service did not confirm a verified session. Restart sign in.');
      return;
    }
    setUser(result.data.user);
    setRoles(result.data.roles);
    setChallenge('');
    setMfaCode('');
    setPageState('workspace');
    setMessage('Verified staff session opened.');
    if (result.data.roles.some((role) => CASE_ACCESS_ROLES.has(role))) await loadCases();
  }

  async function createCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canManageCases || creating) return;
    setCreating(true);
    setMutationError('');
    const result = await staffMutation<StaffCaseResponse>('/api/v1/staff/cases', { case_type: caseType, priority });
    setCreating(false);
    if (!result.ok) { setMutationError(errorMessage(result, 'The case could not be created.')); return; }
    if (!result.data || !isStaffCase(result.data.case)) { setMutationError('The staff service returned an invalid create response. Refresh the case list before continuing.'); return; }
    setCases((current) => [result.data.case, ...current.filter((item) => item.id !== result.data.case.id)]);
    setMessage(`Staff metadata record ${result.data.case.case_ref} created.`);
  }

  async function updateStatus(item: StaffCase) {
    if (!canManageCases || updatingCase) return;
    const next = statusValues[item.id] ?? item.status;
    if (next === item.status) return;
    setUpdatingCase(item.id);
    setMutationError('');
    const result = await staffMutation<StaffCaseResponse>(`/api/v1/staff/cases/${encodeURIComponent(item.id)}/status`, { status: next });
    setUpdatingCase(null);
    if (!result.ok) { setMutationError(errorMessage(result, 'The status was not changed.')); return; }
    if (!result.data || !isStaffCase(result.data.case)) { setMutationError('The staff service returned an invalid status response. Refresh the case list before continuing.'); return; }
    setCases((current) => current.map((caseItem) => caseItem.id === item.id ? result.data.case : caseItem));
    setStatusValues((current) => ({ ...current, [item.id]: result.data.case.status }));
    setMessage(`${item.case_ref} status updated to ${result.data.case.status}.`);
  }

  async function signOut() {
    setMutationError('');
    const result = await staffMutation<{ success: boolean }>('/api/v1/staff/auth/logout', {});
    if (!result.ok) {
      setMutationError(errorMessage(result, 'Sign out could not be confirmed. Retry or close this browser session.'));
      return;
    }
    setUser(null);
    setRoles([]);
    setCases([]);
    setPageState('sign_in');
    setMessage('You have signed out.');
  }

  function retryCases() { void loadCases(); }

  return (
    <section className="container py-5 mt-5" aria-labelledby="staff-title">
      <div className="d-flex flex-column flex-lg-row justify-content-between align-items-lg-start gap-3 mb-4">
        <div>
          <p className="text-uppercase small fw-semibold text-primary mb-2">Authenticated · tenant scoped · MFA required</p>
          <h1 id="staff-title" className="display-6 fw-bold mb-2">Staff workspace</h1>
          <p className="text-muted mb-0">Metadata-only staff case workflow. It is not connected to citizen submissions or government agency systems.</p>
        </div>
        {pageState === 'workspace' && user ? <div className="text-lg-end"><div className="fw-semibold">{user.display_name}</div><div className="small text-muted">{user.email}</div><div className="d-flex flex-wrap gap-2 mt-2" aria-label="Staff roles">{roles.map((role) => <span className="badge text-bg-light border" key={role}>{formatCode(role)}</span>)}</div></div> : null}
      </div>

      {message ? <div className="alert alert-info" role="status">{message}</div> : null}
      {error && pageState !== 'connection_error' ? <div className="alert alert-danger" role="alert">{error}</div> : null}
      {mutationError ? <div className="alert alert-danger" role="alert">{mutationError}</div> : null}

      {pageState === 'checking' ? <div className="card shadow-sm"><div className="card-body" role="status"><span className="spinner-border spinner-border-sm me-2" aria-hidden="true" />Checking staff session…</div></div> : null}

      {pageState === 'disabled' ? <div className="card shadow-sm border-warning"><div className="card-body p-4"><h2 className="h4" id="staff-unavailable-title">Staff workspace unavailable</h2><p className="mb-3">Staff authentication is disabled by deployment configuration. No sign-in or case action is available in this environment.</p><button className="btn btn-outline-dark" type="button" onClick={() => setRefreshAuth((value) => value + 1)}>Retry connection</button></div></div> : null}

      {pageState === 'connection_error' ? <div className="card shadow-sm"><div className="card-body p-4"><h2 className="h4">Staff service could not be reached</h2><p className="text-muted">{error || 'No staff session or case data was loaded. Check the connection, then retry.'}</p><button className="btn btn-outline-dark" type="button" onClick={() => setRefreshAuth((value) => value + 1)}>Retry connection</button></div></div> : null}

      {pageState === 'sign_in' ? <div className="card shadow-sm" style={{ maxWidth: 560 }}><div className="card-body p-4">
        <h2 className="h4">Staff sign in</h2>
        <p className="text-muted">Use an account provisioned by your organization. Credentials and MFA are verified by the staff service.</p>
        <form onSubmit={startSignIn} noValidate>
          <div className="mb-3"><label className="form-label" htmlFor="staff-tenant">Tenant slug</label><input className="form-control" id="staff-tenant" value={tenantSlug} onChange={(event) => setTenantSlug(event.target.value)} autoComplete="organization" maxLength={80} required /></div>
          <div className="mb-3"><label className="form-label" htmlFor="staff-email">Staff email</label><input className="form-control" id="staff-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="username" maxLength={254} required /></div>
          <div className="mb-3"><label className="form-label" htmlFor="staff-password">Password</label><input className="form-control" id="staff-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" maxLength={256} required /></div>
          <button className="btn btn-primary" type="submit" disabled={authSubmitting}>{authSubmitting ? <><span className="spinner-border spinner-border-sm me-2" aria-hidden="true" />Checking…</> : 'Continue to verification'}</button>
        </form>
      </div></div> : null}

      {pageState === 'mfa' ? <div className="card shadow-sm" style={{ maxWidth: 560 }}><div className="card-body p-4">
        <h2 className="h4">Verify your sign in</h2>
        <p className="text-muted">Enter the six-digit code from your enrolled authenticator app. The code is not stored by this page.</p>
        <form onSubmit={verifyMfa} noValidate>
          <div className="mb-3"><label className="form-label" htmlFor="staff-mfa-code">Authenticator code</label><input className="form-control" id="staff-mfa-code" type="text" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" minLength={6} maxLength={6} value={mfaCode} onChange={(event) => setMfaCode(event.target.value.replace(/\D/g, '').slice(0, 6))} aria-describedby="mfa-hint" required /><div id="mfa-hint" className="form-text">Use the current code. Paste is allowed.</div></div>
          <div className="d-flex flex-wrap gap-2"><button className="btn btn-primary" type="submit" disabled={authSubmitting || mfaCode.length !== 6}>{authSubmitting ? 'Verifying…' : 'Verify and open workspace'}</button><button className="btn btn-outline-secondary" type="button" onClick={() => { setChallenge(''); setMfaCode(''); setPageState('sign_in'); setMessage('Restart sign in to request a new verification challenge.'); setError(''); }}>Restart sign in</button></div>
        </form>
      </div></div> : null}

      {pageState === 'workspace' ? <div className="row g-4">
        {!canReadCases ? <div className="col-12"><div className="alert alert-warning mb-0" role="status"><h2 className="h5">No staff case access</h2><p className="mb-0">Your current role has no case endpoint in this workspace. Source review and administration screens are not available in this release.</p></div></div> : <>
          <div className="col-12"><div className="alert alert-secondary mb-0"><strong>Metadata only.</strong> The API accepts a fixed category and priority. It has no citizen identity, case narrative, attachment, evidence, agency submission, or source-review field. Do not put personal information into this workflow.</div></div>
          {!canManageCases && roles.includes('AUDITOR') ? <div className="col-12"><div className="alert alert-info mb-0" role="status"><strong>Read-only role.</strong> You can review only the case records authorized for your tenant. Case creation and status changes are not available to auditors.</div></div> : null}
          {canManageCases ? <div className="col-xl-4"><section className="card shadow-sm h-100" aria-labelledby="create-case-title"><div className="card-body p-4">
            <h2 id="create-case-title" className="h5 fw-bold">Create a staff case</h2><p className="small text-muted">Creates a tenant-scoped metadata record under your staff identity.</p>
            <form onSubmit={createCase} noValidate>
              <div className="mb-3"><label htmlFor="staff-case-type" className="form-label">Case category</label><select id="staff-case-type" className="form-select" value={caseType} onChange={(event) => setCaseType(event.target.value as CaseType)}>{CASE_TYPES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></div>
              <div className="mb-3"><label htmlFor="staff-case-priority" className="form-label">Priority</label><select id="staff-case-priority" className="form-select" value={priority} onChange={(event) => setPriority(event.target.value as Priority)}>{PRIORITIES.map((item) => <option key={item} value={item}>{item}</option>)}</select></div>
              <button className="btn btn-primary" type="submit" disabled={creating}>{creating ? 'Creating…' : 'Create staff case'}</button>
            </form>
          </div></section></div> : null}
          <div className={canManageCases ? 'col-xl-8' : 'col-12'}><section className="card shadow-sm" aria-labelledby="case-list-title"><div className="card-body p-4">
            <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3"><div><h2 id="case-list-title" className="h5 fw-bold mb-1">Staff case records</h2><p className="small text-muted mb-0">Server authorization applies tenant, role, creator, and assignment scope.</p></div><div className="d-flex gap-2 align-items-center"><span className="badge text-bg-light border">{cases.length} loaded</span><button className="btn btn-sm btn-outline-secondary" type="button" onClick={retryCases} disabled={casesLoading}>{casesLoading ? 'Refreshing…' : 'Refresh cases'}</button></div></div>
            {casesError ? <div className="alert alert-danger" role="alert">{casesError} <button className="btn btn-sm btn-outline-dark ms-2" type="button" onClick={retryCases}>Retry</button></div> : null}
            {casesLoading && cases.length === 0 ? <p className="text-muted" role="status"><span className="spinner-border spinner-border-sm me-2" aria-hidden="true" />Loading authorized case records…</p> : null}
            {!casesLoading && !casesError && cases.length === 0 ? <p className="text-muted mb-0">No staff case records are visible to this account.</p> : null}
            <div className="d-grid gap-3">{cases.map((item) => {
              const options = NEXT_STATUSES[item.status];
              const selectedStatus = statusValues[item.id] ?? item.status;
              return <article className="border rounded-3 p-3" key={item.id}>
                <div className="d-flex flex-wrap justify-content-between gap-2"><div><h3 className="h6 fw-bold mb-1">{item.case_ref}</h3><div>{item.title}</div><div className="small text-muted">{formatCode(item.case_type)} · {item.priority} priority</div></div><span className="badge text-bg-light border align-self-start">{formatCode(item.status)}</span></div>
                <div className="small text-muted mt-2">Created {new Date(item.created_at).toLocaleString()}</div>
                {canManageCases && options.length ? <div className="d-flex flex-column flex-sm-row align-items-sm-end gap-2 mt-3"><div className="flex-grow-1"><label className="form-label small mb-1" htmlFor={`case-status-${item.id}`}>Status for {item.case_ref}</label><select id={`case-status-${item.id}`} className="form-select form-select-sm" value={selectedStatus} onChange={(event) => setStatusValues((current) => ({ ...current, [item.id]: event.target.value as CaseStatus }))}><option value={item.status}>{formatCode(item.status)}</option>{options.map((status) => <option key={status} value={status}>{formatCode(status)}</option>)}</select></div><button className="btn btn-sm btn-outline-primary" type="button" disabled={updatingCase === item.id || selectedStatus === item.status} onClick={() => void updateStatus(item)}>{updatingCase === item.id ? 'Updating…' : `Update ${item.case_ref}`}</button></div> : null}
              </article>;
            })}</div>
          </div></section></div>
        </>}
        <div className="col-12"><button className="btn btn-link px-0" type="button" onClick={() => void signOut()}>Sign out</button></div>
      </div> : null}
    </section>
  );
}

export default StaffWorkspacePage;
