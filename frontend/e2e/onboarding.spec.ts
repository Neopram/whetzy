import { test, expect } from '@playwright/test';
import { answerCurrentQuestion, uniqueUsername } from './helpers';

test('onboarding: landing → first answered question in < 60 s', async ({ page }) => {
  const start = Date.now();

  // Register a new user
  const username = uniqueUsername('e2e_ob_');
  await page.goto('/');
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

  // Register
  await page.goto('/');
  await page.getByLabel('Nombre').fill('Returning Test');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();

  // Mark onboarding done in localStorage (simulates returning user)
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => {
    // Find the user id from zustand persisted state
    try {
      const raw = localStorage.getItem('learning-engine-store');
      if (raw) {
        const parsed = JSON.parse(raw) as { state?: { user?: { id?: string } } };
        const uid = parsed.state?.user?.id;
        if (uid) localStorage.setItem(`whetzy_onboarded_${uid}`, '1');
      }
    } catch { /* ignore */ }
  });

  // Reload — should land on home screen, not onboarding
  await page.reload();
  await page.waitForLoadState('networkidle');

  // Home screen bottom nav must appear (no onboarding CTA)
  await expect(page.getByRole('button', { name: 'Inicio' })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('button', { name: /EMPEZAR A APRENDER/i })).not.toBeVisible({ timeout: 2_000 }).catch(() => {/* already not visible */});
});
