import { expect, test } from '@playwright/test';
import { loginUser } from './helpers';

// MCQ option buttons have text that starts with a single letter: "A…", "B…" etc.
// During the quiz screen the BottomNav is hidden (App.tsx guards it), so these
// are the only buttons whose text begins with A–D.
const OPTION_LOCATOR = (page: Parameters<typeof page.getByRole>[0]) =>
  (page as import('@playwright/test').Page)
    .getByRole('button')
    .filter({ hasText: /^[A-D]/ });

test.describe('Quiz', () => {
  test.beforeEach(async ({ page }) => {
    await loginUser(page, process.env.E2E_EMAIL!, process.env.E2E_PASSWORD!);
  });

  test('start quiz → question appears with ≥2 answer options', async ({ page }) => {
    // The HomeScreen "EMPEZAR A APRENDER" button triggers startQuiz('study', 10)
    await page.getByRole('button', { name: /empezar a aprender/i }).click();

    // Wait for quiz to load — answer options appear once the API returns a question
    const options = page.getByRole('button').filter({ hasText: /^[A-D]/ });
    await expect(options.first()).toBeVisible({ timeout: 20_000 });

    const count = await options.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('answer a question → feedback panel or next-question button appears', async ({ page }) => {
    await page.getByRole('button', { name: /empezar a aprender/i }).click();

    const options = page.getByRole('button').filter({ hasText: /^[A-D]/ });
    await expect(options.first()).toBeVisible({ timeout: 20_000 });

    // Click the first available option
    await options.first().click();

    // QuizScreen shows a "SIGUIENTE" or "VER RESULTADOS" button after answer
    await expect(
      page.getByRole('button', { name: /siguiente|ver resultados/i }),
    ).toBeVisible({ timeout: 15_000 });
  });

  test('complete quiz session → summary stats visible', async ({ page }) => {
    test.setTimeout(120_000); // 10 questions × up to ~8 s each = budget

    // Use the BottomNav Quiz button to start (label = "Quiz")
    await page.getByRole('button', { name: /^quiz$/i }).click();

    // Answer questions until the summary appears or we exceed 10 iterations
    for (let i = 0; i < 10; i++) {
      const options = page.getByRole('button').filter({ hasText: /^[A-D]/ });

      // If options are no longer visible the quiz ended early — break out
      const optionsVisible = await options.first().isVisible({ timeout: 20_000 }).catch(() => false);
      if (!optionsVisible) break;

      await options.first().click();

      const nextBtn = page.getByRole('button', { name: /siguiente|ver resultados/i });
      await expect(nextBtn).toBeVisible({ timeout: 15_000 });

      const btnText = await nextBtn.innerText();
      await nextBtn.click();

      if (/ver resultados/i.test(btnText)) break;
    }

    // SessionSummary renders accuracy as "{n}% de precisión"
    await expect(page.getByText(/de precisión|accuracy/i)).toBeVisible({
      timeout: 15_000,
    });
  });
});
