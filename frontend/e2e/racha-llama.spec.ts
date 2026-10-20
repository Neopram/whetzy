import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerUser, uniqueUsername } from './helpers';

/**
 * 46.11 (docs/PLAN_UI_AVANZADA.md §7.3): la llama de la TopBar crece con la
 * racha y el comodín gastado pone un escudo. La racha y el escudo se fijan
 * desde el store de desarrollo (`__whetzyStore`): esperar 30 días reales no es
 * una prueba; lo que se comprueba aquí es la pintura, y la lógica tiene sus
 * tests de componente y de servidor.
 */
type Store = { setState: (f: (s: { user: object }) => object) => void; getState: () => { showStreakShield: () => void } };

async function setStreak(page: Page, days: number, lang: 'es' | 'en') {
  await page.evaluate(([d, l]) => {
    (window as unknown as { __whetzyStore: Store }).__whetzyStore.setState((s) => ({
      user: { ...s.user, currentStreak: d, language: l },
    }));
  }, [days, lang] as const);
}

for (const lang of ['es', 'en'] as const) {
  for (const width of [390, 1280]) {
    test(`tres tamaños y el escudo (${lang}, ${width} px)`, async ({ page }) => {
      await page.setViewportSize({ width, height: 700 });
      await registerUser(page, { username: uniqueUsername('e2e_racha_'), displayName: 'Racha' });
      for (const [days, tier] of [[3, '1'], [12, '2'], [45, '3']] as const) {
        await setStreak(page, days, lang);
        await expect(page.getByTestId('streak-flame')).toHaveAttribute('data-tier', tier);
        await page.locator('header').first().screenshot({ path: `../docs/ui-snapshots/46.11/llama-${days}-${lang}-${width}.png` });
      }
      await page.evaluate(() => (window as unknown as { __whetzyStore: Store }).__whetzyStore.getState().showStreakShield());
      await expect(page.getByTestId('streak-shield')).toBeVisible();
      await expect(page.getByRole('status').filter({ hasText: lang === 'es' ? 'Comodín usado' : 'Streak freeze used' })).toHaveCount(1);
      await page.waitForTimeout(200);
      await page.locator('header').first().screenshot({ path: `../docs/ui-snapshots/46.11/escudo-${lang}-${width}.png` });
      await expect(page.getByTestId('streak-shield')).toHaveCount(0, { timeout: 2000 });

      const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
      expect(axe.violations, formatViolations(axe.violations)).toHaveLength(0);
    });
  }
}
