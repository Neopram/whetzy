import { test, expect } from '@playwright/test';
import { answerCurrentQuestion, registerUser, uniqueUsername } from './helpers';

/**
 * NOTE on scope: the offline queue (services/offlineQueue.ts, IndexedDB) and
 * useOfflineSync are built and unit-tested (Q.9), but nothing in QuizScreen
 * ever calls `enqueue()` — its answer-submit catch block only shows a toast.
 * More fundamentally, QuizScreen gets the *next* question from the server's
 * answer response (`feedback.next_question`), so there's no local queue of
 * upcoming questions to fall back to while offline — true "answer offline,
 * sync later" needs question prefetching that doesn't exist yet. That's a
 * real feature gap (tracked as 3.2 in the ledger), not something to fake
 * here. This spec verifies what the app actually does today: going offline
 * mid-quiz fails the answer request gracefully (an error toast, no crash,
 * no stuck UI) rather than losing the user's place or throwing.
 */
test.describe('offline', () => {
  test('going offline during a quiz answer fails gracefully, no crash', async ({ page, context }) => {
    const username = uniqueUsername('e2e_offline_');
    await registerUser(page, { username, displayName: 'E2E Offline' });

    await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
    await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });

    await context.setOffline(true);
    try {
      const options = page.locator('[class*="options_"] button');
      if (await options.count() > 0) {
        await options.first().click();
      } else {
        // Exec-type question drawn: no network call happens until "Run", and
        // Pyodide itself needs network to fetch its WASM runtime on first
        // load, so there's nothing meaningful to assert offline here.
        test.skip(true, 'exec-type question drawn — Pyodide needs network for first load');
      }

      // The answer POST fails (offline, so fetch itself throws); app must not
      // crash and must not get stuck showing a stale "submitting" state
      // forever. The error toast text is the browser's own fetch error
      // message ("Failed to fetch" in Chromium) — assert on the toast role
      // rather than that exact wording, which isn't part of the app's contract.
      await expect(page.getByRole('status')).toBeVisible({ timeout: 10_000 });
      await expect(page.locator('[class*="option_"]').first()).toBeEnabled({ timeout: 5_000 });
    } finally {
      await context.setOffline(false);
    }

    // Recovery: back online, the same answer now succeeds normally.
    await answerCurrentQuestion(page);
  });
});
