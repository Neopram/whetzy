import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  reporter: [
    ['html', { open: 'never' }],
    ['github'],
    ['list'],
  ],
  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  globalSetup: './global-setup.ts',
  webServer: [
    {
      // DATABASE_URL is injected by the CI environment (PostgreSQL) or local env.
      // For local dev, set DATABASE_URL before running playwright, e.g.:
      //   DATABASE_URL=postgresql+asyncpg://whetzy:whetzy@localhost:5432/whetzy_e2e npx playwright test
      command:
        'python -m uvicorn app.main:app --port 8000',
      url: 'http://localhost:8000/health/ready',
      cwd: '../backend',
      env: {
        DATABASE_URL: process.env.DATABASE_URL ?? 'postgresql+asyncpg://whetzy:whetzy@localhost:5432/whetzy_e2e',
        ENVIRONMENT: process.env.ENVIRONMENT ?? 'test',
        SECRET_KEY: process.env.SECRET_KEY ?? 'e2e-local-secret',
        GROQ_API_KEY: process.env.GROQ_API_KEY ?? '',
      },
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      cwd: '../frontend',
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
});
