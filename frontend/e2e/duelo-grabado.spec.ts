import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerAndCompleteAQuiz, suppressOnboarding, uniqueUsername } from './helpers';

/**
 * Duelo, partida grabada, contra el backend real con dos cuentas: quien juega
 * primero no ve nada del rival (aún no ha jugado); quien juega segundo ve, tras
 * contestar cada pregunta, si el otro la acertó y en cuánto tiempo. Los datos
 * son los que el servidor guardó de la partida del primero.
 */
const SHOTS = '../docs/ui-snapshots/duelo-grabado';

async function axe0(page: Page) {
  const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  expect(r.violations, formatViolations(r.violations)).toHaveLength(0);
}

test('duelo: quien juega segundo ve la partida grabada del rival, pregunta a pregunta', async ({ browser, request, baseURL }) => {
  test.setTimeout(120_000);
  const oppUsername = uniqueUsername('e2e_grab_opp_');
  const oppEmail = `${oppUsername}@example.com`;
  const reg = await request.post(`${baseURL}/api/v1/auth/register`, {
    data: {
      email: oppEmail, username: oppUsername, display_name: 'Rival Grabado', password: 'e2e-test-pass-123',
      language: 'es', age_confirmed: true,
    },
  });
  expect(reg.ok(), await reg.text()).toBeTruthy();
  expect((await request.get(`${baseURL}/api/v1/lessons/sk010101`)).ok()).toBeTruthy();

  const chalContext = await browser.newContext();
  const chal = await chalContext.newPage();
  const chalUsername = uniqueUsername('e2e_grab_chal_');
  await registerAndCompleteAQuiz(chal, { username: chalUsername, displayName: 'Retador Grabado' });
  await chal.getByRole('button', { name: 'Ranking', exact: true }).click();
  await chal.getByRole('tab', { name: 'Duelos' }).click();
  await chal.getByRole('button', { name: 'Retar', exact: true }).click();
  await chal.getByPlaceholder('Nombre de usuario').fill(oppUsername);
  await chal.getByRole('button', { name: 'Retar', exact: true }).click();
  for (let i = 0; i < 5; i++) {
    // Un tiempo de persona, no de robot: el rival lo verá luego en segundos.
    await chal.waitForTimeout(1_300);
    await chal.getByTestId('duel-option').first().click();
    const next = chal.getByRole('button', { name: /Siguiente|Finalizar/ });
    await expect(next).toBeVisible();
    // Primero en jugar: no hay partida del rival que enseñar.
    await expect(chal.getByTestId('duel-rival')).toHaveCount(0);
    await next.click();
  }
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
    // Antes de contestar, nada del rival: verlo antes sería una pista.
    await expect(opp.getByTestId('duel-option').first()).toBeEnabled();
    await expect(opp.getByTestId('duel-rival')).toHaveCount(0);
    await opp.getByTestId('duel-option').first().click();
    const rival = opp.getByTestId('duel-rival');
    await expect(rival).toHaveText(new RegExp(`${chalUsername} (acertó esta en |falló esta \\()[1-9][\\d,]* s`), { timeout: 10_000 });
    if (i === 0) {
      await opp.screenshot({ path: `${SHOTS}/rival-por-pregunta-es-390.png` });
      await axe0(opp);
    }
    await opp.getByRole('button', { name: /Siguiente|Finalizar/ }).click();
  }
  await expect(opp.getByText(/^(¡Ganaste!|Perdiste|Empate)$/)).toBeVisible({ timeout: 15_000 });

  await chalContext.close();
  await oppContext.close();
});
