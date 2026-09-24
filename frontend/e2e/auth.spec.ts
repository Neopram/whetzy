import { test, expect } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

test.describe('auth', () => {
  test('register creates an account and lands on home', async ({ page }) => {
    const username = uniqueUsername('e2e_reg_');
    await registerUser(page, { username, displayName: 'E2E Register' });

    await expect(page.getByRole('button', { name: 'ESTUDIAR AHORA' })).toBeVisible();
  });

  test('login with a previously registered account', async ({ page }) => {
    const username = uniqueUsername('e2e_login_');
    await registerUser(page, { username, displayName: 'E2E Login' });

    // Log out by clearing session storage and reloading (no logout button in TopBar
    // for this flow — simulate a fresh session the way the app itself detects it).
    await page.evaluate(() => localStorage.removeItem('whetzy_access_token'));
    await page.goto('/auth');
    await expect(page.getByRole('button', { name: 'Iniciar sesión' })).toBeVisible();

    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
    await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
    await page.getByRole('button', { name: 'ENTRAR' }).click();

    await expect(page.getByRole('button', { name: 'Inicio' })).toBeVisible({ timeout: 15_000 });
  });

  test('invalid login shows an error and does not navigate away', async ({ page }) => {
    await page.goto('/auth');
    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    await page.getByLabel('Correo electrónico').fill('nobody@example.com');
    await page.getByLabel('Contraseña').fill('wrong-password');
    await page.getByRole('button', { name: 'ENTRAR' }).click();

    await expect(page.locator('text=⚠️')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole('button', { name: 'ENTRAR' })).toBeVisible();
  });

  test('logout from the profile screen returns to the auth screen', async ({ page }) => {
    // Regression guard. Porting this assertion out of the abandoned root e2e/
    // suite (task 12.4) exposed a real bug: ProfileScreen's "Cerrar sesión"
    // calls useAppStore's `signOut`, which clears the tokens and resets the
    // store but cannot reach App.tsx's separate local `authState` — so the app
    // went on rendering the authenticated shell around a reset placeholder
    // user until the next reload. Nobody noticed because a manual reload does
    // land on AuthScreen (isAuthenticated() re-reads the cleared token on
    // boot), and the only test that covered it lived in the suite nothing ran.
    // Fixed in App.tsx; this test is what keeps it fixed.
    const username = uniqueUsername('e2e_logout_');
    await registerUser(page, { username, displayName: 'E2E Logout' });

    // ProfileScreen renders the sign-out button (i18n key `signOut` = "Cerrar sesión").
    await page.getByRole('button', { name: 'Perfil' }).click();
    await page.getByRole('button', { name: 'Cerrar sesión' }).click();

    // Sign-out leaves `/` as the public landing, not the register form.
    await expect(page.getByRole('link', { name: /Empieza gratis|Start free/i }).first()).toBeVisible({ timeout: 10_000 });
  });
});
