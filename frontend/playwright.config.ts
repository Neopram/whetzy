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
    // es-ES: los tests están escritos contra la UI en español, y desde 34.11
    // /auth y la landing eligen idioma por el del navegador (en-US por defecto
    // en Chromium headless). Los tests bilingües fijan el inglés ellos mismos.
    { name: 'chromium', use: { ...devices['Desktop Chrome'], locale: 'es-ES' } },
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
        // Same reason for the general per-IP budget (120/min by default): every
        // worker shares 127.0.0.1, and a 429 on /auth/me drops a freshly
        // registered user back on the landing — the intermittent reds of
        // 2026-09-24 (a different 1-3 tests failing on every full run).
        DEFAULT_RATE_LIMIT: '5000',
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
