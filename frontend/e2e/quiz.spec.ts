import { test } from '@playwright/test';
import { registerAndCompleteAQuiz, uniqueUsername } from './helpers';

test.describe('quiz', () => {
  test('completes a 10-question study session end to end', async ({ page }) => {
    const username = uniqueUsername('e2e_quiz_');
    await registerAndCompleteAQuiz(page, { username, displayName: 'E2E Quiz' });
  });
});
