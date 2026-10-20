import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerAndCompleteAQuiz, registerUser, suppressOnboarding, uniqueUsername } from './helpers';

/**
 * 46.15 bloque C (docs/PLAN_UI_AVANZADA.md §7.5), contra el backend real:
 * - Examen final: el reloj late una vez al entrar en los 5 últimos minutos y el
 *   veredicto del servidor entra con efecto. Para no esperar 70 minutos se
 *   adelanta solo `expires_at` en la respuesta de empezar (a 5 min + 3 s); la
 *   pantalla cuenta desde ahí. Con el reloj falso de Playwright las entradas de
 *   framer se quedaban a medias: capturas vacías y un axe con colores mezclados.
 * - Duelo de dos jugadores: quien termina segundo recibe el resultado del
 *   servidor y el desenlace entra con efecto.
 */
const SHOTS = '../docs/ui-snapshots/46.15c';

async function axe0(page: Page) {
  const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  expect(r.violations, formatViolations(r.violations)).toHaveLength(0);
}

async function startTrackFinal(page: Page) {
  await page.route('**/exams/track/*/start', async (route) => {
    const res = await route.fetch();
    const body = await res.json();
    body.expires_at = new Date(Date.now() + 303_000).toISOString();
    await route.fulfill({ response: res, json: body });
  });
  await registerUser(page, { username: uniqueUsername('e2e_reloj_'), displayName: 'Reloj' });
  await page.getByRole('button', { name: 'Rutas', exact: true }).click();
  await page.getByRole('button', { name: /Examen final del curso/ }).click();
  await page.getByRole('button', { name: /EMPEZAR EXAMEN/ }).click();
  await expect(page.getByRole('radiogroup')).toBeVisible({ timeout: 30_000 });
}

for (const width of [390, 1280]) {
  test(`examen final: el reloj late a 5 minutos y el veredicto entra (es, ${width} px)`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await startTrackFinal(page);
    const clock = page.getByRole('timer');
    await expect(clock).not.toHaveAttribute('data-fx', /.+/);
    await expect(clock).toHaveAttribute('data-fx', 'urgent', { timeout: 10_000 });
    await page.waitForTimeout(600); // el latido ya terminó: axe ve el color final
    await page.screenshot({ path: `${SHOTS}/reloj-urgente-es-${width}.png` });
    await axe0(page);

    // Entregar con todo en blanco: la cuadrícula lleva a la última pregunta.
    await page.getByText(/Respondidas/).click();
    await page.getByRole('button', { name: /^Pregunta \d+: sin responder$/ }).last().click();
    await page.getByRole('button', { name: /^ENTREGAR$/ }).click();
    await page.getByRole('alertdialog').getByRole('button', { name: /Entregar igualmente/ }).click();
    const verdict = page.getByRole('heading', { name: 'No aprobado' });
    await expect(verdict).toBeVisible({ timeout: 30_000 });
    await expect(verdict).toHaveAttribute('data-fx', 'reveal');
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(600);
    await expect(verdict).toBeInViewport();
    await page.screenshot({ path: `${SHOTS}/veredicto-es-${width}.png` });
    await axe0(page);
  });
}

test('examen final con movimiento reducido: el reloj no late (el color y el texto avisan)', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await startTrackFinal(page);
  const clock = page.getByRole('timer');
  await expect(clock).toHaveClass(/clockUrgent/, { timeout: 10_000 });
  await expect(clock).not.toHaveAttribute('data-fx', /.+/);
});

test('duelo: quien termina segundo ve el desenlace del servidor entrar', async ({ browser, request, baseURL }) => {
  const oppUsername = uniqueUsername('e2e_opp46_');
  const oppEmail = `${oppUsername}@example.com`;
  const reg = await request.post(`${baseURL}/api/v1/auth/register`, {
    data: {
      email: oppEmail, username: oppUsername, display_name: 'Rival 46', password: 'e2e-test-pass-123',
      language: 'es', age_confirmed: true,
    },
  });
  expect(reg.ok(), await reg.text()).toBeTruthy();
  expect((await request.get(`${baseURL}/api/v1/lessons/sk010101`)).ok()).toBeTruthy();

  const chalContext = await browser.newContext();
  const chal = await chalContext.newPage();
  await registerAndCompleteAQuiz(chal, { username: uniqueUsername('e2e_chal46_'), displayName: 'Retador 46' });
  await chal.getByRole('button', { name: 'Ranking', exact: true }).click();
  await chal.getByRole('tab', { name: 'Duelos' }).click();
  await chal.getByRole('button', { name: 'Retar', exact: true }).click();
  await chal.getByPlaceholder('Nombre de usuario').fill(oppUsername);
  await chal.getByRole('button', { name: 'Retar', exact: true }).click();
  for (let i = 0; i < 5; i++) {
    await chal.getByTestId('duel-option').first().click();
    await chal.getByRole('button', { name: /Siguiente|Finalizar/ }).click();
  }
  // Primero en terminar: aún no hay resultado, así que no hay desenlace.
  await expect(chal.getByText(/Cuando tu oponente termine/)).toBeVisible({ timeout: 10_000 });

  const oppContext = await browser.newContext();
  const opp = await oppContext.newPage();
  await opp.setViewportSize({ width: 390, height: 900 });
  await opp.goto('/auth');
  await opp.getByRole('button', { name: 'Iniciar sesión' }).click();
  await opp.getByLabel('Correo electrónico').fill(oppEmail);
  await opp.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await opp.getByRole('button', { name: 'ENTRAR' }).click();
  await suppressOnboarding(opp, { maybeDone: true });
  await opp.getByRole('button', { name: 'Ranking', exact: true }).click();
  await opp.getByRole('tab', { name: 'Duelos' }).click();
  await opp.getByRole('button', { name: 'Jugar' }).click();
  for (let i = 0; i < 5; i++) {
    await opp.getByTestId('duel-option').first().click();
    await opp.getByRole('button', { name: /Siguiente|Finalizar/ }).click();
  }
  const outcome = opp.getByText(/^(¡Ganaste!|Perdiste|Empate)$/);
  await expect(outcome).toBeVisible({ timeout: 15_000 });
  await expect(outcome).toHaveAttribute('data-fx', 'reveal');
  await opp.waitForTimeout(500);
  await opp.screenshot({ path: `${SHOTS}/duelo-desenlace-es-390.png` });
  await axe0(opp);

  await chalContext.close();
  await oppContext.close();
});
