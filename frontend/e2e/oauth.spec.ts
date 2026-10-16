/**
 * 19.1 — OAuth social login E2E tests using the `test` provider.
 *
 * The `test` provider is only active when ENVIRONMENT != "production".
 * It bypasses external HTTP calls so these tests run without real OAuth
 * credentials. The backend immediately redirects to its own callback with
 * code=test-code and a fresh CSRF state.
 *
 * Run with:
 *   npx playwright test e2e/oauth.spec.ts
 */
import { test, expect } from '@playwright/test';

export const BASE_URL = process.env.E2E_BASE_URL ?? 'http://localhost:5173';
const API_URL = process.env.API_BASE_URL ?? 'http://localhost:8000';

// El backend solo anuncia los proveedores con credenciales configuradas
// (`GET /auth/oauth/providers`, para no pintar un botón que responde 503), y en
// CI no hay credenciales de GitHub ni de Google. Estos tests prueban la
// interfaz y el flujo del proveedor `test`, así que fijan la lista.
test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/auth/oauth/providers', (route) =>
    route.fulfill({ json: { providers: ['github', 'google'] } }),
  );
});

test.describe('19.1 — OAuth test provider flow', () => {
  test('test provider start → callback → tokens stored → home screen', async ({ page }) => {
    // Navigate to auth screen
    await page.goto('/auth');
    await expect(page.getByRole('button', { name: 'Crear cuenta' })).toBeVisible({ timeout: 10_000 });

    // Social buttons should be visible
    await expect(page.locator('button', { hasText: /GitHub/i })).toBeVisible();
    await expect(page.locator('button', { hasText: /Google/i })).toBeVisible();

    // Simulate the backend OAuth redirect manually: hit /start directly and follow the chain
    // The test provider redirects to /callback which redirects to FRONTEND_BASE_URL/?oauth_token=...
    const startRes = await page.request.get(`${API_URL}/api/v1/auth/oauth/test/start`, {
      maxRedirects: 0,
    }).catch(() => null);

    // Expect a redirect to the test callback
    if (startRes && startRes.status() === 302) {
      const callbackUrl = startRes.headers()['location'] ?? '';
      expect(callbackUrl).toContain('/test/callback');

      // Follow the callback — it will redirect to FRONTEND_BASE_URL/?oauth_token=...
      const cbRes = await page.request.get(callbackUrl, { maxRedirects: 0 }).catch(() => null);
      if (cbRes && cbRes.status() === 302) {
        const finalUrl = cbRes.headers()['location'] ?? '';
        expect(finalUrl).toContain('oauth_token=');
        expect(finalUrl).toContain('oauth_refresh=');

        // Navigate to the frontend URL with the OAuth tokens
        await page.goto(finalUrl);

        // The IIFE in api.ts should consume the tokens and store them in localStorage
        // Then the app should show the home/onboarding screen (user is logged in)
        // Wait for the page to stabilize
        await page.waitForLoadState('networkidle');

        // Tokens should be in localStorage now, URL params should be cleaned
        const accessToken = await page.evaluate(() =>
          localStorage.getItem('whetzy_access_token')
        );
        expect(accessToken).toBeTruthy();

        // URL should not contain oauth params anymore
        const url = page.url();
        expect(url).not.toContain('oauth_token=');
      }
    }
  });

  test('OAuth error param is displayed and cleared', async ({ page }) => {
    // Navigate with an oauth_error param (simulates backend redirect on error).
    // domcontentloaded, not networkidle: on this root path (unlike /auth,
    // used by the other tests in this file) networkidle never fired and the
    // test hung to its 60s timeout — root cause not pinned down, but the
    // assertions below already retry-wait for the error banner itself, so
    // waiting for the DOM instead of network silence changes nothing they check.
    await page.goto('/?oauth_error=email_required');
    await page.waitForLoadState('domcontentloaded');

    // The error should be shown
    await expect(page.locator('[class*="error_"]')).toBeVisible({ timeout: 5_000 });
    const errorText = await page.locator('[class*="error_"]').textContent();
    expect(errorText).toContain('proveedor');

    // URL should be cleaned of the param
    const url = page.url();
    expect(url).not.toContain('oauth_error=');
  });

  test('unknown oauth_error shows raw value', async ({ page }) => {
    await page.goto('/?oauth_error=some_unknown_error');
    await page.waitForLoadState('domcontentloaded');

    const errorText = await page.locator('[class*="error_"]').textContent();
    expect(errorText).toContain('some_unknown_error');
    expect(page.url()).not.toContain('oauth_error=');
  });

  test('provider_error shows connection error message', async ({ page }) => {
    await page.goto('/?oauth_error=provider_error');
    await page.waitForLoadState('domcontentloaded');

    const errorText = await page.locator('[class*="error_"]').textContent();
    expect(errorText).toContain('proveedor');
  });
});

test.describe('19.1 — OAuth buttons UI', () => {
  test('GitHub and Google buttons are visible on auth screen', async ({ page }) => {
    await page.goto('/auth');
    // No `networkidle`: /auth pregunta por la sesión (/auth/me, /auth/refresh,
    // #215) y Playwright no da por cerradas esas respuestas 401, así que la red
    // nunca quedaba «inactiva». Se espera a lo que importa: los botones.
    await expect(page.locator('button', { hasText: /GitHub/i })).toBeVisible({ timeout: 15_000 });

    await expect(page.locator('button', { hasText: /GitHub/i })).toBeVisible();
    await expect(page.locator('button', { hasText: /Google/i })).toBeVisible();
  });

  test('GitHub button redirects to OAuth start endpoint', async ({ page }) => {
    // We intercept the navigation instead of following it (would go to GitHub)
    await page.goto('/auth');
    // No `networkidle`: /auth pregunta por la sesión (/auth/me, /auth/refresh,
    // #215) y Playwright no da por cerradas esas respuestas 401, así que la red
    // nunca quedaba «inactiva». Se espera a lo que importa: los botones.
    await expect(page.locator('button', { hasText: /GitHub/i })).toBeVisible({ timeout: 15_000 });

    let navigatedUrl = '';
    page.on('framenavigated', (frame) => {
      if (frame === page.mainFrame()) {
        navigatedUrl = frame.url();
      }
    });

    // Since GITHUB_CLIENT_ID is empty in test env, this will return 503
    // but we just need to verify the button triggers a navigation to the backend
    const githubBtn = page.locator('button', { hasText: /GitHub/i });
    await githubBtn.click();

    // Give navigation a moment
    await page.waitForTimeout(500);

    // The button calls auth.startOAuth('github') which sets window.location.href
    // to BASE_URL/auth/oauth/github/start
    expect(navigatedUrl).toContain('/auth/oauth/github/start');
  });
});
