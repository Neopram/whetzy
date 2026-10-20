import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerUser, uniqueUsername } from './helpers';

/**
 * 46.15 bloque E (docs/PLAN_UI_AVANZADA.md §7.5), contra el backend real: las
 * tarjetas del catálogo entran escalonadas. El éxito del checkout (check solo
 * cuando el servidor confirma el plan) no se puede recorrer en local: hace
 * falta Paddle, que aquí no está configurado; lo cubre `comprar46.test.tsx`.
 */
const SHOTS = '../docs/ui-snapshots/46.15e';

async function axe0(page: Page) {
  const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  expect(r.violations, formatViolations(r.violations)).toHaveLength(0);
}

for (const width of [390, 1280]) {
  test(`catálogo: las tarjetas entran escalonadas (es, ${width} px)`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await registerUser(page, { username: uniqueUsername('e2e_cat_'), displayName: 'Catálogo' });
    await page.getByRole('button', { name: 'Yo', exact: true }).click();
    await page.getByRole('button', { name: 'Catálogo de cursos' }).click();
    const grid = page.getByRole('list').first();
    await expect(grid).toHaveAttribute('data-enter', 'stagger', { timeout: 10_000 });
    await page.waitForTimeout(800);
    await page.screenshot({ path: `${SHOTS}/catalogo-es-${width}.png` });
    await axe0(page);
  });
}

test('catálogo con movimiento reducido: sin escalonado', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await registerUser(page, { username: uniqueUsername('e2e_cat_rm_'), displayName: 'Catálogo' });
  await page.getByRole('button', { name: 'Yo', exact: true }).click();
  await page.getByRole('button', { name: 'Catálogo de cursos' }).click();
  await expect(page.getByRole('list').first()).toBeVisible({ timeout: 10_000 });
  await expect(page.getByRole('list').first()).not.toHaveAttribute('data-enter', /.+/);
});
