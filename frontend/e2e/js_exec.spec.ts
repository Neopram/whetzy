import { test, expect } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

/**
 * JS Worker E2E: deterministic js_exec question test.
 *
 * Uses force_question_id (dev/test only) to guarantee a js_exec question is
 * served, then exercises the full run-code path to verify that the Blob URL
 * Web Worker sandbox initialises, executes, and returns the correct output.
 *
 * Question: q140101js001 — `const greeting = "Hello, ___!"; console.log(greeting);`
 * Answer: "World"  →  output: "Hello, World!"
 *
 * The JS Worker sandbox is synchronous unlike Pyodide (no WASM download), so
 * the Run button is enabled immediately after the question renders.
 */

const FORCED_Q_ID = 'q140101js001';
const CORRECT_BLANK = 'World';
const EXPECTED_OUTPUT = 'Hello, World!';

test('js_exec — Worker sandbox executes and returns correct output', async ({ page }) => {
  test.setTimeout(60_000);

  const pageErrors: string[] = [];
  page.on('pageerror', (err) => pageErrors.push(err.message));

  const username = uniqueUsername('e2e_jsexec_');
  await registerUser(page, { username, displayName: 'E2E JS' });

  await page.route('**/quiz/start', async (route, request) => {
    const body = JSON.parse((await request.postData()) ?? '{}') as Record<string, unknown>;
    await route.continue({
      postData: JSON.stringify({ ...body, force_question_id: FORCED_Q_ID }),
    });
  });

  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();

  const blankInput = page.getByPlaceholder('Escribe tu respuesta aquí…');
  await expect(blankInput).toBeVisible({ timeout: 20_000 });

  await blankInput.fill(CORRECT_BLANK);

  // JS Worker is ready synchronously (no WASM download), so the Run button
  // should be enabled immediately.
  const runBtn = page.locator('[class*="btnRun_"]');
  await expect(runBtn).toBeEnabled({ timeout: 10_000 });

  await runBtn.click();

  const outputPre = page.locator('[class*="outputPre_"]');
  await expect(outputPre).toBeVisible({ timeout: 15_000 });
  await expect(outputPre).toHaveText(new RegExp(EXPECTED_OUTPUT.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));

  // Ejecutar ya no entrega: muestra la salida y pide «Confirmar» (la
  // etiqueta dice «Salida» hasta entonces). Al confirmar se corrige.
  await page.getByRole('button', { name: /^(Confirmar|Confirm)$/ }).click();
  const outputLabel = page.locator('[class*="outputLabel_"]').first();
  await expect(outputLabel).toContainText('¡Correcto!', { timeout: 15_000 });

  expect(pageErrors, `Uncaught page errors: ${pageErrors.join('; ')}`).toHaveLength(0);
});
