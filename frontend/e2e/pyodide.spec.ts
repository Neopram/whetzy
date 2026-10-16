import { test, expect } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

/**
 * Pyodide E2E: deterministic exec-type question test.
 *
 * Uses force_question_id (dev/test only) to guarantee a fill_blank_exec
 * question is served, then exercises the full run-code path so we verify
 * that Pyodide initialises, executes, and returns the correct output.
 *
 * Question: q010101ex001 — "x = ___; print(x)" → answer "42" → output "42"
 */

const FORCED_Q_ID = 'q010101ex001';
const CORRECT_BLANK = '42';
const EXPECTED_OUTPUT = '42';

test('fill_blank_exec — Pyodide executes and returns correct output', async ({ page }) => {
  // Pyodide downloads ~10 MB of WASM from CDN on first load.
  // In CI (GitHub Actions, Ubuntu, full internet) this takes 15-60 s.
  test.setTimeout(180_000);

  // Collect page errors so we can assert 0 at the end.
  const pageErrors: string[] = [];
  page.on('pageerror', (err) => pageErrors.push(err.message));

  const username = uniqueUsername('e2e_pyodide_');
  await registerUser(page, { username, displayName: 'E2E Pyodide' });

  // From now on, every quiz/start request will serve the forced exec question.
  await page.route('**/quiz/start', async (route, request) => {
    const body = JSON.parse((await request.postData()) ?? '{}') as Record<string, unknown>;
    await route.continue({
      postData: JSON.stringify({ ...body, force_question_id: FORCED_Q_ID }),
    });
  });

  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();

  // The blank input appears when a fill_blank_exec question is rendered.
  const blankInput = page.getByPlaceholder('Escribe tu respuesta aquí…');
  await expect(blankInput).toBeVisible({ timeout: 20_000 });

  await blankInput.fill(CORRECT_BLANK);

  // Run button is disabled while Pyodide is loading ('⚙ Cargando motor Python…').
  // Wait until it becomes enabled (pyodideStatus === 'ready').
  const runBtn = page.locator('[class*="btnRun_"]');
  await expect(runBtn).toBeEnabled({ timeout: 120_000 });

  await runBtn.click();

  // After execution, the output box should appear showing the correct output.
  const outputPre = page.locator('[class*="outputPre_"]');
  await expect(outputPre).toBeVisible({ timeout: 30_000 });
  await expect(outputPre).toHaveText(new RegExp(EXPECTED_OUTPUT));

  // The label should confirm the answer is correct.
  // Ejecutar ya no entrega: muestra la salida y pide «Confirmar» (la
  // etiqueta dice «Salida» hasta entonces). Al confirmar se corrige.
  await page.getByRole('button', { name: /^(Confirmar|Confirm)$/ }).click();
  const outputLabel = page.locator('[class*="outputLabel_"]').first();
  await expect(outputLabel).toContainText('¡Correcto!', { timeout: 15_000 });

  // 0 uncaught page errors during the entire test.
  expect(pageErrors, `Uncaught page errors: ${pageErrors.join('; ')}`).toHaveLength(0);
});
