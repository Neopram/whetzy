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
    await page.reload();
    await expect(page.getByRole('button', { name: 'Iniciar sesión' })).toBeVisible();

    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
    await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
    await page.getByRole('button', { name: 'ENTRAR' }).click();

    await expect(page.getByRole('button', { name: 'Inicio' })).toBeVisible({ timeout: 15_000 });
  });

  test('invalid login shows an error and does not navigate away', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    await page.getByLabel('Correo electrónico').fill('nobody@example.com');
    await page.getByLabel('Contraseña').fill('wrong-password');
    await page.getByRole('button', { name: 'ENTRAR' }).click();

    await expect(page.locator('text=⚠️')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole('button', { name: 'ENTRAR' })).toBeVisible();
  });
});
