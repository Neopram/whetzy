import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerUser, uniqueUsername, waitForAnimations } from './helpers';

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
      // El idioma se cambia antes de medir: al pasar a inglés, la franja «verifica tu
      // correo» y la barra superior cambian de texto y se recolocan, y ese salto
      // (0,019 a 390 px, medido con las fuentes del sistema) no es del esqueleto.
      await page.evaluate((l) => {
        const w = window as unknown as StoreW;
        w.__whetzyStore.setState({ user: { ...w.__whetzyStore.getState().user, language: l } });
      }, lang);
      await page.waitForTimeout(300);
      await page.evaluate(() => {
        // CLS del tramo: el esqueleto no puede empujar lo de abajo al llegar los datos.
        (window as unknown as { __cls: number }).__cls = 0;
        (window as unknown as { __clsSources: string[] }).__clsSources = [];
        type Shift = { value: number; hadRecentInput: boolean; sources?: { node?: Node; previousRect: DOMRectReadOnly; currentRect: DOMRectReadOnly }[] };
        new PerformanceObserver((list) => {
          for (const e of list.getEntries() as unknown as Shift[]) {
            if (e.hadRecentInput) continue;
            (window as unknown as { __cls: number }).__cls += e.value;
            // Qué se movió, para que un fallo en CI diga dónde (2026-10-21: 0,019 solo
            // en inglés a 390 px en CI; en local, menos de 0,01).
            for (const src of e.sources ?? []) {
              const el = src.node as Element | undefined;
              const name = el?.getAttribute?.('class') ?? el?.nodeName ?? '?';
              (window as unknown as { __clsSources: string[] }).__clsSources.push(
                `${e.value.toFixed(4)} ${name}: y ${Math.round(src.previousRect.y)}→${Math.round(src.currentRect.y)}, h ${Math.round(src.previousRect.height)}→${Math.round(src.currentRect.height)}`,
              );
            }
          }
        }).observe({ type: 'layout-shift', buffered: false });
        (window as unknown as StoreW).__whetzyStore.setState({ currentScreen: 'stats' });
      });
      const busy = page.locator('[aria-busy="true"]').first();
      await expect(busy).toBeVisible();
      await expect(busy.locator('[data-skeleton]')).toBeVisible();
      // La pantalla de carga de Suspense (BootSplash, App.tsx) sale con su animación
      // de salida; si axe la pilla a medio fundido, mide su texto contra el fondo
      // a contraste 1,01. Antes de axe se espera a que no quede y a que acabe el fundido.
      await page.screenshot({ path: `../docs/ui-snapshots/46.14/esqueleto-${lang}-${width}.png` });
      await expect(page.locator('[data-boot-splash]')).toHaveCount(0);
      await waitForAnimations(page);
      const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
      expect(axe.violations, formatViolations(axe.violations)).toHaveLength(0);
      await expect(page.locator('[aria-busy="true"]')).toHaveCount(0, { timeout: 15_000 });
      await page.waitForTimeout(500);
      await page.screenshot({ path: `../docs/ui-snapshots/46.14/contenido-${lang}-${width}.png` });
      // Medido en `master` con el «Cargando…» de texto: 0,003. Con un esqueleto de
      // tarjeta en la sección, 0,072; con el de una línea, 0,003.
      const cls = await page.evaluate(() => (window as unknown as { __cls: number }).__cls);
      const sources = await page.evaluate(() => (window as unknown as { __clsSources: string[] }).__clsSources);
      expect(cls, `desplazamientos:\n${sources.join('\n')}`).toBeLessThan(0.01);
    });
  }
}
