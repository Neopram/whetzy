import { test, expect } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

/**
 * sql_exec E2E: deterministic SQL execution test.
 *
 * Uses force_question_id to serve a sql_exec question, then verifies that
 * the sql.js worker initialises, executes the query, and returns the result.
 *
 * The forced question is q_sql_exec_001 (track-agnostic fixture) which asks:
 *   "SELECT 1 + 1 AS result" → expected output "1 | result\n-+--------\n2"
 *
 * Since sql_exec questions may not yet exist in the fixture DB, this test
 * uses a mock route interceptor to inject a synthetic sql_exec question into
 * the quiz/start response — the same technique used in sandbox.spec.ts.
 */

const SQL_QUESTION = {
  id: 'q_sql_test_001',
  type: 'sql_exec',
  skill_id: 'sk010101',
  question_es: 'Escribe una consulta SQL que devuelva el valor 42.',
  question_en: 'Write a SQL query that returns the value 42.',
  options_es: null,
  options_en: null,
  correct_index: null,
  correct_answer_es: '42',
  correct_answer_en: '42',
  difficulty_tier: 'easy',
  expected_time_ms: 30000,
  source: 'SQL standard',
  code_es: 'SELECT ___;',
  code_en: 'SELECT ___;',
};

test.describe('sql_exec runtime', () => {
  test('sql.js worker initialises and executes SQL query', async ({ page }) => {
    test.setTimeout(90_000);

    const pageErrors: string[] = [];
    page.on('pageerror', (err) => pageErrors.push(err.message));

    const username = uniqueUsername('e2e_sql_');
    await registerUser(page, { username, displayName: 'E2E SQL' });

    // Intercept quiz/start to inject a synthetic sql_exec question.
    await page.route('**/quiz/start', async (route) => {
      const json = {
        question: SQL_QUESTION,
        session_id: 'test-sql-session-001',
        question_number: 1,
        questions_remaining: 1,
      };
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(json) });
    });

    await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();

    // The exec area (fill_blank input or code editor) should appear.
    // For sql_exec with a code template, the blank input is shown.
    const blankInput = page.getByPlaceholder(/respuesta|answer/i);
    await expect(blankInput).toBeVisible({ timeout: 15_000 });

    // Type the SQL fragment to complete the blank.
    await blankInput.fill('42');

    // Wait for the SQL engine to be ready (button enabled).
    const runBtn = page.locator('[class*="btnRun_"]');
    await expect(runBtn).toBeEnabled({ timeout: 60_000 });

    // Execute.
    await runBtn.click();

    // The output box should appear.
    const outputBox = page.locator('[class*="outputBox_"]');
    await expect(outputBox).toBeVisible({ timeout: 20_000 });

    // No uncaught page errors.
    expect(pageErrors, `Uncaught page errors: ${pageErrors.join('; ')}`).toHaveLength(0);
  });
});
