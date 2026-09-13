import { defineConfig, devices } from '@playwright/test';

/**
 * Config for the *production* performance probes (11.6 / market-quality table).
 *
 * Deliberately different from `playwright.config.ts`:
 *  - no `webServer`: it must hit the deployed stack, never a local build;
 *  - a mobile project, because the threshold is stated for "móvil medio en 4G";
 *  - a long per-test timeout, since the budget being measured is itself 60 s.
 *
 * Run:  npx playwright test -c playwright.prod.config.ts
 */
export default defineConfig({
  testDir: './e2e-prod',
  timeout: 180_000,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: process.env.PROD_BASE_URL ?? 'https://whetzy.com',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'mobile-4g',
      use: { ...devices['Pixel 5'] },
    },
  ],
});
