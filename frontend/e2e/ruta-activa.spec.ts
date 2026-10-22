import { test, expect } from '@playwright/test';
import { completeOnboarding, uniqueUsername } from './helpers';

/**
 * 43.4 (ADR-65 D5/D6): la ruta activa se cambia desde Rutas, persiste tras
 * recargar (vive en el servidor) y Hoy la nombra arriba.
 */
test('cambiar de ruta persiste tras recargar y Hoy la nombra', async ({ page }) => {
  const username = uniqueUsername('e2e_ruta_');
  await page.goto('/auth');
  await page.getByLabel('Nombre').fill('Ruta Activa');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByLabel('Confirmo que tengo 16 años o más').check();
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();

  await completeOnboarding(page); // Aprender → Python Básico → empiezo de cero → Hoy
  const header = page.getByTestId('home-active-track');
  await expect(header).toContainText('Tu ruta: Python Básico', { timeout: 15_000 });

  // «Cambiar» → catálogo → Ciberseguridad → «Hacer esta mi ruta».
  await header.getByRole('button', { name: 'Cambiar' }).click();
  await page.getByRole('button', { name: /Ciberseguridad/ }).first().click();
  const saved = page.waitForResponse(
    (r) => r.url().endsWith('/auth/me') && r.request().method() === 'PATCH' && r.ok(),
  );
  await page.getByRole('button', { name: 'Hacer esta mi ruta' }).click();
  await saved;
  await expect(page.getByTestId('track-is-active')).toBeVisible();
  // Sin progreso en la ruta nueva se ofrece su prueba de nivel.
  await expect(page.getByRole('button', { name: 'Hacer la prueba' })).toBeVisible();

  await page.reload();
  await page.getByRole('button', { name: 'Hoy', exact: true }).click();
  await expect(page.getByTestId('home-active-track')).toContainText('Tu ruta: Ciberseguridad', { timeout: 15_000 });
});
