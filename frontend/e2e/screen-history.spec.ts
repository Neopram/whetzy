import { expect, test, type Page } from '@playwright/test';
import { markLessonSeen, registerUser, uniqueUsername } from './helpers';

/**
 * «Atrás» dentro de la app (PR B, 2026-10-16). Reproducido sobre `master`
 * 9e32059: las pantallas no tenían URL, «atrás» desde Rutas salía de la app y
 * recargar en Ranking volvía a Hoy.
 */
const tab = (page: Page, name: string) => page.getByRole('button', { name, exact: true });

test('cada pestaña tiene su URL; «atrás» vuelve a la anterior y recargar se queda', async ({ page }) => {
  await registerUser(page, { username: uniqueUsername('hist'), displayName: 'Historial' });
  await expect(page).toHaveURL(/\/$/);

  await tab(page, 'Rutas').click();
  await expect(page).toHaveURL(/\/tracks$/);
  await tab(page, 'Ranking').click();
  await expect(page).toHaveURL(/\/ranking$/);

  await page.goBack();
  await expect(page).toHaveURL(/\/tracks$/);
  await expect(tab(page, 'Rutas')).toHaveAttribute('aria-current', 'page');

  await page.goto('/ranking');
  await expect(tab(page, 'Ranking')).toHaveAttribute('aria-current', 'page', { timeout: 15_000 });
});

test('en el quiz «atrás» abre el diálogo de salida, y recargar lleva a Hoy', async ({ page }) => {
  await registerUser(page, { username: uniqueUsername('histq'), displayName: 'Historial Quiz' });
  await markLessonSeen(page);
  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
  await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });

  // Con algo respondido, salir pide confirmación (QuizScreen.requestClose).
  const options = page.locator('[class*="options_"] button');
  if (await options.count() > 0) await options.first().click();
  else await page.getByRole('button', { name: 'No lo sé' }).click();
  await expect(page.locator('[class*="explanation_"]')).toBeVisible({ timeout: 10_000 });

  await page.goBack();
  await expect(page.getByRole('alertdialog')).toBeVisible();
  await expect(page.locator('[class*="questionCard_"]')).toBeVisible();

  await page.getByRole('button', { name: 'Salir' }).click();
  await expect(tab(page, 'Hoy')).toHaveAttribute('aria-current', 'page');
  // El quiz cerrado no queda detrás de «atrás».
  await page.goBack();
  await expect(page.locator('[class*="questionCard_"]')).toHaveCount(0);

  // Recargar en mitad de un quiz lleva a Hoy, no a un quiz sin estado.
  await page.goto('/');
  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
  await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });
  await page.reload();
  await expect(tab(page, 'Hoy')).toHaveAttribute('aria-current', 'page', { timeout: 15_000 });
});
