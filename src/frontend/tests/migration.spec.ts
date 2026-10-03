import { expect, test, type Page } from '@playwright/test';

const issueRecords = [
  {
    id: 1,
    public_id: 'issue-critical',
    title: 'Critical pothole near school',
    description: 'Deep pothole reported by residents.',
    category: 'road',
    location: { lat: 28.6139, lng: 77.209 },
    priority_tier: 'critical',
    status: 'reported',
    fund_target: 50000,
    fund_collected: 12500,
    media_files: [],
  },
  {
    id: 2,
    public_id: 'issue-high',
    title: 'Water leak on Civic Road',
    description: 'A water leak is affecting the footpath.',
    category: 'water',
    location: { lat: 28.62, lng: 77.215 },
    priority_tier: 'high',
    status: 'in_progress',
    fund_target: 20000,
    fund_collected: 5000,
    media_files: [],
  },
];

async function mockApi(page: Page) {
  await page.route((url) => url.pathname.startsWith('/api/'), async (route) => {
    const { pathname } = new URL(route.request().url());
    let payload: Record<string, unknown> = { success: false, error: 'No test response configured.' };

    if (pathname === '/api/issues') payload = { success: true, count: issueRecords.length, issues: issueRecords };
    if (pathname === '/api/v1/services') payload = { items: [], count: 0 };
    if (pathname === '/api/v1/triage' || pathname === '/api/v1/jurisdiction/resolve') payload = {
      decision_id: 'decision-synthetic-test',
      created_at: '2026-10-01T00:00:00Z',
      retention_until: '2026-10-31T00:00:00Z',
      outcome: 'ROUTE_UNCERTAIN',
      issue_type: 'OTHER',
      urgency: 'NORMAL',
      urgent_human_help_required: false,
      explanation: 'No route can be recommended until a current official source is verified.',
      route_rule_version: 'rules-test-v1',
      service_registry_version: 'registry-test-v1',
      model_version: null,
      authority: null,
      service: null,
      official_handoff: null,
      submission_status: 'NOT_SUBMITTED',
      official_reference: null,
      sources: [],
    };
    if (pathname === '/api/documents/generate') payload = { success: true, content: 'Draft generated for browser verification.' };
    if (pathname === '/api/tracker/summary') payload = {
      success: true,
      kpis: { open_cases: 2, due_escalations: 1, avg_eta_days: 8, avg_funded_progress: 25 },
      items: [{ public_id: 'issue-critical', title: issueRecords[0].title, status: 'reported', priority_tier: 'critical', category: 'road', eta_days: 8, escalation_ready: true }],
    };
    if (pathname === '/api/analytics/summary') payload = {
      success: true,
      summary: { total_reports: 2, critical_share: 50, predicted_sla: '7-12 days', top_bottleneck: 'road' },
      category_distribution: { road: 1, water: 1 },
      status_distribution: { reported: 1, in_progress: 1 },
    };
    if (pathname === '/api/offices') payload = {
      success: true,
      offices: [{ id: 1, name: 'District Service Center', department: 'Public Services', address: '12 Civic Road', phone: '011-555-0100', timings: 'Mon-Fri 9:00-17:00', services: 'Certificates, applications', rating: 4.5 }],
    };

    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(payload) });
  });
}

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

test('homepage, sticky navigation, feature anchor, and consented source route check work', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/');

  await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible();
  await expect(page.getByRole('heading', { name: /What happened\? Find the next step\./ })).toBeVisible();
  await expect(page.locator('#home .floating-card').filter({ hasText: 'Consent' })).toBeVisible();
  await page.getByRole('button', { name: 'Explore Features' }).click();
  await expect(page.getByRole('heading', { name: 'Available capabilities' })).toBeInViewport();

  await page.getByLabel('What happened?').fill('How do I report a blocked drain?');
  await page.locator('#home').getByRole('button', { name: 'Find the next step' }).click();
  const chat = page.getByRole('region', { name: 'SCMIRN source-linked problem solver' });
  await expect(chat).toBeVisible();
  await expect(chat.getByLabel('Problem description')).toHaveValue('How do I report a blocked drain?');
  const routeButton = chat.getByRole('button', { name: 'Find the correct action' });
  await expect(routeButton).toBeDisabled();
  await expect(routeButton).toBeDisabled();
  await chat.getByLabel(/I agree to process this description/).check();
  await routeButton.click();
  await expect(chat.getByText('Route result · ROUTE UNCERTAIN')).toBeVisible();
  await expect(chat.getByText('Not submitted')).toBeVisible();
  await chat.getByRole('button', { name: 'Close problem solver' }).click();
  await expect(chat).toBeHidden();
  expect(errors).toEqual([]);
});

test('rights route handoff and consented issue demo record work', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Describe an issue to check for a verified route').fill('Police refused to register a theft FIR');
  await page.getByRole('button', { name: 'Continue to Route Check' }).click();
  const assistant = page.getByRole('region', { name: 'SCMIRN source-linked problem solver' });
  await expect(assistant.getByLabel('Problem description')).toHaveValue('Police refused to register a theft FIR');
  await assistant.getByLabel(/I agree to process this description/).check();
  await assistant.getByRole('button', { name: 'Find the correct action' }).click();
  await expect(assistant.getByText('Route result · ROUTE UNCERTAIN')).toBeVisible();
  await assistant.getByRole('button', { name: 'Close problem solver' }).click();

  let multipartRequest = false;
  await page.route('**/api/report-issue', async (route) => {
    const request = route.request();
    multipartRequest = request.headers()['content-type']?.includes('multipart/form-data') === true
      && request.postData()?.includes('A broken streetlight') === true;
    await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ success: true }) });
  });

  await page.getByRole('link', { name: 'Open Labs' }).click();
  await page.getByRole('button', { name: 'Create a sample record' }).click();
  const dialog = page.getByRole('dialog', { name: 'Create SCMIRN Demo Record' });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('button', { name: 'Close' })).toBeFocused();
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/2ioAAAAASUVORK5CYII=', 'base64');
  await dialog.getByLabel('Issue title').fill('A broken streetlight');
  await dialog.getByLabel('Issue description').fill('The light has been out for two nights beside the crossing.');
  await dialog.locator('#report-photos').setInputFiles({ name: 'light.png', mimeType: 'image/png', buffer: png });
  await expect(dialog.getByRole('img', { name: 'Issue photo 1' })).toBeVisible();
  await expect(dialog.getByRole('button', { name: 'Save SCMIRN Demo Record' })).toBeDisabled();
  await dialog.getByLabel(/I understand this saves a prototype record/).check();
  await dialog.getByRole('button', { name: 'Close' }).focus();
  await page.keyboard.press('Shift+Tab');
  await expect(dialog.getByRole('button', { name: 'Save SCMIRN Demo Record' })).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(dialog.getByRole('button', { name: 'Close' })).toBeFocused();
  await dialog.getByRole('button', { name: 'Save SCMIRN Demo Record' }).click();
  await expect(dialog.getByText(/SCMIRN demo record saved/)).toBeVisible();
  expect(multipartRequest).toBe(true);
  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
  await expect(page.getByRole('button', { name: 'Create a sample record' })).toBeFocused();
});

test('document generator exposes all types and reports its generated result', async ({ page }) => {
  await page.goto('/documents');
  await expect(page.locator('article')).toHaveCount(6);
  await page.getByRole('button', { name: 'Generate' }).first().click();
  const dialog = page.getByRole('dialog', { name: 'Generate Unreviewed Draft' });
  const typeSelect = dialog.getByLabel('Application Type');
  await expect(typeSelect.locator('option')).toHaveCount(8);
  for (const type of ['rti', 'fir', 'consumer', 'electricity', 'rent', 'scholarship', 'pension', 'cybercrime']) {
    await typeSelect.selectOption(type);
  }
  await dialog.getByLabel('Applicant Name').fill('Asha Citizen');
  await dialog.getByLabel('Contact Number').fill('9999999999');
  await dialog.getByLabel('Address').fill('10 Civic Lane, Delhi');
  await dialog.getByLabel('Issue / Request Summary').fill('Please provide the requested public information.');
  await dialog.getByLabel('I have entered synthetic test information only.').check();
  await dialog.getByRole('button', { name: 'Generate Draft' }).click();
  await expect(dialog.getByLabel('Unreviewed Draft Output')).toHaveValue('Draft generated for browser verification.');
});

test('sample office data, local tracker, and demo analytics refresh their summaries', async ({ page }) => {
  let trackerRequests = 0;
  let analyticsRequests = 0;
  page.on('request', (request) => {
    const url = new URL(request.url());
    if (url.pathname === '/api/tracker/summary') trackerRequests += 1;
    if (url.pathname === '/api/analytics/summary') analyticsRequests += 1;
  });

  await page.goto('/offices');
  await expect(page.getByRole('heading', { name: 'District Service Center' })).toBeVisible();
  await expect(page.getByText('12 Civic Road')).toBeVisible();

  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'SCMIRN Record Tracker' })).toBeVisible();
  await expect(page.getByText('Critical pothole near school')).toBeVisible();
  const initialTrackerRequests = trackerRequests;
  await page.getByRole('button', { name: 'Refresh', exact: true }).click();
  await expect.poll(() => trackerRequests).toBe(initialTrackerRequests + 1);

  await page.goto('/analytics');
  await expect(page.getByRole('heading', { name: 'Category Distribution' })).toBeVisible();
  await expect(page.locator('canvas')).toHaveCount(2);
  const initialAnalyticsRequests = analyticsRequests;
  await page.getByRole('button', { name: 'Refresh Insights' }).click();
  await expect.poll(() => analyticsRequests).toBe(initialAnalyticsRequests + 1);
});

test('source route and document API errors are shown to users', async ({ page }) => {
  await page.route((url) => url.pathname === '/api/v1/triage', async (route) => {
    await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: { message: 'Route service unavailable.' } }) });
  });
  await page.goto('/');
  await page.getByLabel('Describe an issue to check for a verified route').fill('Synthetic test issue without personal details.');
  await page.getByRole('button', { name: 'Continue to Route Check' }).click();
  const assistant = page.getByRole('region', { name: 'SCMIRN source-linked problem solver' });
  await assistant.getByLabel(/I agree to process this description/).check();
  await assistant.getByRole('button', { name: 'Find the correct action' }).click();
  await expect(assistant.getByRole('alert')).toContainText('Route service unavailable.');

  await page.route((url) => url.pathname === '/api/documents/generate', async (route) => {
    await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ success: false, error: 'Document service unavailable.' }) });
  });
  await page.goto('/documents');
  await page.getByRole('button', { name: 'Generate' }).first().click();
  const dialog = page.getByRole('dialog', { name: 'Generate Unreviewed Draft' });
  await dialog.getByLabel('Applicant Name').fill('Asha Citizen');
  await dialog.getByLabel('Contact Number').fill('9999999999');
  await dialog.getByLabel('Address').fill('10 Civic Lane, Delhi');
  await dialog.getByLabel('Issue / Request Summary').fill('Please repair the public drain.');
  await dialog.getByLabel('I have entered synthetic test information only.').check();
  await dialog.getByRole('button', { name: 'Generate Draft' }).click();
  await expect(dialog.getByRole('alert')).toContainText('Document service unavailable.');
});

test('service directory shows dated source provenance and only safe handoff links', async ({ page }) => {
  const source = {
    source_id: 'nch-portal-about',
    version: 1,
    source_type: 'OFFICIAL_FAQ',
    title: 'National Consumer Helpline scope and grievance process',
    authority: 'Department of Consumer Affairs',
    canonical_url: 'https://consumerhelpline.gov.in/public/index.php/about',
    document_hash: 'a'.repeat(64),
    verification_status: 'VERIFIED',
    verified_at: null,
    reviewed_on: '2026-10-02',
    verified_on: '2026-10-02',
  };
  const service = {
    service_id: 'national-consumer-helpline',
    version: 1,
    canonical_name: 'National Consumer Helpline consumer grievance handoff',
    description: 'Pre-litigation consumer grievance channel; no remedy is guaranteed.',
    authority: 'Department of Consumer Affairs',
    authority_level: 'CENTRAL',
    jurisdiction: { country: 'IN' },
    eligibility: 'Consumer issues can be lodged through the official NCH channels.',
    exclusions: ['Not a court filing.'],
    issue_types: ['CONSUMER_GRIEVANCE'],
    required_evidence: [],
    recommended_evidence: [],
    optional_evidence: [],
    application_channel: 'https://consumerhelpline.gov.in/',
    grievance_channel: 'tel:1915',
    official_url: 'https://consumerhelpline.gov.in/public/index.php/about',
    integration_mode: 'OFFICIAL_HANDOFF_ONLY',
    identity_assurance_required: 'A0',
    official_sla: null,
    source_ids: ['nch-portal-about'],
    sources: [source],
    effective_from: null,
    effective_until: null,
    last_verified: null,
    last_verified_on: '2026-10-02',
    status: 'ACTIVE',
  };
  const unsafe = {
    ...service,
    service_id: 'unsafe-test-service',
    canonical_name: 'Unsafe test service',
    description: 'A synthetic record with a destination host that does not match its source.',
    eligibility: null,
    issue_types: [],
    application_channel: 'https://spoof.example.test/submit',
  };
  let directoryRequests = 0;
  await page.route('**/api/v1/services', async (route) => {
    directoryRequests += 1;
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [service, unsafe], count: 2 }) });
  });
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));

  await page.goto('/services');
  await expect(page).toHaveTitle('Service Directory | SCMIRN');
  await expect(page.getByRole('heading', { name: 'Browse service handoffs' })).toBeVisible();
  await expect(page.getByText('internal review date 2026-10-02')).toHaveCount(2);
  await expect(page.getByRole('link', { name: 'Open official service channel' })).toHaveAttribute('href', 'https://consumerhelpline.gov.in/');
  await expect(page.getByText('No destination passes this record’s source, hash, status, date, and host checks.')).toBeVisible();
  await page.getByText('View source URL and content hash').first().click();
  await expect(page.getByText('a'.repeat(64)).first()).toBeVisible();

  await page.getByLabel('Search services').fill('consumer grievance');
  await expect(page.getByText('Showing 1 of 2 catalogue entries.')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Unsafe test service' })).toHaveCount(0);
  expect(directoryRequests).toBe(1);
  expect(errors).toEqual([]);
});

test('service directory reports unavailable catalogue and supports retry', async ({ page }) => {
  let requests = 0;
  await page.route('**/api/v1/services', async (route) => {
    requests += 1;
    if (requests === 1) {
      await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: { message: 'Service unavailable.' } }) });
      return;
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], count: 0 }) });
  });
  await page.goto('/services');
  await expect(page.getByRole('alert')).toContainText('The service catalogue could not be loaded.');
  await page.getByRole('button', { name: 'Refresh directory' }).click();
  await expect(page.getByRole('heading', { name: 'No handoffs are currently listed' })).toBeVisible();
  expect(requests).toBe(2);
});

test('heatmap markers filter and search, and all migrated routes survive direct navigation', async ({ page }) => {
  let donationPosted = false;
  await page.route('**/api/donate', async (route) => {
    donationPosted = route.request().postDataJSON()?.amount === 750;
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) });
  });
  await page.goto('/heatmap');
  await expect(page.getByRole('heading', { name: 'Civic Issue Map · Demo Records' })).toBeVisible();
  await expect(page.locator('.leaflet-marker-icon[title]')).toHaveCount(2);
  const criticalMarker = page.locator('.leaflet-marker-icon[title="Critical pothole near school"]');
  await criticalMarker.hover();
  const popup = page.locator('.leaflet-popup-content').filter({ hasText: 'Critical pothole near school' });
  await expect(popup).toBeVisible();
  await expect(popup.getByText('no funding is collected here')).toBeVisible();
  await expect(popup.getByRole('button', { name: 'Fund', exact: true })).toHaveCount(0);
  expect(donationPosted).toBe(false);
  await page.getByRole('button', { name: 'Critical', exact: true }).click();
  await expect(page.locator('.leaflet-marker-icon[title]')).toHaveCount(1);
  await page.getByRole('button', { name: 'All', exact: true }).click();
  await page.getByLabel('Search area, landmark, or issue').fill('pothole');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page.getByText('Found 1 local result(s).')).toBeVisible();

  let externalGeocodeCalls = 0;
  let externalQuery = '';
  await page.route('https://nominatim.openstreetmap.org/search**', async (route) => {
    externalGeocodeCalls += 1;
    externalQuery = new URL(route.request().url()).searchParams.get('q') ?? '';
    await route.fulfill({ status: 200, contentType: 'application/json', body: '[]' });
  });
  await page.getByLabel('Search area, landmark, or issue').fill('Synthetic place name');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page.getByText(/Opt in below to search OpenStreetMap/)).toBeVisible();
  expect(externalGeocodeCalls).toBe(0);
  await page.getByLabel('Allow unmatched place-name searches to OpenStreetMap Nominatim').check();
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect.poll(() => externalGeocodeCalls).toBe(1);
  expect(externalQuery).toBe('Synthetic place name');

  await page.context().grantPermissions(['geolocation']);
  await page.context().setGeolocation({ latitude: 28.6, longitude: 77.2, accuracy: 25 });
  await page.getByRole('button', { name: 'Use my location' }).click();
  await expect(page.getByText(/Location shown on this map/)).toBeVisible();

  for (const [path, heading] of [
    ['/offices', 'Office Directory Demo'],
    ['/tracker', 'SCMIRN Record Tracker'],
    ['/analytics', 'Demo Record Summary'],
    ['/documents', 'Unreviewed Draft Templates'],
    ['/platform', 'Prototype Workspaces'],
  ]) {
    await page.goto(path);
    await expect(page.getByRole('heading', { name: heading })).toBeVisible();
  }
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Prototype Workspaces' })).toBeVisible();
});

test('every advanced workspace opens and exposes its interactive controls', async ({ page }) => {
  await page.goto('/platform');
  const workspaces = [
    ['Civic Map · Demo Records', 'Search area, landmark, or issue'],
    ['IoT Predictive Maintenance · Simulation', 'Ingest Sensor Payload'],
    ['Blockchain Registry · Simulation', 'Register Issue Hash'],
    ['Legal Co-Pilot · Experimental', 'Classify Intent'],
    ['Civic Score & Challenges · Demo', 'Refresh'],
    ['Resilience & Mutual Aid · Simulation', 'Match Aid Request'],
    ['Digital Twin · Simulation', 'Run Simulation'],
    ['City Organism · Simulation', 'Run Antifragile Drill'],
    ['Enterprise Command Center · Demo', 'Load Risk Radar'],
  ];
  for (const [workspace] of workspaces) {
    await expect(page.getByRole('heading', { name: workspace })).toBeVisible();
  }
  for (const [workspace, control] of workspaces) {
    const card = page.locator('article').filter({ hasText: workspace });
    await card.getByRole('button', { name: 'Open Workspace' }).click();
    if (workspace.startsWith('Civic Map')) {
      await expect(page.getByLabel(control)).toBeVisible();
    } else {
      await expect(page.getByRole('button', { name: control, exact: true })).toBeVisible();
    }
    await page.getByRole('button', { name: 'All Workspaces' }).click();
  }
});

test('mobile layout has no horizontal page overflow', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /What happened\? Find the next step\./ })).toBeVisible();
  for (const width of [320, 360, 375, 390, 430, 768, 1024, 1280, 1366, 1440, 1536, 1920, 2560]) {
    await page.setViewportSize({ width, height: 844 });
    await page.waitForTimeout(50);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `page overflow at ${width}px`).toBe(true);
    const orb = await page.getByRole('button', { name: 'Open Problem Solver' }).boundingBox();
    expect(orb).not.toBeNull();
    expect(orb!.x + orb!.width).toBeLessThanOrEqual(width + 1);
  }

  await page.setViewportSize({ width: 320, height: 844 });
  await page.getByRole('link', { name: 'Open Labs' }).click();
  await page.getByRole('button', { name: 'Create a sample record' }).click();
  const reportDialog = page.getByRole('dialog', { name: 'Create SCMIRN Demo Record' });
  await expect(reportDialog).toBeVisible();
  const dialog = await reportDialog.boundingBox();
  expect(dialog).not.toBeNull();
  expect(dialog!.x).toBeGreaterThanOrEqual(0);
  expect(dialog!.x + dialog!.width).toBeLessThanOrEqual(321);
  await page.keyboard.press('Escape');

  await page.getByRole('button', { name: 'Open Problem Solver' }).click();
  const chat = page.getByRole('region', { name: 'SCMIRN source-linked problem solver' });
  await expect(chat).toBeVisible();
  const chatBox = await chat.boundingBox();
  expect(chatBox).not.toBeNull();
  expect(chatBox!.x).toBeGreaterThanOrEqual(0);
  expect(chatBox!.x + chatBox!.width).toBeLessThanOrEqual(321);
  await chat.getByRole('button', { name: 'Close problem solver' }).click();

  await page.goto('/platform');
  for (const width of [320, 390, 768, 1024, 1440, 1920, 2560]) {
    await page.setViewportSize({ width, height: 844 });
    await page.waitForTimeout(50);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `platform overflow at ${width}px`).toBe(true);
  }

});
