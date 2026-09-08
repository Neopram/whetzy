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
      // Env vars are set inline — works on Linux CI; adjust for local Windows dev
      command:
        'DATABASE_URL=sqlite+aiosqlite:///./e2e-test.db ENVIRONMENT=test SECRET_KEY=e2e-test-secret GROQ_API_KEY= python -m uvicorn app.main:app --port 8000',
      url: 'http://localhost:8000/health/ready',
      cwd: '../backend',
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
