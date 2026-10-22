import { test, expect, type Page, type Route } from '@playwright/test';
import { uniqueUsername } from './helpers';

/**
 * 46.15 F (docs/PLAN_UI_AVANZADA.md §7.7): capturas, a 390 px y en español, de
 * las pantallas de la tabla de §7.5 con su movimiento ya puesto. Backend real
 * para el registro y las pantallas con sesión; lo que en local no existe
 * (certificado válido, correo verificado, Paddle) se simula con `page.route`.
 * No afirma comportamiento (eso lo hacen los specs de cada bloque): solo
 * comprueba que la pantalla carga y deja la imagen en `docs/ui-snapshots/46.15f`.
 */
const SHOTS = '../docs/ui-snapshots/46.15f';
const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

test.use({ viewport: { width: 390, height: 844 } });

async function shot(page: Page, name: string, settleMs = 1200) {
  // Los trozos perezosos del servidor de desarrollo tardan: sin esperar a la red
  // la captura sale con la pantalla de carga.
  await page.waitForLoadState('networkidle', { timeout: 8_000 }).catch(() => {});
  await page.waitForTimeout(settleMs);
  await page.screenshot({ path: `${SHOTS}/${name}-es-390.png` });
}

async function go(page: Page, screen: string) {
  await page.evaluate((s) => {
    (window as unknown as { __whetzyStore: { getState: () => { setScreen: (x: string) => void } } }).__whetzyStore.getState().setScreen(s);
  }, screen);
}

test('A. Entrada: Auth, Verificar, Restablecer (formulario y éxito), Landing y Estado', async ({ page }) => {
  await page.goto('/auth');
  await expect(page.getByRole('button', { name: 'Crear cuenta' })).toBeVisible();
  await shot(page, 'auth');

  await page.route('**/auth/verify-email', (r) => json(r, { message: 'ok' }));
  await page.goto('/verify-email?token=tok');
  await expect(page.getByTestId('drawn-check')).toBeVisible();
  await shot(page, 'verificar');

  await page.goto('/reset-password?token=tok');
  await expect(page.getByRole('button', { name: 'Cambiar' })).toBeVisible();
  await shot(page, 'restablecer-formulario');
  await page.route('**/auth/reset-password', (r) => json(r, { message: 'ok' }));
  await page.getByPlaceholder('Nueva contraseña').fill('e2e-test-pass-123');
  await page.getByPlaceholder('Confirmar').fill('e2e-test-pass-123');
  await page.getByRole('button', { name: 'Cambiar' }).click();
  await expect(page.getByTestId('drawn-check')).toBeVisible();
  await shot(page, 'restablecer-exito', 500);

  await page.goto('/landing');
  await expect(page.locator('[data-lcp="hero"]')).toBeVisible();
  await shot(page, 'landing');

  await page.goto('/status');
  await expect(page.locator('[data-fx="enter"]').first()).toBeVisible();
  await shot(page, 'estado');
});

test('A. Onboarding y B-D con sesión: Hoy, Rutas, Perfil, Stats, Cartera, Liga, Duelo, Playground, Marketplace', async ({ page }) => {
  const username = uniqueUsername('e2e_f_');
  await page.goto('/auth');
  await page.getByLabel('Nombre').fill('Capturas');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByLabel('Confirmo que tengo 13 años o más').check();
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();
  await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible({ timeout: 15_000 });
  await shot(page, 'onboarding');

  // Mismo atajo que `registerUser`: marca el onboarding como hecho y recarga.
  const userId = await page.evaluate(() =>
    (window as unknown as { __whetzyStore: { getState: () => { user: { id: string } } } }).__whetzyStore.getState().user.id);
  await page.evaluate((id) => localStorage.setItem(`whetzy_onboarded_${id}`, '1'), userId);
  await page.reload();
  await expect(page.getByRole('button', { name: 'Hoy', exact: true })).toBeVisible({ timeout: 15_000 });
  await shot(page, 'hoy');

  for (const [screen, name] of [
    ['tracks', 'rutas'], ['profile', 'perfil'], ['stats', 'stats'], ['wallet', 'cartera'], ['league', 'liga'],
    ['duels', 'duelo'], ['playground', 'playground'], ['marketplace', 'marketplace'],
  ] as const) {
    await go(page, screen);
    await shot(page, name);
  }
});

test('D-E. Certificado público y checkout', async ({ page }) => {
  const code = 'a'.repeat(32);
  await page.route('**/exams/certificates/*', (route) =>
    route.request().url().endsWith('/qr') ? route.fulfill({ status: 404 }) : json(route, {
      code, username: 'ada', track_id: 'track01', track_name_es: 'Python Básico', track_name_en: 'Python Basics',
      score_pct: 86.5, questions: 50, issued_at: '2026-10-20T10:00:00Z', revoked: false, is_certification: false,
    }));
  await page.goto(`/certificate/${code}`);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  await shot(page, 'certificado-publico');
  await page.goto('/checkout');
  await shot(page, 'checkout');
});
