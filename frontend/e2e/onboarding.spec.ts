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
  await page.getByLabel('Confirmo que tengo 13 años o más').check();
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();

  // Onboarding (24.3): three segment questions that auto-advance, then the
  // language choice, then home. It must appear — not the home screen directly.
  const onboarding = page.getByTestId('onboarding');
  await expect(onboarding).toBeVisible({ timeout: 15_000 });
  for (let i = 0; i < 3; i++) {
    await onboarding.locator('button.option').first().click();
    await page.waitForTimeout(700); // the screen advances itself after 600 ms
  }
  await onboarding.getByRole('button', { name: /Español/ }).click();

  // D-20: quien empieza de cero va directo a la primera lección de su ruta
  // (OnboardingScreen.handleLanguageSelect); abrirla ya registra la vista y
  // levanta la puerta de lecciones (32.4). Antes el spec pasaba por «ESTUDIAR
  // AHORA» → «Ir a las lecciones» → «Aprender», un camino que ya no existe.
  const closeLesson = page.getByRole('button', { name: 'Cerrar' });
  await expect(closeLesson).toBeVisible({ timeout: 15_000 });
  await closeLesson.click(); // onExit → 'tracks' (App.tsx)

  // Back to Home, now unblocked.
  await page.getByRole('button', { name: 'Hoy', exact: true }).click();
  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();

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
  await page.getByLabel('Confirmo que tengo 13 años o más').check();
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
  await expect(page.getByRole('button', { name: 'Hoy', exact: true })).toBeVisible({ timeout: 15_000 });
  // …and onboarding is nowhere on it. Asserted on OnboardingScreen's own
  // test id, not on any button: the old CTA shared an accessible name with
  // the registration button. (An earlier version asserted this with a
  // `.catch(() => {})` tacked on, which made it incapable of ever failing.)
  await expect(page.getByTestId('onboarding')).toHaveCount(0);
});
