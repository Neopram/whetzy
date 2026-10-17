import { expect, test } from '@playwright/test';
import { registerUser, suppressOnboarding, uniqueUsername } from './helpers';

/**
 * «Atrás» y la entrada a la app (2026-10-16). Reproducido sobre `master`
 * 56e7001 antes del arreglo:
 * - landing → acceso → panel; «atrás» volvía al formulario con la sesión abierta;
 * - `/auth` con la sesión abierta enseñaba el formulario;
 * - `/login` abría «Crear cuenta»;
 * - `/r/<código>` atrapaba «atrás» en /register.
 */
test('quien vuelve entra por «Entrar» y «atrás» no le devuelve al formulario', async ({ browser }) => {
  const username = uniqueUsername('atras');
  const first = await browser.newContext();
  await registerUser(await first.newPage(), { username, displayName: 'Atrás' });
  await first.close();

  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto('/landing/');
  await page.getByRole('link', { name: 'Entrar' }).click();
  await expect(page).toHaveURL(/\/login$/);
  // /login abre «Iniciar sesión»: sin el campo de nombre del registro.
  await expect(page.getByLabel('Nombre')).toHaveCount(0);

  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByRole('button', { name: 'ENTRAR' }).click();
  await suppressOnboarding(page, { maybeDone: true });
  await expect(page.getByRole('button', { name: 'Hoy', exact: true })).toBeVisible({ timeout: 15_000 });

  // «Atrás» vuelve a la landing, no al formulario de acceso.
  await page.goBack();
  await expect(page).toHaveURL(/\/landing\/?$/);
  await expect(page.getByLabel('Contraseña')).toHaveCount(0);

  // Con la sesión abierta, /auth lleva a la app en vez de pedir la contraseña.
  await page.goto('/auth');
  await expect(page.getByRole('button', { name: 'Hoy', exact: true })).toBeVisible({ timeout: 15_000 });
  await expect(page).toHaveURL(/\/$/);
  await ctx.close();
});

test('un enlace de invitación no atrapa «atrás» en el registro', async ({ page }) => {
  await page.goto('/landing/');
  await page.goto('/r/ATRAS123');
  await expect(page).toHaveURL(/\/register$/);
  await page.goBack();
  await expect(page).toHaveURL(/\/landing\/?$/);
});
