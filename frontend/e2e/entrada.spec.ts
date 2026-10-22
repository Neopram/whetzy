import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { completeOnboarding, formatViolations, uniqueUsername } from './helpers';

/**
 * 46.15 bloque A (docs/PLAN_UI_AVANZADA.md §7.5): las pantallas de entrada,
 * contra el backend real salvo verificar el correo (su token sale del buzón;
 * aquí se intercepta la respuesta, no la pantalla).
 * - Entrar con una contraseña mala: el error tiembla y se anuncia (`role=alert`).
 * - «Te enviamos el enlace» y «correo verificado»: un check que se dibuja.
 * - El alta cambia de paso con un desplazamiento lateral.
 * - La prueba de nivel marca un punto por pregunta respondida.
 * Con movimiento reducido no tiembla, no se dibuja y no se desplaza.
 */
const SHOTS = '../docs/ui-snapshots/46.15a';

async function axe0(page: Page) {
  const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  expect(r.violations, formatViolations(r.violations)).toHaveLength(0);
}

const COPY = {
  es: { login: 'ENTRAR', email: 'Correo electrónico', password: 'Contraseña', forgot: '¿Olvidaste tu contraseña?' },
  en: { login: 'LOG IN', email: 'Email', password: 'Password', forgot: 'Forgot your password?' },
} as const;

for (const lang of ['es', 'en'] as const) {
  test.describe(`entrada (${lang})`, () => {
    test.use({ locale: lang === 'es' ? 'es-ES' : 'en-US' });

    for (const width of [390, 1280]) {
      test(`contraseña mala: el error tiembla y se anuncia (${width} px)`, async ({ page }) => {
        await page.setViewportSize({ width, height: 900 });
        await page.goto('/login');
        await page.getByLabel(COPY[lang].email).fill(`${uniqueUsername('e2e_nadie_')}@example.com`);
        await page.getByLabel(COPY[lang].password, { exact: true }).fill('no-es-esta-123');
        await page.getByRole('button', { name: COPY[lang].login, exact: true }).click();
        const alert = page.getByRole('alert');
        await expect(alert).toBeVisible();
        await expect(alert).toHaveAttribute('data-fx', 'shake');
        await page.waitForTimeout(400);
        await page.screenshot({ path: `${SHOTS}/error-${lang}-${width}.png` });
        await axe0(page);
      });
    }

    test('enlace enviado: el check se dibuja', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.goto('/login');
      await page.getByRole('button', { name: COPY[lang].forgot }).click();
      await page.getByRole('textbox').fill(`${uniqueUsername('e2e_olvido_')}@example.com`);
      await page.getByRole('textbox').press('Enter');
      const check = page.getByTestId('drawn-check');
      await expect(check).toHaveAttribute('data-fx', 'draw');
      await page.waitForTimeout(800);
      await page.screenshot({ path: `${SHOTS}/enlace-${lang}-390.png` });
      await axe0(page);
    });

    test('correo verificado: el check se dibuja', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 900 });
      await page.route('**/auth/verify-email', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: '{"message":"ok"}' }));
      await page.goto(`/verify-email?token=e2e&lang=${lang}`);
      await expect(page.getByTestId('drawn-check')).toHaveAttribute('data-fx', 'draw');
      await page.waitForTimeout(800);
      await page.screenshot({ path: `${SHOTS}/verificado-${lang}-1280.png` });
      await axe0(page);
    });
  });
}

test('alta: cada paso entra desplazándose (es, 390 px)', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  const username = uniqueUsername('e2e_paso_');
  await page.goto('/auth');
  await page.getByLabel('Nombre').fill('Paso');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByLabel('Confirmo que tengo 16 años o más').check();
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();
  const step = page.getByTestId('onboarding-step');
  await expect(step).toHaveAttribute('data-fx', 'slide', { timeout: 15_000 });
  await page.getByRole('button', { name: 'Aprender' }).click();
  // El paso nuevo responde al toque al instante: sin esperar a que el viejo se vaya.
  await expect(page.getByText('Paso 2 de', { exact: false })).toBeVisible({ timeout: 1_000 });
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${SHOTS}/alta-paso2-es-390.png` });
  await axe0(page);
});

test('movimiento reducido: el error no tiembla y el check sale ya dibujado', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/login');
  await page.getByLabel('Correo electrónico').fill(`${uniqueUsername('e2e_rm_')}@example.com`);
  await page.getByLabel('Contraseña', { exact: true }).fill('no-es-esta-123');
  await page.getByRole('button', { name: 'ENTRAR' }).click();
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.getByRole('alert')).not.toHaveAttribute('data-fx', /.+/);

  await page.route('**/auth/verify-email', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: '{"message":"ok"}' }));
  await page.goto('/verify-email?token=e2e');
  await expect(page.getByTestId('drawn-check')).toBeVisible();
  await expect(page.getByTestId('drawn-check')).not.toHaveAttribute('data-fx', /.+/);
});

test('prueba de nivel: un punto por pregunta respondida (es, 390 px)', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  const username = uniqueUsername('e2e_puntos_');
  await page.goto('/auth');
  await page.getByLabel('Nombre').fill('Puntos');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByLabel('Confirmo que tengo 16 años o más').check();
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();
  await completeOnboarding(page, { takeTest: true });
  await page.getByRole('button', { name: 'COMENZAR EXAMEN' }).click();
  await page.getByTestId('placement-option').first().click();
  await expect(page.getByText('Pregunta 2 de 20')).toBeVisible({ timeout: 15_000 });
  const done = page.getByTestId('placement-dots').locator('[data-done]');
  await expect(done).toHaveCount(1);
  await expect(done).toHaveAttribute('data-fx', 'fill');
  // El punto lleno tiene color de verdad: un token inexistente lo dejaría transparente.
  await expect(done).not.toHaveCSS('background-color', 'rgba(0, 0, 0, 0)');
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${SHOTS}/prueba-puntos-es-390.png` });
  await axe0(page);
});
