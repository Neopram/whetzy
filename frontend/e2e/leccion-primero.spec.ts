import { test, expect } from '@playwright/test';
import { completeOnboarding, uniqueUsername } from './helpers';

/**
 * 43.5 (ADR-65 D7): con una cuenta nueva, «Estudiar» abre la lección, no un
 * quiz que acaba en «Abre una lección primero».
 */
test('cuenta nueva: «Estudiar» abre la primera lección de la ruta', async ({ page }) => {
  const username = uniqueUsername('e2e_lp_');
  await page.goto('/auth');
  await page.getByLabel('Nombre').fill('Lección Primero');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByLabel('Confirmo que tengo 13 años o más').check();
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();
  await completeOnboarding(page); // Python Básico, empiezo de cero → Hoy

  await expect(page.getByTestId('home-next')).toContainText('Lección:', { timeout: 15_000 });
  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
  // Es la lección (LessonScreen tiene «Cerrar»), no el quiz ni su aviso.
  await expect(page.getByRole('button', { name: 'Cerrar' })).toBeVisible({ timeout: 15_000 });
  await expect(page.locator('[class*="questionCard_"]')).toHaveCount(0);
});
