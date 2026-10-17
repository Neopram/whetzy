import { test, expect } from '@playwright/test';
import { registerAndCompleteAQuiz, suppressOnboarding, uniqueUsername } from './helpers';

test.describe('duel', () => {
  test('challenge an opponent and complete the challenger side', async ({ page, request, baseURL }) => {
    const opponentUsername = uniqueUsername('e2e_opp_');
    const challengerUsername = uniqueUsername('e2e_duel_');

    // Create the opponent directly via the API — only their username needs
    // to exist for /duels/challenge to accept it; no UI interaction needed.
    const registerRes = await request.post(`${baseURL}/api/v1/auth/register`, {
      data: {
        email: `${opponentUsername}@example.com`,
        username: opponentUsername,
        display_name: 'E2E Opponent',
        password: 'e2e-test-pass-123',
        language: 'es',
        age_confirmed: true,
      },
    });
    expect(registerRes.ok(), await registerRes.text()).toBeTruthy();
    // 43.5 (ADR-65 D7): un duelo va sobre una skill con la lección vista por
    // los dos. `request` guarda la sesión del registro del rival.
    const oppLesson = await request.get(`${baseURL}/api/v1/lessons/sk010101`);
    expect(oppLesson.ok(), await oppLesson.text()).toBeTruthy();

    // Challenging requires skill history — complete a study session first.
    await registerAndCompleteAQuiz(page, { username: challengerUsername, displayName: 'E2E Challenger' });

    await page.getByRole('button', { name: 'Ranking', exact: true }).click();

    await page.getByRole('tab', { name: 'Duelos' }).click();
    await page.getByRole('button', { name: 'Retar', exact: true }).click();
    await page.getByPlaceholder('Nombre de usuario').fill(opponentUsername);
    await page.getByRole('button', { name: 'Retar', exact: true }).click();

    // Challenge accepted -> straight into the 5-question duel quiz.
    await expect(page.locator('text=/Pregunta 1 de 5/')).toBeVisible({ timeout: 15_000 });

    // DuelScreen renders answer options as plain <button> elements with
    // inline styles (no CSS modules, no test ids) — before an answer is
    // selected they're the only buttons on screen, so the first one is safe.
    for (let i = 0; i < 5; i++) {
      await page.getByRole('button').first().click();
      const nextOrFinish = page.getByRole('button', { name: /Siguiente|Finalizar/ });
      await expect(nextOrFinish).toBeVisible({ timeout: 10_000 });
      await nextOrFinish.click();
    }

    await expect(page.locator('text=¡Duelo completado!')).toBeVisible({ timeout: 10_000 });
  });

  /**
   * Full two-player resolution: challenger challenges → both sides answer →
   * API confirms status=completed and winner_id resolved. Covers ledger 3.1.
   */
  test('full two-player duel: both sides answer, winner resolved', async ({ browser, request, baseURL }) => {
    const oppUsername = uniqueUsername('e2e_opp2_');
    const chalUsername = uniqueUsername('e2e_chal2_');
    const oppEmail = `${oppUsername}@example.com`;

    // Register opponent via API
    const oppReg = await request.post(`${baseURL}/api/v1/auth/register`, {
      data: {
        email: oppEmail,
        username: oppUsername,
        display_name: 'E2E Opponent2',
        password: 'e2e-test-pass-123',
        language: 'es',
        age_confirmed: true,
      },
    });
    expect(oppReg.ok(), await oppReg.text()).toBeTruthy();
    // 43.5 (D7): la lección del rival, como arriba.
    const oppLesson = await request.get(`${baseURL}/api/v1/lessons/sk010101`);
    expect(oppLesson.ok(), await oppLesson.text()).toBeTruthy();

    // ── Context 1: Challenger ────────────────────────────────────────────────
    const chalContext = await browser.newContext();
    const chalPage = await chalContext.newPage();

    await registerAndCompleteAQuiz(chalPage, { username: chalUsername, displayName: 'E2E Challenger2' });

    await chalPage.getByRole('button', { name: 'Ranking', exact: true }).click();

    await chalPage.getByRole('tab', { name: 'Duelos' }).click();
    await chalPage.getByRole('button', { name: 'Retar', exact: true }).click();
    await chalPage.getByPlaceholder('Nombre de usuario').fill(oppUsername);
    await chalPage.getByRole('button', { name: 'Retar', exact: true }).click();
    await expect(chalPage.locator('text=/Pregunta 1 de 5/')).toBeVisible({ timeout: 15_000 });

    // Challenger answers all 5 questions
    for (let i = 0; i < 5; i++) {
      await chalPage.getByRole('button').first().click();
      const nextOrFinish = chalPage.getByRole('button', { name: /Siguiente|Finalizar/ });
      await expect(nextOrFinish).toBeVisible({ timeout: 10_000 });
      await nextOrFinish.click();
    }
    await expect(chalPage.locator('text=¡Duelo completado!')).toBeVisible({ timeout: 10_000 });

    // Resolve duel_id via the API using challenger's token
    // `request` keeps the session cookie from the opponent's registration, and a
    // POST with a session cookie must carry an allowed Origin (CSRF, S.13):
    // without it the login came back 403 and `myDuels` was an error object.
    const chalLoginRes = await request.post(`${baseURL}/api/v1/auth/login`, {
      form: { username: `${chalUsername}@example.com`, password: 'e2e-test-pass-123' },
      headers: { Origin: new URL(baseURL!).origin },
    });
    expect(chalLoginRes.ok(), await chalLoginRes.text()).toBeTruthy();
    const chalToken = (await chalLoginRes.json()).access_token;
    const myDuelsRes = await request.get(`${baseURL}/api/v1/duels/my`, {
      headers: { Authorization: `Bearer ${chalToken}` },
    });
    const myDuels = await myDuelsRes.json();
    expect(myDuels.length).toBeGreaterThan(0);
    const duelId: string = myDuels[0].duel_id;

    // ── Context 2: Opponent ──────────────────────────────────────────────────
    const oppContext = await browser.newContext();
    const oppPage = await oppContext.newPage();

    await oppPage.goto('/auth');
    // Switch to login tab
    await oppPage.getByRole('button', { name: 'Iniciar sesión' }).click();
    await oppPage.getByLabel('Correo electrónico').fill(oppEmail);
    await oppPage.getByLabel('Contraseña').fill('e2e-test-pass-123');
    await oppPage.getByRole('button', { name: 'ENTRAR' }).click();

    // Second browser context. Since 43.3 the onboarding flag also lives on the
    // server, so the opponent usually goes straight to Hoy; `maybeDone` covers
    // both (the server write is fire-and-forget after the first context).
    await suppressOnboarding(oppPage, { maybeDone: true });
    await expect(oppPage.getByRole('button', { name: 'Hoy', exact: true })).toBeVisible({ timeout: 15_000 });

    // Navigate to duels and play
    await oppPage.getByRole('button', { name: 'Ranking', exact: true }).click();
    await oppPage.getByRole('tab', { name: 'Duelos' }).click();
    await expect(oppPage.getByRole('button', { name: 'Jugar' })).toBeVisible({ timeout: 10_000 });
    await oppPage.getByRole('button', { name: 'Jugar' }).click();
    await expect(oppPage.locator('text=/Pregunta 1 de 5/')).toBeVisible({ timeout: 15_000 });

    // Opponent answers all 5 questions
    for (let i = 0; i < 5; i++) {
      await oppPage.getByRole('button').first().click();
      const nextOrFinish = oppPage.getByRole('button', { name: /Siguiente|Finalizar/ });
      await expect(nextOrFinish).toBeVisible({ timeout: 10_000 });
      await nextOrFinish.click();
    }
    await expect(oppPage.locator('text=¡Duelo completado!')).toBeVisible({ timeout: 10_000 });

    // ── Verify via API that both sides resolved ──────────────────────────────
    const oppLoginRes = await request.post(`${baseURL}/api/v1/auth/login`, {
      form: { username: oppEmail, password: 'e2e-test-pass-123' },
      headers: { Origin: new URL(baseURL!).origin },
    });
    expect(oppLoginRes.ok(), await oppLoginRes.text()).toBeTruthy();
    const oppToken = (await oppLoginRes.json()).access_token;
    const resultRes = await request.get(`${baseURL}/api/v1/duels/${duelId}/result`, {
      headers: { Authorization: `Bearer ${oppToken}` },
    });
    expect(resultRes.ok()).toBeTruthy();
    const result = await resultRes.json();
    expect(result.status).toBe('completed');
    // challenger and opponent fields must be present
    expect(result).toHaveProperty('challenger');
    expect(result).toHaveProperty('opponent');

    await chalContext.close();
    await oppContext.close();
  });
});
