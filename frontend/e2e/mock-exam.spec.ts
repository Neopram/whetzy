import { test, expect } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

/**
 * Timed certification mock exam (10.3), end to end against a real server.
 *
 * What this covers that the integration tests do not: the path a learner
 * actually walks. The API tests prove the selection, the clock and the report
 * are right; they say nothing about whether the exam can be reached from the
 * track list, whether the countdown renders, or whether the report's caveats
 * survive into the page. A feature that is correct and unreachable is not
 * shipped.
 *
 * It does NOT prove the session is committed. That difference only appears on
 * Postgres - under SQLite, which this suite and the local tooling use, an
 * uncommitted flush still persists, so removing the commit in the endpoint
 * leaves this test green. The commit is there because `get_db` never commits
 * and every other writing endpoint commits for itself.
 */
test.describe('certification mock exam', () => {
  test('starts a timed exam, submits it and reports per domain', async ({ page }) => {
    const username = uniqueUsername('e2e_mock_');
    // registerUser already clears the onboarding gate for this context.
    await registerUser(page, { username, displayName: 'E2E Mock' });

    // Tracks -> the certification track -> the mock exam entry. No swallowed
    // failures here: if any of these three steps stops working, the mock exam
    // is unreachable and this test must say so.
    await page.getByRole('button', { name: 'Rutas' }).click();
    await page.getByRole('tab', { name: /AWS Cloud Practitioner/ }).click();

    const cta = page.getByRole('button', { name: /Simulacro de examen|Mock exam/ });
    await expect(cta).toBeVisible({ timeout: 10_000 });
    await cta.click();

    // The intro states the cost in time before the clock starts.
    await expect(page.getByText(/65/)).toBeVisible({ timeout: 10_000 });
    await page.getByRole('button', { name: /EMPEZAR SIMULACRO|START MOCK EXAM/ }).click();

    // A question and a running clock. If the attempt had not been committed,
    // this is where it would fail.
    await expect(page.getByRole('radiogroup')).toBeVisible({ timeout: 30_000 });
    const clock = page.getByRole('timer');
    await expect(clock).toBeVisible();
    await expect(clock).toHaveText(/^\d{2}:\d{2}$/);

    // The counter must say 65, not some other number: the whole point is that
    // the mock mirrors the real exam's length.
    await expect(page.getByText(/de 65|of 65/)).toBeVisible();

    // Answer the first three, then submit with the rest blank - blanks are
    // scored as incorrect, exactly as the real exam does.
    for (let i = 0; i < 3; i++) {
      await page.getByRole('radio').first().click();
      await page.getByRole('button', { name: /^(Siguiente|Next)$/ }).click();
    }

    // Jump to the end so the submit button is the one on screen.
    for (let i = 3; i < 64; i++) {
      await page.getByRole('button', { name: /^(Siguiente|Next)$/ }).click();
    }
    await page.getByRole('button', { name: /^(ENTREGAR|SUBMIT)$/ }).click();

    // The report: a raw percentage, four domains, and no invented scaled score.
    await expect(page.getByText(/Resultado del simulacro|Mock exam result/)).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByText(/de 65 aciertos|of 65 correct/)).toBeVisible();

    const domains = page.getByRole('progressbar');
    await expect(domains).toHaveCount(4);

    // The scoring note must be present: it is what stops the raw percentage
    // from being read as a predicted exam score.
    await expect(page.getByText(/100 a 1\.000|100 to 1,000/)).toBeVisible();
  });
});
