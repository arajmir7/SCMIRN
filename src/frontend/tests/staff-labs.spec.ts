import { expect, test } from '@playwright/test';

function json(status: number, payload: unknown) {
  return { status, contentType: 'application/json', body: JSON.stringify(payload) };
}

test('Labs keeps demonstration workspaces visibly separate from public service routes', async ({ page }) => {
  page.on('pageerror', (error) => console.error(`Browser error: ${error.message}`));
  await page.route((url) => url.pathname.startsWith('/api/'), (route) => route.fulfill(json(200, { success: true, offices: [], items: [], issues: [] })));
  await page.goto('/labs');

  await expect(page.getByRole('heading', { name: 'SCMIRN Labs' })).toBeVisible();
  await expect(page.getByText(/demonstration only/i)).toBeVisible();
  await expect(page.getByRole('link', { name: /Issue Map/i })).toHaveAttribute('href', '/labs/heatmap');

  await page.goto('/heatmap');
  await expect(page).toHaveURL(/\/labs\/heatmap$/);
  await expect(page.getByText(/Do not enter personal, confidential, or real case information/i)).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Civic Issue Map · Demo Records' })).toBeVisible();
});

test('staff workspace fails closed when authentication is disabled and supports retry', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  let checks = 0;
  await page.route('**/api/v1/staff/auth/me', (route) => {
    checks += 1;
    return route.fulfill(json(503, { success: false, code: 'STAFF_AUTH_DISABLED', error: 'Staff authentication is disabled.' }));
  });
  await page.goto('/staff');

  await expect(page.getByRole('heading', { name: 'Staff workspace unavailable' })).toBeVisible();
  await expect(page.getByText(/disabled by deployment configuration/i)).toBeVisible();
  await expect(page.getByLabel('Tenant slug')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Open Problem Solver' })).toHaveCount(0);
  await expect(page.getByRole('contentinfo')).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Retry connection' }).click();
  await expect.poll(() => checks).toBe(2);
});

test('staff workspace exits loading when a proxy returns a successful non-JSON response', async ({ page }) => {
  await page.route('**/api/v1/staff/auth/me', (route) => route.fulfill({ status: 200, contentType: 'text/html', body: '<!doctype html><title>Proxy fallback</title>' }));
  await page.goto('/staff');
  await expect(page.getByRole('heading', { name: 'Staff service could not be reached' })).toBeVisible();
  await expect(page.getByRole('status').filter({ hasText: 'Checking staff session' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Retry connection' })).toBeVisible();
});

test('staff case work requires MFA and sends CSRF on case mutations', async ({ page }) => {
  let createdCase: Record<string, unknown> | null = null;
  let statusBody: Record<string, unknown> | null = null;
  let statusCsrf = '';
  await page.route('**/api/v1/staff/**', async (route) => {
    const request = route.request();
    const { pathname } = new URL(request.url());
    if (pathname === '/api/v1/staff/auth/me') return route.fulfill(json(401, { success: false, code: 'AUTHENTICATION_REQUIRED', error: 'Authentication required.' }));
    if (pathname === '/api/v1/staff/auth/login') return route.fulfill(json(200, { success: true, mfa_required: true, challenge: 'signed-one-time-challenge', expires_in: 300 }));
    if (pathname === '/api/v1/staff/auth/mfa') {
      expect(request.postDataJSON()).toEqual({ challenge: 'signed-one-time-challenge', code: '123456' });
      await page.context().addCookies([
        { name: 'scmirn_staff_session', value: 'session-test', url: 'http://127.0.0.1:3411', httpOnly: true, sameSite: 'Strict' },
        { name: 'scmirn_staff_csrf', value: 'csrf-test', url: 'http://127.0.0.1:3411', sameSite: 'Strict' },
      ]);
      return route.fulfill(json(200, {
        success: true, user: { id: 'staff-1', email: 'officer@example.test', display_name: 'Test Officer' },
        roles: ['CASE_OFFICER'], mfa_verified: true, session_expires_at: '2026-10-02T18:00:00Z',
      }));
    }
    if (pathname === '/api/v1/staff/cases' && request.method() === 'GET') return route.fulfill(json(200, { success: true, cases: [] }));
    if (pathname === '/api/v1/staff/cases' && request.method() === 'POST') {
      createdCase = request.postDataJSON() as Record<string, unknown>;
      return route.fulfill(json(201, { success: true, case: {
        id: 'case-1', case_ref: 'C-20261002-ABC123', case_type: 'ROADS', title: 'Road infrastructure case',
        status: 'OPEN', priority: 'HIGH', assigned_user_id: null, created_at: '2026-10-02T12:00:00Z', updated_at: '2026-10-02T12:00:00Z',
      } }));
    }
    if (pathname === '/api/v1/staff/cases/case-1/status') {
      statusBody = request.postDataJSON() as Record<string, unknown>;
      statusCsrf = request.headers()['x-csrf-token'] ?? '';
      return route.fulfill(json(200, { success: true, case: {
        id: 'case-1', case_ref: 'C-20261002-ABC123', case_type: 'ROADS', title: 'Road infrastructure case',
        status: 'UNDER_REVIEW', priority: 'HIGH', assigned_user_id: null, created_at: '2026-10-02T12:00:00Z', updated_at: '2026-10-02T12:10:00Z',
      } }));
    }
    return route.fulfill(json(404, { success: false, error: 'Not found.' }));
  });

  await page.goto('/staff');
  await page.getByLabel('Tenant slug').fill('district-demo');
  await page.getByLabel('Staff email').fill('officer@example.test');
  await page.getByLabel('Password').fill('test-password-allow-password-manager');
  await page.getByRole('button', { name: 'Continue to verification' }).click();
  await expect(page.getByLabel('Authenticator code')).toBeVisible();
  await page.getByLabel('Authenticator code').fill('123456');
  await page.getByRole('button', { name: 'Verify and open workspace' }).click();

  await expect(page.getByRole('heading', { name: 'Staff workspace' })).toBeVisible();
  await expect(page.getByText('Metadata only')).toBeVisible();
  await page.getByLabel('Case category').selectOption('ROADS');
  await page.getByLabel('Priority').selectOption('HIGH');
  await page.getByRole('button', { name: 'Create staff case' }).click();
  await expect(page.getByRole('heading', { name: 'C-20261002-ABC123' })).toBeVisible();
  expect(createdCase).toEqual({ case_type: 'ROADS', priority: 'HIGH' });

  await page.getByLabel('Status for C-20261002-ABC123').selectOption('UNDER_REVIEW');
  await page.getByRole('button', { name: 'Update C-20261002-ABC123' }).click();
  await expect(page.locator('article').getByText('UNDER REVIEW', { exact: true }).first()).toBeVisible();
  expect(statusBody).toEqual({ status: 'UNDER_REVIEW' });
  expect(statusCsrf).toBe('csrf-test');
  await expect(page.getByText(/no citizen identity, case narrative, attachment, evidence, agency submission, or source-review field/i)).toBeVisible();
});

test('auditor role receives read-only staff workspace', async ({ page }) => {
  await page.route('**/api/v1/staff/**', (route) => {
    const { pathname } = new URL(route.request().url());
    if (pathname === '/api/v1/staff/auth/me') return route.fulfill(json(200, {
      success: true, user: { id: 'auditor-1', email: 'audit@example.test', display_name: 'Test Auditor' },
      tenant: { id: 'tenant-1' }, roles: ['AUDITOR'], mfa_verified_at: '2026-10-02T12:00:00Z',
    }));
    if (pathname === '/api/v1/staff/cases') return route.fulfill(json(200, { success: true, cases: [] }));
    return route.fulfill(json(404, { success: false, error: 'Not found.' }));
  });
  await page.goto('/staff');
  await expect(page.getByRole('heading', { name: 'Staff workspace' })).toBeVisible();
  await expect(page.getByText('Read-only role')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Create staff case' })).toHaveCount(0);
});
