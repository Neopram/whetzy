import { defineConfig, devices } from '@playwright/test';
import { OUTBOX_DIR } from './e2e/outbox';

// Chromium propio de la máquina (p. ej. /opt/pw-browsers/chromium en el
// contenedor de las sesiones): sin esto hacía falta escribir un config local,
// y un verificador de solo lectura (PROTOCOLO_VERIFICACION §7) no podía correr
// el e2e (2026-10-17, 43.1).
const executablePath = process.env.PW_CHROMIUM_EXECUTABLE || undefined;

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
    {
      name: 'chromium',
      testIgnore: /entre-sitios\.spec\.ts/,
      use: { ...devices['Desktop Chrome'], locale: 'es-ES', launchOptions: { executablePath } },
    },
    // 43.1 (ADR-65 D1): la API en otro sitio (127.0.0.1 frente a localhost) y
    // Chromium bloqueando las cookies de terceros, como Safari en iPhone con la
    // API en `*.up.railway.app`. Su frontend es el de :5198, con la API absoluta.
    {
      name: 'entre-sitios',
      // 43.8: la puerta del alumno corre también aquí (§6 del anexo: «y con
      // cookies de terceros bloqueadas»); en `chromium` corre en el mismo sitio.
      // 45.4: la puerta de la serie 45 (correoAlta) también corre entre sitios.
      testMatch: /(entre-sitios|alumno|correoAlta)\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        locale: 'es-ES',
        baseURL: 'http://localhost:5198',
        launchOptions: { executablePath, args: ['--test-third-party-cookie-phaseout'] },
      },
    },
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
        EMAIL_OUTBOX_DIR: OUTBOX_DIR,
        // The suite's frontend runs on :5199, which is not in the default
        // origin list (only :3000 and :5173). The CSRF middleware rejected
        // every POST carrying a session cookie from it (`POST /quiz/start`,
        // a second login…): 18 of 52 specs went red on a default run
        // (2026-10-16). Replaces the list, so it keeps :5173 too. JSON, not
        // comma-separated: pydantic-settings decodes a list[str] env var as
        // JSON before the field validator ever sees it, and the backend
        // refused to start with the comma form.
        BACKEND_CORS_ORIGINS: JSON.stringify([
          'http://localhost:5199', 'http://127.0.0.1:5199', 'http://localhost:5198',
          'http://localhost:5173', 'http://127.0.0.1:5173',
        ]),
      },
    },
    {
      command: 'npm run dev -- --port 5199 --strictPort',
      url: 'http://localhost:5199',
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      // El proyecto `entre-sitios`: la API en otro origen y otro sitio.
      command: 'npm run dev -- --port 5198 --strictPort',
      url: 'http://localhost:5198',
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: { VITE_API_URL: 'http://127.0.0.1:8000/api/v1' },
    },
  ],
});
