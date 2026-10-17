import { test, expect } from '@playwright/test';
import { completeOnboarding, suppressOnboarding, uniqueUsername } from './helpers';

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

  // 43.3 (D2): objetivo → ruta → experiencia → prueba de nivel. Tiene que
  // aparecer el onboarding, no Hoy directamente, y ya no pregunta el idioma.
  await completeOnboarding(page, { takeTest: true });

  // La primera pregunta que contesta es la primera de la prueba de nivel de su ruta.
  await page.getByRole('button', { name: 'COMENZAR EXAMEN' }).click();
  await expect(page.getByText('Pregunta 1 de 20')).toBeVisible({ timeout: 15_000 });
  await page.getByTestId('placement-option').first().click();
  await expect(page.getByText('Pregunta 2 de 20')).toBeVisible({ timeout: 15_000 });

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

test('otro navegador no repite el onboarding (43.3, D2)', async ({ browser }) => {
  const username = uniqueUsername('e2e_ob2_');
  const first = await browser.newContext();
  const page = await first.newPage();
  await page.goto('/auth');
  await page.getByLabel('Nombre').fill('Dos Navegadores');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByLabel('Confirmo que tengo 13 años o más').check();
  const saved = page.waitForResponse(
    (r) => r.url().endsWith('/auth/me') && r.request().method() === 'PATCH' && r.ok(),
  );
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();
  await completeOnboarding(page);
  await saved;
  await expect(page.getByRole('button', { name: 'Hoy', exact: true })).toBeVisible({ timeout: 15_000 });
  await first.close();

  // Un contexto nuevo no tiene nada en localStorage: lo que decide es el servidor.
  const second = await browser.newContext();
  const other = await second.newPage();
  await other.goto('/login');
  await other.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await other.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await other.getByRole('button', { name: 'ENTRAR' }).click();
  await expect(other.getByRole('button', { name: 'Hoy', exact: true })).toBeVisible({ timeout: 15_000 });
  await expect(other.getByTestId('onboarding')).toHaveCount(0);
  await second.close();
});
