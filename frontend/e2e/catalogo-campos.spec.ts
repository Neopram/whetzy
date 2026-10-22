import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerUser, uniqueUsername } from './helpers';

/**
 * Catálogo por campos (ola 2, 2026-10-21), contra el backend real con el
 * contenido de verdad: el campo filtra y se combina con el tipo. axe 0 en cada
 * paso, en ES a 390 y a 1280 px.
 */
const SHOTS = '../docs/ui-snapshots/catalogo-campos';

async function axe0(page: Page) {
  const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  expect(r.violations, formatViolations(r.violations)).toHaveLength(0);
}

for (const width of [390, 1280]) {
  test(`catálogo por campos (es, ${width} px)`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await registerUser(page, { username: uniqueUsername('e2e_campos_'), displayName: 'Campos' });
    await page.getByRole('button', { name: 'Rutas', exact: true }).click();
    await page.getByRole('button', { name: /todas las rutas/i }).click();
    const fields = page.getByRole('group', { name: 'Campo' });
    await expect(fields).toBeVisible({ timeout: 15_000 });
    await page.screenshot({ path: `${SHOTS}/todos-es-${width}.png`, fullPage: true });
    await axe0(page);

    const total = await page.locator('[class*="catalogue_"] > li').count();
    await fields.getByRole('button', { name: /Seguridad y redes/ }).click();
    await expect(fields.getByRole('button', { name: /Seguridad y redes/ })).toHaveAttribute('aria-pressed', 'true');
    const security = await page.locator('[class*="catalogue_"] > li').count();
    expect(security).toBeGreaterThan(0);
    expect(security).toBeLessThan(total);
    await page.screenshot({ path: `${SHOTS}/seguridad-es-${width}.png`, fullPage: true });
    await axe0(page);

    await page.getByRole('tab', { name: /Certificaciones/ }).click();
    const certs = page.locator('[class*="catalogue_"] > li');
    await expect(certs.first()).toBeVisible();
    expect(await certs.count()).toBeLessThan(security);
    await expect(fields.getByRole('button', { name: /Desarrollo de software/ })).toHaveCount(0);
    await page.screenshot({ path: `${SHOTS}/seguridad-certificaciones-es-${width}.png`, fullPage: true });
    await axe0(page);
  });
}
