import { expect, test } from '@playwright/test';
import { loginUser } from './helpers';

test.describe('Offline behaviour', () => {
  test.beforeEach(async ({ page }) => {
    await loginUser(page, process.env.E2E_EMAIL!, process.env.E2E_PASSWORD!);
  });

  test('go offline → offline indicator visible → answer attempt handled gracefully', async ({
    page,
    context,
  }) => {
    // Start a quiz so we have a live session
    await page.getByRole('button', { name: /empezar a aprender/i }).click();

    const options = page.getByRole('button').filter({ hasText: /^[A-D]/ });
    await expect(options.first()).toBeVisible({ timeout: 20_000 });

    // Disconnect the network — navigator.onLine becomes false, "offline" event fires
    await context.setOffline(true);

    // TopBar renders "Sin conexión" when !isOnline (useOfflineSync hook)
    await expect(page.getByText(/sin conexión/i)).toBeVisible({ timeout: 5_000 });

    // Attempt to answer while offline — submitAnswer() will throw a network error,
    // but the offline indicator should remain visible in the TopBar
    await options.first().click();
    await expect(page.getByText(/sin conexión/i)).toBeVisible();

    // Restore the network before the test ends to avoid polluting later tests
    await context.setOffline(false);
  });

  test('go back online → offline indicator disappears', async ({ page, context }) => {
    // Start quiz so the TopBar is rendered (it is hidden on the auth screen)
    await page.getByRole('button', { name: /empezar a aprender/i }).click();

    const options = page.getByRole('button').filter({ hasText: /^[A-D]/ });
    await expect(options.first()).toBeVisible({ timeout: 20_000 });

    // Go offline
    await context.setOffline(true);
    await expect(page.getByText(/sin conexión/i)).toBeVisible({ timeout: 5_000 });

    // Come back online — the "offline" div unmounts when isOnline becomes true
    await context.setOffline(false);
    await expect(page.getByText(/sin conexión/i)).not.toBeVisible({ timeout: 5_000 });
  });
});
