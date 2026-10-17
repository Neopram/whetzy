import { test, expect } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

/**
 * 45.3 (ADR-66 E4): tras registrarse, la app avisa de que falta verificar el
 * correo con una franja en el armazón (no dentro de Hoy), con el email
 * enmascarado, «Reenviar» y ×. No bloquea nada (E3).
 */
test('tras el registro, la franja «verifica tu correo» es visible y se puede ocultar', async ({ page }) => {
  const username = uniqueUsername('e2e_franja_');
  await registerUser(page, { username, displayName: 'Franja' });

  const banner = page.getByTestId('verify-email-banner');
  await expect(banner).toBeVisible();
  await expect(banner).toContainText(`${username.slice(0, 2)}***@example.com`);
  await expect(banner).not.toContainText(`${username}@example.com`);

  // «Reenviar» pide otro enlace y espera antes de dejar pedir otro.
  const resent = page.waitForResponse(
    (r) => r.url().endsWith('/auth/resend-verification') && r.request().method() === 'POST',
  );
  await banner.getByRole('button', { name: 'Reenviar' }).click();
  expect((await resent).status()).toBe(200);
  await expect(banner.getByRole('button', { name: /Reenviar en \d+ s/ })).toBeDisabled();

  // La × la oculta y sigue oculta al cambiar de pantalla dentro de la sesión.
  await banner.getByRole('button', { name: 'Ocultar aviso' }).click();
  await expect(banner).toHaveCount(0);
  await page.getByRole('button', { name: 'Yo', exact: true }).click();
  await page.getByRole('button', { name: 'Hoy', exact: true }).click();
  await expect(page.getByTestId('verify-email-banner')).toHaveCount(0);
});
