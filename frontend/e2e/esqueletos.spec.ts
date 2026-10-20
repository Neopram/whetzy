import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerUser, uniqueUsername } from './helpers';

/**
 * 46.14 (docs/PLAN_UI_AVANZADA.md §7.4): con la red lenta, Stats enseña un
 * esqueleto (no un «Cargando…» suelto) y luego el contenido. Se frena
 * `/progress/dashboard` 1,5 s contra el backend real, y se mide el CLS del tramo.
 */
type StoreW = { __whetzyStore: { setState: (s: object) => void; getState: () => { user: object } } };

for (const lang of ['es', 'en'] as const) {
  for (const width of [390, 1280]) {
    test(`esqueleto y luego contenido (${lang}, ${width} px)`, async ({ page }) => {
      await page.setViewportSize({ width, height: 900 });
      await registerUser(page, { username: uniqueUsername('e2e_skel_'), displayName: 'Skel' });
      await page.route('**/api/v1/progress/dashboard', async (route) => {
        await new Promise((r) => setTimeout(r, 1500));
        await route.continue();
      });
      await page.evaluate((l) => {
        // CLS del tramo: el esqueleto no puede empujar lo de abajo al llegar los datos.
        (window as unknown as { __cls: number }).__cls = 0;
        new PerformanceObserver((list) => {
          for (const e of list.getEntries() as unknown as { value: number; hadRecentInput: boolean }[]) {
            if (!e.hadRecentInput) (window as unknown as { __cls: number }).__cls += e.value;
          }
        }).observe({ type: 'layout-shift', buffered: false });
        const w = window as unknown as StoreW;
        w.__whetzyStore.setState({ user: { ...w.__whetzyStore.getState().user, language: l }, currentScreen: 'stats' });
      }, lang);
      const busy = page.locator('[aria-busy="true"]').first();
      await expect(busy).toBeVisible();
      await expect(busy.locator('[data-skeleton]')).toBeVisible();
      await page.screenshot({ path: `../docs/ui-snapshots/46.14/esqueleto-${lang}-${width}.png` });
      const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
      expect(axe.violations, formatViolations(axe.violations)).toHaveLength(0);
      await expect(page.locator('[aria-busy="true"]')).toHaveCount(0, { timeout: 15_000 });
      await page.waitForTimeout(500);
      await page.screenshot({ path: `../docs/ui-snapshots/46.14/contenido-${lang}-${width}.png` });
      // Medido en `master` con el «Cargando…» de texto: 0,003. Con un esqueleto de
      // tarjeta en la sección, 0,072; con el de una línea, 0,003.
      expect(await page.evaluate(() => (window as unknown as { __cls: number }).__cls)).toBeLessThan(0.01);
    });
  }
}
