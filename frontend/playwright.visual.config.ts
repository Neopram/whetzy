import { defineConfig, devices } from '@playwright/test';

/**
 * 46.5: regresión visual. Config aparte de `playwright.config.ts` a propósito:
 * aquí NO hay backend (la API se simula con `page.route` en `e2e/visual.spec.ts`)
 * y el servidor de desarrollo es propio (:5197), así que corre sin base de datos
 * y en segundos. Solo lo lanza el nivel 2 de `scripts/ci_local.sh`, nunca el hook.
 *
 *   npx playwright test -c playwright.visual.config.ts            # comprobar
 *   npx playwright test -c playwright.visual.config.ts -u        # regenerar baselines
 *
 * Las baselines llevan `{platform}`: el antialiasing del texto cambia entre
 * Linux, Windows y macOS, y una sola carpeta daría rojo en cualquier otra máquina.
 */
const executablePath = process.env.PW_CHROMIUM_EXECUTABLE || undefined;

export default defineConfig({
  testDir: './e2e',
  testMatch: /visual\.spec\.ts/,
  snapshotPathTemplate: '{testDir}/__screenshots__/{platform}/{arg}{ext}',
  fullyParallel: false,
  workers: 1,
  // 1 reintento: el primer arranque en frío de Vite re-optimiza dependencias y la
  // primera carga puede recibir un 504 «Outdated Optimize Dep»; una diferencia de
  // píxeles real falla igual en el reintento.
  retries: 1,
  reporter: [['list']],
  timeout: 60_000,
  expect: { toHaveScreenshot: { animations: 'disabled', caret: 'hide', maxDiffPixelRatio: 0.002 } },
  use: {
    baseURL: 'http://localhost:5197',
    trace: 'off',
    video: 'off',
    screenshot: 'off',
    ...devices['Desktop Chrome'],
    launchOptions: { executablePath },
  },
  webServer: {
    command: 'npm run dev -- --port 5197 --strictPort',
    url: 'http://localhost:5197',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
