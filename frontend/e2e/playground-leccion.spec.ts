import { test, expect } from '@playwright/test';
import { completeOnboarding, uniqueUsername } from './helpers';

/**
 * 43.7 (ADR-65 D9), contra el backend real con el contenido cargado:
 * «Probar este código» abre el ejemplo de la lección en el playground, y lo que
 * el alumno ejecuta para esa skill reaparece la vez siguiente.
 *
 * Antes: el playground era una herramienta de Hoy que abría siempre el mismo
 * «Hello, Whetzy!» en Python, sin relación con la lección.
 */
test('el ejemplo de la lección se abre en el playground y el fragmento reaparece', async ({ page }) => {
  test.setTimeout(120_000); // Pyodide se descarga y arranca en el primer «Ejecutar»
  const username = uniqueUsername('e2e_pg_');
  await page.goto('/auth');
  await page.getByLabel('Nombre').fill('Playground Lección');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByLabel('Confirmo que tengo 13 años o más').check();
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();
  await completeOnboarding(page); // Python Básico, empiezo de cero → Hoy

  // Hoy ya no lleva al playground.
  await expect(page.getByTestId('home-next')).toContainText('Lección:', { timeout: 15_000 });
  await expect(page.getByRole('button', { name: /Playground/ })).toHaveCount(0);

  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
  const tryCode = page.getByRole('button', { name: /Probar este código/ });
  // El ejemplo va en el último paso de la lección.
  for (let i = 0; i < 12 && !(await tryCode.isVisible()); i++) {
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(250);
  }
  const example = (await page.locator('pre code').first().innerText()).split('\n')[0];
  await tryCode.click();

  const lines = page.locator('.monaco-editor .view-lines');
  await expect(lines).toContainText(example.trim().slice(0, 12), { timeout: 20_000 });
  await expect(page.getByText(/Ejemplo de la lección/)).toBeVisible();

  // El alumno añade una línea y la ejecuta: se guarda para esta skill.
  await page.locator('.monaco-editor').click();
  await page.keyboard.press('Control+End');
  await page.keyboard.press('Enter');
  // insertText: sin eventos de tecla, el autocompletado de Monaco no se come letras.
  await page.keyboard.insertText('marca_e2e = 7');
  await page.getByRole('button', { name: /Ejecutar/ }).click();
  await expect(page.getByText('Ejecutando…')).toHaveCount(0, { timeout: 90_000 });

  // Volver lleva a la lección; abrirlo otra vez enseña el fragmento, no el ejemplo.
  await page.getByRole('button', { name: 'Volver', exact: true }).click();
  await expect(tryCode).toBeVisible();
  await tryCode.click();
  await expect(lines).toContainText('marca_e2e = 7', { timeout: 20_000 });
  await page.getByRole('button', { name: 'Volver al ejemplo' }).click();
  await expect(lines).not.toContainText('marca_e2e');
});
