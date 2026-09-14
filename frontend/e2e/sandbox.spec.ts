import { test, expect } from '@playwright/test';

/**
 * Pyodide sandbox hardening tests (task 2.2, repaired by 12.11).
 *
 * Uses a minimal harness page (/pyodide-sandbox-test.html) that drives the
 * worker directly, bypassing the app UI. Three properties are verified:
 *
 * 1. `import os` raises ImportError (blocked).
 * 2. `while True: pass` is interrupted and the WORKER reports timedOut:true.
 * 3. The interpreter survives that interrupt and runs the next snippet.
 *
 * Why (2) is worded that way: the previous version of this file asserted the
 * same DOM node, but the harness itself filled it in — it ran its own kill
 * timer and wrote `timedOut: true` when the worker went quiet. So the test
 * passed against a worker whose timeout could never fire (the timer was set
 * inside the worker, whose event loop is blocked while `runPython` runs), and
 * that is what shipped. The harness now reports only what the worker said, and
 * records an explicit failure if the worker never answers.
 *
 * (3) is not a bonus: interrupting rather than terminating is the entire point
 * of the SharedArrayBuffer, and the only way to tell them apart from outside is
 * that after an interrupt the next run is instant instead of paying a full
 * Pyodide reload.
 */

// Pyodide downloads ~13 MB of WASM on first run — allow generous time.
const PYODIDE_READY_TIMEOUT = 120_000;

async function readResult(page: import('@playwright/test').Page, id: string) {
  const raw = await page.locator(`#result-${id}`).textContent();
  return JSON.parse(raw ?? '{}') as {
    error: string | null;
    output: string;
    timedOut: boolean;
    harnessGaveUp?: boolean;
  };
}

test.describe('Pyodide sandbox hardening', () => {
  test.setTimeout(180_000);

  test('import os is blocked', async ({ page }) => {
    await page.goto('/pyodide-sandbox-test.html');

    await page.waitForFunction(
      () => (document.getElementById('result-import-os')?.textContent ?? '') !== '',
      { timeout: PYODIDE_READY_TIMEOUT + 30_000 },
    );

    const result = await readResult(page, 'import-os');
    expect(
      result.error,
      `import os must raise ImportError; got: ${JSON.stringify(result.error)}`,
    ).toMatch(/ImportError|not allowed/i);
    expect(result.timedOut).toBe(false);
  });

  test('while True: pass is interrupted, and the worker itself says so', async ({ page }) => {
    await page.goto('/pyodide-sandbox-test.html');

    const start = Date.now();
    await page.waitForFunction(
      () => (document.getElementById('result-timeout')?.textContent ?? '') !== '',
      { timeout: PYODIDE_READY_TIMEOUT + 40_000 },
    );

    const result = await readResult(page, 'timeout');
    const elapsed = (Date.now() - start) / 1000;

    // The harness writes this instead of a fake pass when the worker goes quiet.
    expect(
      result.harnessGaveUp ?? false,
      'the worker never reported back: the interrupt did not land, which is the ' +
        'exact failure this test exists to catch (see task 12.11)',
    ).toBe(false);

    expect(
      result.timedOut,
      `the worker must report timedOut; got: ${JSON.stringify(result)}`,
    ).toBe(true);
    // The interrupt arrives as a KeyboardInterrupt inside Python — evidence that
    // execution was stopped, not that the worker was killed from outside.
    expect(`${result.error ?? ''}${result.output}`).toMatch(/KeyboardInterrupt|TimeoutError/);
    expect(
      elapsed,
      `timeout test completed in ${elapsed.toFixed(1)}s — must finish within 60s of page load`,
    ).toBeLessThan(60);
  });

  test('the interpreter survives the interrupt and runs the next snippet', async ({ page }) => {
    await page.goto('/pyodide-sandbox-test.html');

    await page.waitForFunction(
      () => (document.getElementById('result-after-timeout')?.textContent ?? '') !== '',
      { timeout: PYODIDE_READY_TIMEOUT + 60_000 },
    );

    const result = await readResult(page, 'after-timeout');
    expect(result.error, `a run after the interrupt must succeed; got: ${result.error}`).toBeNull();
    expect(result.output.trim()).toBe('42');
  });
});
