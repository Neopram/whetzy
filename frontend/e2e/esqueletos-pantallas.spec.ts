import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerUser, uniqueUsername } from './helpers';

/**
 * 46.14 (docs/PLAN_UI_AVANZADA.md §7.4), fuera de Stats: con la red lenta, cada
 * pantalla enseña su esqueleto (no un «Cargando…» suelto, no una pantalla en
 * blanco) y luego el contenido, sin que el esqueleto empuje lo que hay debajo.
 * `esqueletos.spec.ts` cubre Stats; aquí, las otras pantallas con carga propia.
 *
 * Contra el backend real; se frena 1,5 s solo la llamada de la que depende el
 * esqueleto de cada pantalla.
 */
type StoreW = { __whetzyStore: { setState: (s: object) => void; getState: () => { user: object } } };

const CASES = [
  { screen: 'profile', api: '**/api/v1/badges' },
  { screen: 'league', api: '**/api/v1/league/current' },
  { screen: 'duels', api: '**/api/v1/duels/my' },
  { screen: 'wallet', api: '**/api/v1/economy/balance' },
] as const;

for (const lang of ['es', 'en'] as const) {
  for (const { screen, api } of CASES) {
    test(`${screen}: esqueleto y luego contenido (${lang}, 390 px)`, async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await registerUser(page, { username: uniqueUsername(`e2e_sk_${screen.slice(0, 3)}_`), displayName: 'Skel' });
      await page.route(api, async (route) => {
        await new Promise((r) => setTimeout(r, 1500));
        await route.continue();
      });
      await page.evaluate((l) => {
        const w = window as unknown as StoreW;
        w.__whetzyStore.setState({ user: { ...w.__whetzyStore.getState().user, language: l } });
      }, lang);
      await page.waitForTimeout(300);
      await page.evaluate((s) => {
        (window as unknown as { __cls: number }).__cls = 0;
        (window as unknown as { __clsSources: string[] }).__clsSources = [];
        type Shift = { value: number; hadRecentInput: boolean; sources?: { node?: Node; previousRect: DOMRectReadOnly; currentRect: DOMRectReadOnly }[] };
        new PerformanceObserver((list) => {
          for (const e of list.getEntries() as unknown as Shift[]) {
            if (e.hadRecentInput) continue;
            (window as unknown as { __cls: number }).__cls += e.value;
            for (const src of e.sources ?? []) {
              const el = src.node as Element | undefined;
              const name = el?.getAttribute?.('class') ?? el?.nodeName ?? '?';
              (window as unknown as { __clsSources: string[] }).__clsSources.push(
                `${e.value.toFixed(4)} ${name}: y ${Math.round(src.previousRect.y)}→${Math.round(src.currentRect.y)}, h ${Math.round(src.previousRect.height)}→${Math.round(src.currentRect.height)}`,
              );
            }
          }
        }).observe({ type: 'layout-shift', buffered: false });
        (window as unknown as StoreW).__whetzyStore.setState({ currentScreen: s });
      }, screen);

      // La Home tarda en irse (AnimatePresence `mode="wait"`) y sus misiones
      // recargan al cambiar el idioma: su esqueleto pasaba por el de la pantalla
      // nueva (mutación del 2026-10-24: la Cartera sin esqueleto seguía en verde).
      await expect(page.getByTestId('home-active-track')).toHaveCount(0);

      // Esqueleto: el contenedor ocupado y su forma, no un texto suelto. Solo los
      // visibles: la pantalla que se va puede dejar un esqueleto oculto en el DOM.
      const busy = page.locator('[aria-busy="true"]:visible').first();
      await expect(busy).toBeVisible();
      await expect(busy.locator('[data-skeleton]')).toBeVisible();
      await expect(page.locator('[data-boot-splash]')).toHaveCount(0);
      await page.waitForTimeout(300);
      const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
      expect(axe.violations, formatViolations(axe.violations)).toHaveLength(0);

      // Contenido: el esqueleto se va y lo de debajo no salta al llegar los datos.
      await expect(page.locator('[aria-busy="true"]:visible')).toHaveCount(0, { timeout: 15_000 });
      await page.waitForTimeout(500);
      const cls = await page.evaluate(() => (window as unknown as { __cls: number }).__cls);
      const sources = await page.evaluate(() => (window as unknown as { __clsSources: string[] }).__clsSources);
      expect(cls, `desplazamientos:\n${sources.join('\n')}`).toBeLessThan(0.01);
    });
  }
}
