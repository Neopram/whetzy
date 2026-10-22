import { test, expect, type Page } from '@playwright/test';
import { answerCurrentQuestion, uniqueUsername } from './helpers';

/**
 * 43.8 (ADR-65, anexo «Flujo del alumno» §6): la puerta «lista para pruebas».
 *
 * El recorrido completo de un alumno nuevo, contra el backend real:
 * registro → onboarding (Ciberseguridad) → prueba de nivel de 20 → Hoy de
 * Ciberseguridad → lección → práctica → cambiar a Python → volver a
 * Ciberseguridad sin perder el progreso → recargar sin perder la sesión.
 *
 * Corre en dos proyectos de `playwright.config.ts`:
 * - `chromium`: frontend y API en el mismo sitio (proxy de Vite);
 * - `entre-sitios`: la API en otro sitio y las cookies de terceros bloqueadas,
 *   como Safari en iPhone con whetzy.com y la API en Railway (43.1/43.1b).
 */

async function register(page: Page, username: string) {
  await page.goto('/auth');
  await page.getByLabel('Nombre').fill('Alumno Puerta');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByLabel('Confirmo que tengo 16 años o más').check();
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();
}

async function placementOfTwenty(page: Page) {
  await page.getByRole('button', { name: 'COMENZAR EXAMEN' }).click({ timeout: 20_000 });
  await expect(page.getByText('Pregunta 1 de 20')).toBeVisible({ timeout: 20_000 });
  const result = page.getByRole('heading', { name: /Tu nivel estimado/ });
  const option = page.getByTestId('placement-option').first();
  const deadline = Date.now() + 150_000;
  while (Date.now() < deadline && !(await result.isVisible())) {
    if ((await option.isVisible().catch(() => false)) && (await option.isEnabled().catch(() => false))) {
      await option.click().catch(() => undefined);
    }
    await page.waitForTimeout(200);
  }
  await expect(result).toBeVisible();
  await page.getByRole('button', { name: 'IR A HOY' }).click();
}

async function changeTrack(page: Page, name: RegExp) {
  await page.getByTestId('home-active-track').getByRole('button', { name: 'Cambiar' }).click();
  await page.getByRole('button', { name }).first().click();
  const saved = page.waitForResponse(
    (r) => r.url().endsWith('/auth/me') && r.request().method() === 'PATCH' && r.ok(),
  );
  await page.getByRole('button', { name: 'Hacer esta mi ruta' }).click();
  await saved;
  await page.getByRole('button', { name: 'Hoy', exact: true }).click();
}

test('alumno nuevo: del registro a practicar, cambiar de ruta y volver sin perder nada', async ({ page }) => {
  test.setTimeout(300_000);
  // Orden de las respuestas de sesión: el criterio de §6 es «POST /auth/register
  // 201 seguido de GET /auth/me 200». Antes de registrarse, /auth/me da 401 (no
  // hay sesión todavía) y eso es correcto.
  const auth: string[] = [];
  page.on('response', (r) => {
    const path = new URL(r.url()).pathname;
    if (!path.startsWith('/api/v1/auth/')) return;
    // La sonda del puente (43.1, `bridgeIfCookiesBlocked`) pregunta /auth/me solo
    // con la cookie, sin Authorization: su 401 es lo que activa el puente.
    const probe = path === '/api/v1/auth/me' && !r.request().headers()['authorization'];
    auth.push(`${r.request().method()} ${path} ${r.status()}${probe ? ' (sin token)' : ''}`);
  });

  await register(page, uniqueUsername('e2e_alumno_'));

  // Onboarding: aprender → Ciberseguridad → empiezo de cero → hacer la prueba.
  const onboarding = page.getByTestId('onboarding');
  await expect(onboarding).toBeVisible({ timeout: 15_000 });
  await onboarding.getByRole('button', { name: 'Aprender', exact: true }).click();
  await onboarding.getByTestId('track-track13').click();
  await onboarding.getByRole('button', { name: 'Empiezo de cero' }).click();
  await onboarding.getByRole('button', { name: 'Hacer la prueba' }).click();

  await placementOfTwenty(page);

  // Hoy de Ciberseguridad, con la siguiente lección pendiente.
  const header = page.getByTestId('home-active-track');
  await expect(header).toContainText('Tu ruta: Ciberseguridad', { timeout: 15_000 });
  const next = page.getByTestId('home-next');
  await expect(next).toContainText('Lección:');
  const firstNext = (await next.innerText()).trim();

  // Lección → «Practicar ahora» → la práctica entera.
  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
  await expect(page.getByRole('button', { name: 'Cerrar' })).toBeVisible({ timeout: 15_000 });
  const practice = page.getByRole('button', { name: 'Practicar ahora' });
  for (let i = 0; i < 15 && !(await practice.isVisible()); i++) {
    await page.getByRole('button', { name: /Siguiente/ }).click();
  }
  await practice.click();
  await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });
  for (let i = 0; i < 10; i++) {
    await answerCurrentQuestion(page);
    await page.getByRole('button', { name: /^(SIGUIENTE|VER RESULTADOS)$/ }).click();
  }
  await expect(page.locator('[class*="summaryGrade_"]')).toBeVisible({ timeout: 10_000 });
  await page.getByRole('button', { name: 'CONTINUAR' }).click();

  // Cambiar a Python y volver: la ruta cambia, el progreso de Ciberseguridad no.
  await expect(header).toContainText('Tu ruta: Ciberseguridad', { timeout: 15_000 });
  await changeTrack(page, /Python Básico/);
  await expect(header).toContainText('Tu ruta: Python Básico', { timeout: 15_000 });
  await changeTrack(page, /Ciberseguridad/);
  await expect(header).toContainText('Tu ruta: Ciberseguridad', { timeout: 15_000 });
  // La lección vista ya no es la siguiente.
  await expect(next).not.toHaveText(firstNext);
  const nextAfter = (await next.innerText()).trim();

  // Recargar: sigue dentro (sin volver a la portada), en la misma ruta y el mismo punto.
  await page.reload();
  await expect(page.getByRole('button', { name: 'Hoy', exact: true })).toBeVisible({ timeout: 15_000 });
  await expect(header).toContainText('Tu ruta: Ciberseguridad', { timeout: 15_000 });
  await expect(next).toHaveText(nextAfter);

  // Desde el registro, ningún 401 de sesión (el «GET /auth/me 401» de §6).
  const registered = auth.indexOf('POST /api/v1/auth/register 201');
  expect(registered, auth.join('\n')).toBeGreaterThanOrEqual(0);
  const after = auth.slice(registered + 1);
  const log = auth.join('\n');
  // Con cookies de terceros bloqueadas, la sonda sin token da 401 una vez (y en
  // producción también saldrá en los logs de Railway hasta H.61); nada más.
  const probes401 = after.filter((a) => a === 'GET /api/v1/auth/me 401 (sin token)');
  expect(probes401.length, log).toBeLessThanOrEqual(1);
  const rest = after.filter((a) => a !== 'GET /api/v1/auth/me 401 (sin token)');
  expect(rest.find((a) => a.startsWith('GET /api/v1/auth/me')), log).toMatch(/^GET \/api\/v1\/auth\/me 200/);
  expect(rest.filter((a) => / 401/.test(a)), log).toEqual([]);
});
