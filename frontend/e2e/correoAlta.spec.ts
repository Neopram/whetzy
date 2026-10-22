import { test, expect } from '@playwright/test';
import { registerUser, suppressOnboarding, uniqueUsername } from './helpers';
import { emailsTo, verifyPath } from './outbox';

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

/**
 * 45.4: puerta de cierre de la serie 45 (ADR-66), en `chromium` y en
 * `entre-sitios`. Lo que pasó el 2026-10-17: un iPhone en inglés con la
 * portada en «ES» se registraba en inglés y recibía dos correos en inglés.
 *
 * Navegador en inglés → portada en «ES» → registro → un solo correo, en
 * español → franja visible → enlace del correo → «Continuar» → Hoy sin franja
 * → la bienvenida, en español.
 */
test.describe('puerta 45: alta en español con el navegador en inglés', () => {
  test.use({ locale: 'en-US' });

  test('un correo en español, franja, verificar y la franja desaparece', async ({ page }) => {
    test.setTimeout(120_000);
    const username = uniqueUsername('e2e_puerta45_');
    const email = `${username}@example.com`;

    await page.goto('/landing');
    await expect(page.getByRole('button', { name: 'English' })).toBeVisible();
    await page.getByRole('button', { name: 'Español' }).click();
    await page.getByRole('link', { name: 'Empieza gratis' }).first().click();
    await expect(page).toHaveURL(/\/auth\?lang=es/);

    await page.getByLabel('Nombre').fill('Puerta');
    await page.getByLabel('Usuario').fill(username);
    await page.getByLabel('Correo electrónico').fill(email);
    await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
    await page.getByLabel('Confirmo que tengo 16 años o más').check();
    const registered = page.waitForResponse(
      (r) => r.url().endsWith('/auth/register') && r.request().method() === 'POST',
    );
    await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();
    const reg = await registered;
    expect(reg.status()).toBe(201);
    expect(JSON.parse(reg.request().postData() ?? '{}').language).toBe('es');

    // Un solo correo, el de verificación, en español y con el idioma en el enlace.
    await expect.poll(() => emailsTo(email).length).toBe(1);
    const [verification] = emailsTo(email);
    expect(verification.subject).toBe('Verifica tu email en Whetzy');
    const link = verifyPath(verification.html);
    expect(link).toMatch(/[?&]lang=es(&|$)/);

    await suppressOnboarding(page);
    const banner = page.getByTestId('verify-email-banner');
    await expect(banner).toBeVisible({ timeout: 15_000 });
    await expect(banner).toContainText('Te enviamos un enlace a');

    // El enlace del correo, en la misma pestaña (con la sesión abierta).
    await page.goto(link);
    await expect(page.getByText('Email verificado')).toBeVisible({ timeout: 15_000 });
    await page.getByRole('link', { name: 'Continuar' }).click();
    await expect(page.getByRole('button', { name: 'Hoy', exact: true })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('verify-email-banner')).toHaveCount(0);

    // Y la bienvenida sale ahora, una vez, en español.
    await expect.poll(() => emailsTo(email).length).toBe(2);
    expect(emailsTo(email)[1].subject).toBe('Bienvenido/a a Whetzy, Puerta!');
  });
});
