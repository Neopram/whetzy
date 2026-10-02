import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { registerUser, uniqueUsername, formatViolations, answerCurrentQuestion } from './helpers';

// A plain 4-option MCQ in track01, used to reach the answer-feedback panel
// without booting the Python runtime.
const FORCED_MCQ_ID = 'q010101001';

test.describe('WCAG 2.2 AA — axe-core', () => {
  test('auth screen has zero violations', async ({ page }) => {
    await page.goto('/auth');
    await expect(page.getByRole('heading', { name: /Whetzy/i }).or(page.locator('h1,h2').first())).toBeVisible({ timeout: 10_000 }).catch(() => undefined);

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
      .analyze();

    expect(results.violations, formatViolations(results.violations)).toHaveLength(0);
  });

  // La landing es la página pública: la tabla comparativa llevaba aria-label
  // en <span> sin rol (axe aria-prohibited-attr, 5 nodos, 2026-10-01).
  test('landing has zero violations', async ({ page }) => {
    await page.goto('/landing');
    await expect(page.locator('table').first()).toBeAttached({ timeout: 10_000 });

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
      .analyze();

    expect(results.violations, formatViolations(results.violations)).toHaveLength(0);
  });

  test('home screen has zero violations after login', async ({ page }) => {
    const username = uniqueUsername('e2e_a11y_');
    await registerUser(page, { username, displayName: 'A11y Test' });

    await expect(page.getByRole('button', { name: 'ESTUDIAR AHORA' })).toBeVisible({ timeout: 10_000 });

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
      .analyze();

    expect(results.violations, formatViolations(results.violations)).toHaveLength(0);
  });

  // The three screens below arrived with 16.15. Each paints success green as a
  // glyph or under white text, which 16.12 measured at 2.09:1 on white and
  // 1.88:1 on the green tint — under the 4.5:1 floor. None of them was covered
  // by axe before, so those violations were real and simply unmeasured.

  // Yo y Estadísticas no estaban cubiertas: los dos interruptores de ajustes
  // (modo oscuro, recordatorios) no tenían nombre accesible y nadie lo medía
  // (axe button-name, visto el 2026-10-01).
  test('profile and stats screens have zero violations', async ({ page }) => {
    const username = uniqueUsername('e2e_a11y_profile_');
    await registerUser(page, { username, displayName: 'A11y Profile' });

    await page.getByRole('button', { name: 'Yo', exact: true }).click();
    await expect(page.getByRole('switch').first()).toBeVisible({ timeout: 15_000 });
    const profile = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
      .analyze();
    expect(profile.violations, formatViolations(profile.violations)).toHaveLength(0);

    await page.getByRole('button', { name: 'Estadísticas' }).click();
    await expect(page.getByRole('heading', { name: 'Estadísticas' })).toBeVisible({ timeout: 15_000 });
    const stats = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
      .analyze();
    expect(stats.violations, formatViolations(stats.violations)).toHaveLength(0);
  });

  test('league screen has zero violations', async ({ page }) => {
    const username = uniqueUsername('e2e_a11y_league_');
    await registerUser(page, { username, displayName: 'A11y League' });

    await page.getByRole('button', { name: 'Ranking', exact: true }).click();
    // A brand-new user has no XP this week, so the league renders its empty
    // state (a <p>, no heading) rather than the podium — which is exactly the
    // screen most first-time users see, and the one worth auditing.
    await expect(
      page.locator('[class*="loading_"], [class*="leagueName_"]').first()
    ).toBeVisible({ timeout: 20_000 });

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
      .analyze();

    expect(results.violations, formatViolations(results.violations)).toHaveLength(0);
  });

  test('tracks screen has zero violations', async ({ page }) => {
    const username = uniqueUsername('e2e_a11y_tracks_');
    await registerUser(page, { username, displayName: 'A11y Tracks' });

    await page.getByRole('button', { name: 'Rutas' }).click();
    // The module spine carries the status badges — the green/brand tint pills.
    await expect(page.locator('[class*="moduleHeader_"]').first()).toBeVisible({ timeout: 20_000 });

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
      .analyze();

    expect(results.violations, formatViolations(results.violations)).toHaveLength(0);
  });

  test('quiz answer feedback has zero violations', async ({ page }) => {
    const username = uniqueUsername('e2e_a11y_quiz_');
    await registerUser(page, { username, displayName: 'A11y Quiz' });

    // Force a plain MCQ: the adaptive picker can serve an exec question, and
    // then this spec spends a minute booting Pyodide to audit colours that
    // have nothing to do with it.
    await page.route('**/quiz/start', async (route, request) => {
      const body = JSON.parse((await request.postData()) ?? '{}') as Record<string, unknown>;
      await route.continue({
        postData: JSON.stringify({ ...body, force_question_id: FORCED_MCQ_ID }),
      });
    });

    await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
    // Wait for the card: answerCurrentQuestion counts option buttons to decide
    // which kind of question it is, and counting before the card paints makes
    // it take the exec branch and hunt for a Run button that will never exist.
    await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 20_000 });
    // `.option.correct` is applied to the right answer once the question is
    // answered, whether or not this answer was the right one — so a single
    // click is enough to put the green letter chip and tick on screen.
    await answerCurrentQuestion(page);
    await expect(page.locator('[class*="explanation_"]')).toBeVisible({ timeout: 30_000 });

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
      .analyze();

    expect(results.violations, formatViolations(results.violations)).toHaveLength(0);
  });

  test('legal screen (privacy) has zero violations', async ({ page }) => {
    await page.goto('/privacy');
    await expect(page.locator('h1')).toBeVisible({ timeout: 10_000 });

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
      .analyze();

    expect(results.violations, formatViolations(results.violations)).toHaveLength(0);
  });
});
