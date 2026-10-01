import { test, expect } from '@playwright/test';
import { registerUser, answerCurrentQuestion, markLessonSeen, uniqueUsername } from './helpers';

test.describe('quiz', () => {
  test('completes a 10-question study session end to end', async ({ page }) => {
    const username = uniqueUsername('e2e_quiz_');
    await registerUser(page, { username, displayName: 'E2E Quiz' });
    // 32.4 gates "study" mode on having viewed the skill's lesson first.
    await markLessonSeen(page);

    await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
    await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });

    // Ported from the deleted root e2e/ suite: an MCQ renders with at least 2
    // selectable options (a question can also be exec-type, which has no
    // options_ list — the guard keeps this a real assertion, not a vacuous one).
    const options = page.locator('[class*="options_"] button');
    if (await options.count() > 0) {
      expect(await options.count()).toBeGreaterThanOrEqual(2);
    }

    for (let i = 0; i < 10; i++) {
      await answerCurrentQuestion(page);

      // Ported: the advance button reads "SIGUIENTE" until the final question,
      // where QuizScreen.tsx switches its label to "VER RESULTADOS".
      const nextBtn = page.getByRole('button', { name: /^(SIGUIENTE|VER RESULTADOS)$/ });
      await expect(nextBtn).toBeVisible({ timeout: 10_000 });
      await nextBtn.click();
    }

    await expect(page.locator('[class*="summaryGrade_"]')).toBeVisible({ timeout: 10_000 });
    // Ported: the summary must show the accuracy percentage, not just the grade letter.
    await expect(page.getByText(/% de precisión/i)).toBeVisible();

    await page.locator('[class*="btnStudy_"]').click();
    await expect(page.getByRole('button', { name: 'Inicio' })).toBeVisible();
  });
});
