import { test, expect } from '@playwright/test';
import { answerCurrentQuestion, suppressOnboarding, uniqueUsername } from './helpers';

test('onboarding: landing → first answered question in < 60 s', async ({ page }) => {
  const start = Date.now();

  // Register a new user
  const username = uniqueUsername('e2e_ob_');
  await page.goto('/auth');
  await expect(page.getByRole('button', { name: 'Crear cuenta' })).toBeVisible();

  await page.getByLabel('Nombre').fill('Onboarding Test');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();

  // Onboarding screen must appear (not the home screen directly)
  const ctaBtn = page.getByRole('button', { name: 'EMPEZAR A APRENDER' });
  await expect(ctaBtn).toBeVisible({ timeout: 15_000 });

  // Tap the CTA — should jump directly into QuizScreen
  await ctaBtn.click();

  // First question must appear
  await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });

  // Answer the first question. Which *kind* of question gets drawn depends on the
  // learner's state and on row order in the content DB, so this must handle an
  // exec question too: one click on "Run" does not necessarily reach feedback
  // (Pyodide has to boot, and the app only auto-submits on the 3rd attempt).
  // answerCurrentQuestion encapsulates exactly that, and is what every other
  // spec uses.
  await answerCurrentQuestion(page);

  const elapsed = (Date.now() - start) / 1000;
  expect(elapsed, `Took ${elapsed.toFixed(1)}s — must be < 60s`).toBeLessThan(60);
});

test('onboarding is skipped for returning users', async ({ page }) => {
  const username = uniqueUsername('e2e_ret_');

  // Register by hand rather than via registerUser — that helper suppresses
  // onboarding itself, which is the very thing under test here.
  await page.goto('/auth');
  await page.getByLabel('Nombre').fill('Returning Test');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();

  // Turn this brand-new account into a returning one: set the same
  // whetzy_onboarded_<uid> flag a returning user would already carry, then
  // reload.
  //
  // This used to be inlined here, reading the user id straight after
  // waitForLoadState('networkidle') — which does NOT guarantee zustand has
  // persisted it yet. When it hadn't, the `if (uid)` guard silently did
  // nothing, the reload showed onboarding again, and the test failed 15 s
  // later pointing at a missing "Inicio" button instead of at the real cause.
  // It passed locally and failed in CI, twice, for exactly that reason.
  // suppressOnboarding waits for the onboarding screen first, which is proof
  // that hydration finished and the id exists.
  await suppressOnboarding(page);

  // A returning user lands on the home screen…
  await expect(page.getByRole('button', { name: 'Inicio' })).toBeVisible({ timeout: 15_000 });
  // …and onboarding is nowhere on it. Asserted on OnboardingScreen's own
  // headline, not on its CTA: the CTA shares an accessible name with the
  // registration button. (The previous version asserted this with a
  // `.catch(() => {})` tacked on, which made it incapable of ever failing.)
  await expect(page.locator('[class*="headline_"]')).toHaveCount(0);
});
