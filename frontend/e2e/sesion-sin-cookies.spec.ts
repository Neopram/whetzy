import { test, expect, request, type Page } from '@playwright/test';
import { uniqueUsername } from './helpers';

/**
 * 43.1 (ADR-65 D1): Safari en iPhone no manda las cookies de la API desde
 * `whetzy.com`, porque la API vive en otro dominio y para él son de terceros.
 * Antes, tras registrarse, `GET /auth/me` llegaba sin sesión (401 en Railway) y
 * la app volvía a la portada.
 *
 * Aquí se simula Safari quitando todo `Set-Cookie` de las respuestas de la API:
 * el navegador nunca llega a tener cookie de sesión. El registro tiene que
 * llegar a Hoy igual, y seguir ahí tras recargar: al ver que la cookie no llega,
 * los tokens se guardan en `sessionStorage` y viajan como `Authorization`. Es un
 * puente hasta que la cookie sea de `.whetzy.com` (H.61).
 */
async function dropApiCookies(page: Page) {
  // `route.fetch()` comparte el tarro de cookies del navegador y guardaría el
  // `Set-Cookie`. Cada llamada sale por un contexto nuevo, sin tarro, y la
  // respuesta vuelve sin `Set-Cookie`. Las cookies del navegador nunca viajan
  // (no se reenvía `cookie`), igual que en Safari.
  await page.route('**/api/v1/**', async (route) => {
    const api = await request.newContext();
    try {
      const req = route.request();
      const headers = { ...req.headers() };
      delete headers['cookie'];
      const response = await api.fetch(req.url(), {
        method: req.method(),
        headers,
        data: req.postDataBuffer() ?? undefined,
        failOnStatusCode: false,
        maxRedirects: 0,
      });
      const out = { ...response.headers() };
      delete out['set-cookie'];
      await route.fulfill({ status: response.status(), headers: out, body: await response.body() });
    } finally {
      await api.dispose();
    }
  });
}

test('sin cookies de la API (Safari), registrarse llega a Hoy sin volver a la portada', async ({ page }) => {
  await dropApiCookies(page);
  const username = uniqueUsername('e2e_nocookie_');

  await page.goto('/auth');
  await page.getByLabel('Nombre').fill('Sin Cookies');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByLabel('Confirmo que tengo 13 años o más').check();
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();

  // El onboarding solo aparece si /auth/me respondió con el usuario: es la
  // prueba de que hay sesión sin cookie.
  const onboarding = page.getByTestId('onboarding');
  await expect(onboarding).toBeVisible({ timeout: 15_000 });
  expect(await page.context().cookies()).toEqual([]);

  for (let i = 0; i < 3; i++) {
    await onboarding.locator('button.option').first().click();
    await page.waitForTimeout(700);
  }
  await onboarding.getByRole('button', { name: /Español/ }).click();

  const closeLesson = page.getByRole('button', { name: 'Cerrar' });
  await expect(closeLesson).toBeVisible({ timeout: 15_000 });
  await closeLesson.click();
  await page.getByRole('button', { name: 'Hoy', exact: true }).click();

  await expect(page.getByRole('button', { name: 'ESTUDIAR AHORA' })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('button', { name: 'Crear cuenta' })).toHaveCount(0);

  // Una recarga (pull-to-refresh en el iPhone) no tira la sesión.
  await page.reload();
  await expect(page.getByRole('button', { name: 'Hoy', exact: true })).toBeVisible({ timeout: 15_000 });
  expect(await page.context().cookies()).toEqual([]);
});
