import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [['html', { open: 'never' }], ['list']],
  timeout: 60_000,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5199',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  // Skipped when E2E_BASE_URL is set (local runs against servers already
  // started by hand); CI always starts fresh so both come up from a clean,
  // migrated, content-seeded DB every run.
  webServer: process.env.E2E_BASE_URL ? undefined : [
    {
      command: 'python -m uvicorn app.main:app --host 127.0.0.1 --port 8000',
      cwd: '../backend',
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        // AUTH_RATE_LIMIT raised well above the 12/min production default —
        // the suite registers several fresh users per run (see e2e/helpers.ts).
        AUTH_RATE_LIMIT: '200',
      },
    },
    {
      command: 'npm run dev -- --port 5199 --strictPort',
      url: 'http://localhost:5199',
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
});
