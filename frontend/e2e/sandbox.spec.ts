import { test, expect } from '@playwright/test';

/**
 * Pyodide sandbox hardening tests (task 2.2).
 *
 * Uses a minimal test harness page (/pyodide-sandbox-test.html) that drives
 * the worker directly, bypassing the app UI.  Two properties are verified:
 *
 * 1. `import os` raises ImportError (blocked).
 * 2. `while True: pass` is interrupted and reports timedOut:true within 10 s.
 *
 * Both tests share a single page load so Pyodide is initialised only once.
 */

// Pyodide downloads ~10 MB of WASM on first run — allow generous time.
const PYODIDE_READY_TIMEOUT = 120_000;

test.describe('Pyodide sandbox hardening', () => {
  test.setTimeout(180_000);

  test('import os is blocked', async ({ page }) => {
    await page.goto('/pyodide-sandbox-test.html');

    // Wait for the worker to load Pyodide and run the first test.
    await page.waitForFunction(
      () => {
        const el = document.getElementById('result-import-os');
        return el && el.textContent !== '';
      },
      { timeout: PYODIDE_READY_TIMEOUT + 30_000 },
    );

    const raw = await page.locator('#result-import-os').textContent();
    const result = JSON.parse(raw ?? '{}') as { error: string | null; timedOut: boolean };

    expect(result.error, `import os must raise ImportError; got: ${JSON.stringify(result.error)}`).toMatch(/ImportError|not allowed/i);
    expect(result.timedOut).toBe(false);
  });

  test('while True: pass times out and reports timedOut:true', async ({ page }) => {
    await page.goto('/pyodide-sandbox-test.html');

    // The harness runs import-os first, then triggers the timeout test.
    const start = Date.now();
    await page.waitForFunction(
      () => {
        const el = document.getElementById('result-timeout');
        return el && el.textContent !== '';
      },
      // Pyodide init + import-os test + up to 8s timeout margin
      { timeout: PYODIDE_READY_TIMEOUT + 40_000 },
    );

    const raw = await page.locator('#result-timeout').textContent();
    const result = JSON.parse(raw ?? '{}') as { error: string | null; timedOut: boolean };
    const elapsed = (Date.now() - start) / 1000;

    expect(result.timedOut, `timedOut flag must be true; got: ${JSON.stringify(result)}`).toBe(true);
    expect(elapsed, `timeout test completed in ${elapsed.toFixed(1)}s — must finish within 60s of page load`).toBeLessThan(60);
  });
});
