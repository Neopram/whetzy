import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { answerCurrentQuestion, formatViolations, markLessonSeen, registerUser, uniqueUsername } from './helpers';

/**
 * 46.7b (docs/PLAN_UI_AVANZADA.md §6.0 y §6.2): el resumen de sesión (nivel 3)
 * cuenta hacia arriba y estampa la nota; «Saltar recuento» está desde el primer
 * fotograma y deja la nota puesta. axe 0 en el resumen ya terminado.
 */
test('resumen de sesión: recuento saltable desde el primer fotograma (46.7b)', async ({ page }) => {
  await registerUser(page, { username: uniqueUsername('e2e_rec_'), displayName: 'Recuento' });
  await markLessonSeen(page);
  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
  await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });
  for (let i = 0; i < 10; i++) {
    await answerCurrentQuestion(page);
    await page.getByRole('button', { name: /^(SIGUIENTE|VER RESULTADOS)$/ }).click();
  }

  // El recuento dura 1,4 s: se salta en cuanto aparece (axe tarda más que eso).
  const skip = page.getByRole('button', { name: 'Saltar recuento' });
  await skip.click({ timeout: 10_000 });
  await expect(skip).toHaveCount(0);
  await expect(page.getByTestId('summary-grade')).toHaveCSS('opacity', '1');

  const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  expect(results.violations, formatViolations(results.violations)).toHaveLength(0);
  await page.getByRole('button', { name: 'CONTINUAR' }).click();
  await expect(page.getByRole('button', { name: 'Hoy', exact: true })).toBeVisible();
});
