import { expect, test, type Page } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

/**
 * Offline behaviour of the quiz (ledger 3.2).
 *
 * This spec used to document the opposite contract — "nothing in QuizScreen ever
 * calls enqueue(), it only shows a toast" — and asserted that the options stayed
 * clickable after a failed answer. 3.2 then implemented the real thing: on a
 * network error QuizScreen enqueues the answer in IndexedDB and renders synthetic
 * feedback so the learner can move on, which by design *disables* the options.
 * The stale assertion was never caught because this test started failing earlier,
 * inside registerUser, the moment P.10's onboarding screen appeared — so it never
 * got far enough to disagree with the app.
 *
 * What it asserts now is the contract red line 4 actually promises: the answer is
 * not lost, the UI does not freeze, and the queue drains once the network is back.
 */

const IDB_NAME = 'whetzy_offline';
const IDB_STORE = 'pending_answers';

/**
 * A plain multiple-choice question, forced the same way pyodide.spec.ts forces an
 * exec one (force_question_id, dev/test only). Without it the drawn question type
 * depends on the learner's state and on row order in the content DB, so the test
 * would skip itself whenever an exec question came up — and a test that skips
 * itself is not coverage. Offline behaviour is only meaningful for a question
 * that posts an answer, which exec questions do not until Pyodide has booted.
 */
const FORCED_MCQ_ID = 'q010101001';

/** How many answers are waiting in the offline queue right now. */
function pendingCount(page: Page): Promise<number> {
  return page.evaluate(
    ({ name, store }: { name: string; store: string }) =>
      new Promise<number>((resolve) => {
        const req = indexedDB.open(name, 1);
        req.onsuccess = () => {
          try {
            const tx = req.result.transaction(store, 'readonly');
            const c = tx.objectStore(store).count();
            c.onsuccess = () => resolve(c.result as number);
            c.onerror = () => resolve(0);
          } catch {
            resolve(0); // store not created yet — nothing queued
          }
        };
        req.onerror = () => resolve(0);
      }),
    { name: IDB_NAME, store: IDB_STORE },
  );
}

test.describe('offline', () => {
  test('the TopBar connectivity indicator appears offline and disappears on reconnect', async ({
    page,
    context,
  }) => {
    // Distinct from the per-answer "guardado sin conexión" toast asserted below:
    // TopBar.tsx renders its own persistent "Sin conexión" badge for as long as
    // `useOfflineSync().isOnline` is false, independent of whether the learner
    // has answered anything. It is always mounted (App.tsx renders <TopBar />
    // outside the screen switch), so this only needs the home screen.
    const username = uniqueUsername('e2e_offline_indicator_');
    await registerUser(page, { username, displayName: 'E2E Offline Indicator' });

    await context.setOffline(true);
    await expect(page.getByText(/^Sin conexión/i)).toBeVisible({ timeout: 5_000 });

    await context.setOffline(false);
    await expect(page.getByText(/^Sin conexión/i)).not.toBeVisible({ timeout: 5_000 });
  });

  test('an answer given offline is queued in IndexedDB and flushed on reconnect', async ({
    page,
    context,
  }) => {
    const username = uniqueUsername('e2e_offline_');
    await registerUser(page, { username, displayName: 'E2E Offline' });

    await page.route('**/quiz/start', async (route, request) => {
      const body = JSON.parse((await request.postData()) ?? '{}') as Record<string, unknown>;
      await route.continue({
        postData: JSON.stringify({ ...body, force_question_id: FORCED_MCQ_ID }),
      });
    });

    await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
    await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });

    const options = page.locator('[class*="options_"] button');
    await expect(options.first()).toBeVisible({ timeout: 10_000 });

    await context.setOffline(true);
    try {
      expect(await pendingCount(page), 'queue starts empty').toBe(0);

      await options.first().click();

      // The app must advance rather than freeze: a toast, plus the synthetic
      // feedback panel that lets the learner keep going.
      // El aviso, no cualquier `role=status`: con el correo sin verificar también
      // está la franja de 45.3, y `getByRole('status')` a secas chocaba en modo
      // estricto (CI del 2026-10-21).
      await expect(page.getByRole('status').filter({ hasText: /sin conexión|offline/i })).toBeVisible({ timeout: 10_000 });
      await expect(
        page.getByText(/guardado sin conexión|saved offline/i).first(),
      ).toBeVisible({ timeout: 10_000 });

      // …and the answer must really be persisted, not merely acknowledged on screen.
      expect(await pendingCount(page), 'answer was enqueued').toBeGreaterThan(0);
    } finally {
      await context.setOffline(false);
    }

    // useOfflineSync flushes the queue on the browser's own 'online' event.
    await page.waitForFunction(
      ({ name, store }: { name: string; store: string }) =>
        new Promise<boolean>((resolve) => {
          const req = indexedDB.open(name, 1);
          req.onsuccess = () => {
            try {
              const tx = req.result.transaction(store, 'readonly');
              const c = tx.objectStore(store).count();
              c.onsuccess = () => resolve((c.result as number) === 0);
              c.onerror = () => resolve(false);
            } catch {
              resolve(false);
            }
          };
          req.onerror = () => resolve(false);
        }),
      { name: IDB_NAME, store: IDB_STORE },
      { timeout: 20_000 },
    );
  });
});
