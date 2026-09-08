import { test, expect } from '@playwright/test';
import { registerAndCompleteAQuiz, uniqueUsername } from './helpers';

/**
 * The current UI only supports the *challenger's* side of a duel: `joinDuel`
 * (DuelScreen.tsx) is a stub that just toasts "coming soon" — an opponent
 * cannot yet answer through the browser. Full two-user resolution is tracked
 * separately as ledger task 3.1, gated on that join flow being built. This
 * spec covers what's actually implemented today: challenging an existing
 * user and playing the challenger's 5 questions.
 */
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
      },
    });
    expect(registerRes.ok()).toBeTruthy();

    // Challenging requires skill history — complete a study session first.
    await registerAndCompleteAQuiz(page, { username: challengerUsername, displayName: 'E2E Challenger' });

    await page.getByRole('button', { name: 'Duelos' }).click();
    await page.getByRole('button', { name: '⚔️ Retar' }).click();
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
});
