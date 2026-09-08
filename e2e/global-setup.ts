import type { FullConfig } from '@playwright/test';
import { execSync } from 'child_process';
import path from 'path';

const BACKEND_DIR = path.join(__dirname, '../backend');
const BACKEND_URL = 'http://localhost:8000';

const E2E_ENV: NodeJS.ProcessEnv = {
  ...process.env,
  DATABASE_URL: 'sqlite+aiosqlite:///./e2e-test.db',
  ENVIRONMENT: 'test',
  SECRET_KEY: 'e2e-test-secret',
  GROQ_API_KEY: '',
};

/** Poll /health/ready until the backend responds 200 (webServer config should
 *  already guarantee this, but we add a guard for robustness). */
async function waitForBackend(maxAttempts = 30, delayMs = 2000): Promise<void> {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const resp = await fetch(`${BACKEND_URL}/health/ready`);
      if (resp.ok) return;
    } catch {
      // not ready yet
    }
    await new Promise<void>((r) => setTimeout(r, delayMs));
  }
  throw new Error('[global-setup] Backend did not become ready in time');
}

/** Load question content into the E2E SQLite database. */
function seedContent(): void {
  try {
    execSync('python -m app.services.content_loader', {
      cwd: BACKEND_DIR,
      env: E2E_ENV,
      stdio: 'inherit',
      timeout: 120_000,
    });
    console.log('[global-setup] Content seeded successfully.');
  } catch (err) {
    // Content may already be seeded from a previous run — treat as non-fatal.
    console.warn('[global-setup] content_loader warning (may already be seeded):', err);
  }
}

/** Create a shared test user and expose credentials via process.env. */
async function registerTestUser(): Promise<void> {
  const ts = Date.now();
  const email = `e2e-${ts}@whetzy.test`;
  const username = `e2euser${ts}`;
  const password = 'E2ETest!2024';

  const resp = await fetch(`${BACKEND_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      username,
      display_name: 'E2E Tester',
      password,
      language: 'es',
    }),
  });

  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`[global-setup] Test user registration failed: ${resp.status} ${body}`);
  }

  // Expose to tests via environment variables
  process.env.E2E_EMAIL = email;
  process.env.E2E_PASSWORD = password;
  console.log(`[global-setup] Test user created: ${email}`);
}

export default async function globalSetup(_config: FullConfig): Promise<void> {
  await waitForBackend();
  seedContent();
  await registerTestUser();
}
