import { expect, test, type Page } from '@playwright/test';
import { loginUser } from './helpers';

const IDB_NAME = 'whetzy_offline';
const IDB_STORE = 'pending_answers';

async function idbPendingCount(page: Page): Promise<number> {
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
            resolve(0);
          }
        };
        req.onerror = () => resolve(0);
      }),
    { name: IDB_NAME, store: IDB_STORE },
  );
}

test.describe('Offline behaviour', () => {
  test.beforeEach(async ({ page }) => {
    await loginUser(page, process.env.E2E_EMAIL!, process.env.E2E_PASSWORD!);
  });

  test('go offline → offline indicator visible → answer attempt handled gracefully', async ({
    page,
    context,
  }) => {
    await page.getByRole('button', { name: /empezar a aprender/i }).click();

    const options = page.getByRole('button').filter({ hasText: /^[A-D]/ });
    await expect(options.first()).toBeVisible({ timeout: 20_000 });

    await context.setOffline(true);
    await expect(page.getByText(/sin conexión/i)).toBeVisible({ timeout: 5_000 });

    await options.first().click();
    await expect(page.getByText(/sin conexión/i)).toBeVisible();

    await context.setOffline(false);
  });

  test('go back online → offline indicator disappears', async ({ page, context }) => {
    await page.getByRole('button', { name: /empezar a aprender/i }).click();

    const options = page.getByRole('button').filter({ hasText: /^[A-D]/ });
    await expect(options.first()).toBeVisible({ timeout: 20_000 });

    await context.setOffline(true);
    await expect(page.getByText(/sin conexión/i)).toBeVisible({ timeout: 5_000 });

    await context.setOffline(false);
    await expect(page.getByText(/sin conexión/i)).not.toBeVisible({ timeout: 5_000 });
  });

  test('offline answer is queued in IDB and flushed when back online', async ({
    page,
    context,
  }) => {
    await page.getByRole('button', { name: /empezar a aprender/i }).click();

    const options = page.getByRole('button').filter({ hasText: /^[A-D]/ });
    await expect(options.first()).toBeVisible({ timeout: 20_000 });

    // Go offline
    await context.setOffline(true);
    await expect(page.getByText(/sin conexión/i)).toBeVisible({ timeout: 5_000 });

    // IDB should start empty
    expect(await idbPendingCount(page)).toBe(0);

    // Answer while offline — enqueue() should fire
    await options.first().click();

    // The quiz shows a synthetic feedback panel (offline toast + feedback to advance)
    await expect(page.getByText(/guardado|saved offline/i)).toBeVisible({ timeout: 5_000 });

    // Verify IDB has the queued answer
    expect(await idbPendingCount(page)).toBeGreaterThan(0);

    // Come back online — useOfflineSync fires flush() on the 'online' event
    await context.setOffline(false);

    // Wait for IDB to drain (flush posts to backend then clears the store)
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
      { timeout: 15_000 },
    );
  });
});
