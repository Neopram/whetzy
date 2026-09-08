import { expect, type Page } from '@playwright/test';

/**
 * Log in via the AuthScreen UI.
 *
 * Navigates to '/', switches to the "Iniciar sesión" tab, fills the email and
 * password fields, submits, and waits for the main navigation to confirm that
 * authentication succeeded.
 */
export async function loginUser(page: Page, email: string, password: string): Promise<void> {
  await page.goto('/');

  // Switch to login tab
  await page.getByRole('button', { name: /iniciar sesión/i }).click();

  // Fill credentials (labels match AuthScreen field <span> text inside <label>)
  await page.getByLabel(/correo/i).fill(email);
  await page.getByLabel(/contraseña/i).fill(password);

  // Submit form
  await page.getByRole('button', { name: /entrar/i }).click();

  // Bottom nav signals successful auth
  await expect(
    page.getByRole('navigation', { name: /main navigation/i }),
  ).toBeVisible({ timeout: 15_000 });
}
