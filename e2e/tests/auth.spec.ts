import { expect, test } from '@playwright/test';
import { loginUser } from './helpers';

test.describe('Authentication', () => {
  test('register new user → home screen → nav visible', async ({ page }) => {
    const ts = Date.now();
    const email = `e2e-reg-${ts}@whetzy.test`;
    const username = `reguser${ts}`;

    await page.goto('/');

    // Auth screen shows the Whetzy brand heading
    await expect(page.getByRole('heading', { name: /whetzy/i })).toBeVisible({
      timeout: 10_000,
    });

    // "Crear cuenta" tab is the default — registration fields are already shown.
    // Labels live inside <label> wrappers so getByLabel uses implicit association.
    await page.getByLabel(/nombre/i).fill('E2E Reg User');
    await page.getByLabel(/usuario/i).fill(username);
    await page.getByLabel(/correo/i).fill(email);
    await page.getByLabel(/contraseña/i).fill('RegPass!2024');

    await page.getByRole('button', { name: /empezar a aprender/i }).click();

    // After auth the bottom nav appears (quiz screen hides it, but home does not)
    await expect(
      page.getByRole('navigation', { name: /main navigation/i }),
    ).toBeVisible({ timeout: 15_000 });
  });

  test('login with valid credentials → success', async ({ page }) => {
    await loginUser(page, process.env.E2E_EMAIL!, process.env.E2E_PASSWORD!);

    await expect(
      page.getByRole('navigation', { name: /main navigation/i }),
    ).toBeVisible();
  });

  test('login with wrong password → error message shown', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: /iniciar sesión/i }).click();
    await page.getByLabel(/correo/i).fill(process.env.E2E_EMAIL!);
    await page.getByLabel(/contraseña/i).fill('definitely-wrong-password');

    await page.getByRole('button', { name: /entrar/i }).click();

    // AuthScreen renders: <p className={styles.error}>⚠️ {error}</p>
    await expect(
      page.locator('p').filter({ hasText: /⚠/ }),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('logout → redirected to auth screen', async ({ page }) => {
    await loginUser(page, process.env.E2E_EMAIL!, process.env.E2E_PASSWORD!);

    // Navigate to Profile via the bottom nav
    await page.getByRole('button', { name: /perfil/i }).click();

    // Click the sign-out button (ProfileScreen renders: L.signOut = "Cerrar sesión")
    await page.getByRole('button', { name: /cerrar sesión/i }).click();

    // Auth screen re-appears — the "Crear cuenta" tab is the entry point
    await expect(
      page.getByRole('button', { name: /crear cuenta/i }),
    ).toBeVisible({ timeout: 10_000 });
  });
});
