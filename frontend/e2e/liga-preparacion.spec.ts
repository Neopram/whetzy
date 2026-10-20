import { test, expect, type Page, type Route } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerUser, uniqueUsername } from './helpers';

/**
 * 46.13 (docs/PLAN_UI_AVANZADA.md §7.3): Liga y Preparación entran escalonadas.
 * La clasificación y la preparación se simulan (una cuenta nueva no tiene liga
 * con siete alumnos ni dominios evaluados); la lógica tiene sus tests de componente.
 */
const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
type Store = { setState: (f: (s: { user: object }) => object) => void };

async function prepare(page: Page, lang: 'es' | 'en') {
  await registerUser(page, { username: uniqueUsername('e2e_liga_'), displayName: 'Liga' });
  await page.route('**/api/v1/league/current', (r) => json(r, {
    league: { id: 'oro', name: 'Oro', tier: 'gold', min_xp: 0 }, week_start: '2026-10-19',
    standings: [1, 2, 3, 4, 5, 6, 7].map((rank) => ({
      rank, user_id: `u${rank}`, username: `u${rank}`, display_name: rank === 5 ? 'Liga' : `Alumno ${rank}`,
      avatar_emoji: '🦊', xp_earned: 1000 - rank * 60, is_current_user: rank === 5,
    })),
    promotion_zone: 5, demotion_zone: 1, total_members: 7, participating: true,
  }));
  await page.route('**/api/v1/exams/certification/*/readiness', (r) => json(r, {
    track_id: 'track09', overall_p_known: 0.4,
    domains: [
      { domain_id: 'd1', name_es: 'Fundamentos', name_en: 'Fundamentals', weight_pct: 40, p_known_mean: 0.3, skills_assessed: 4, skills_total: 8, ready: false, answers: 12, correct: 7 },
      { domain_id: 'd2', name_es: 'Control de flujo', name_en: 'Control flow', weight_pct: 30, p_known_mean: 0.9, skills_assessed: 6, skills_total: 6, ready: true, answers: 30, correct: 28 },
      { domain_id: 'd3', name_es: 'Funciones', name_en: 'Functions', weight_pct: 30, p_known_mean: 0.1, skills_assessed: 1, skills_total: 6, ready: false, answers: 3, correct: 1 },
    ],
  }));
  await page.evaluate((l) => {
    (window as unknown as { __whetzyStore: Store }).__whetzyStore.setState((s) => ({ user: { ...s.user, language: l } }));
  }, lang);
}

for (const lang of ['es', 'en'] as const) {
  for (const width of [390, 1280]) {
    test(`liga y preparación escalonadas (${lang}, ${width} px)`, async ({ page }) => {
      await page.setViewportSize({ width, height: 1000 });
      await prepare(page, lang);
      await page.evaluate(() => (window as unknown as { __whetzyStore: { setState: (s: object) => void } }).__whetzyStore.setState({ currentScreen: 'league' }));
      await expect(page.getByTestId('league-rows')).toHaveAttribute('data-enter', 'stagger');
      await expect(page.locator('[data-fx="pulse-once"]')).toHaveCount(2);
      await expect(page.getByRole('dialog')).toHaveCount(0);
      await page.waitForTimeout(900);
      await page.screenshot({ path: `../docs/ui-snapshots/46.13/liga-${lang}-${width}.png`, fullPage: true });
      const axeL = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
      expect(axeL.violations, formatViolations(axeL.violations)).toHaveLength(0);

      await page.evaluate(() => (window as unknown as { __whetzyStore: { setState: (s: object) => void } }).__whetzyStore.setState({ readinessTrackId: 'track09', currentScreen: 'readiness' }));
      await expect(page.locator('ul[data-enter="stagger"]')).toBeVisible();
      await page.waitForTimeout(900);
      await page.screenshot({ path: `../docs/ui-snapshots/46.13/preparacion-${lang}-${width}.png`, fullPage: true });
      const axeR = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
      expect(axeR.violations, formatViolations(axeR.violations)).toHaveLength(0);
    });
  }
}
