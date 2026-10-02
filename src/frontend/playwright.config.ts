import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:3411',
    ...devices['Desktop Chrome'],
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run dev -- --config vite.e2e.config.ts',
    url: 'http://127.0.0.1:3411',
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
});
