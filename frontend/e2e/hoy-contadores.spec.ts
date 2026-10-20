import { test, expect, type Route } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerUser, uniqueUsername } from './helpers';

/**
 * 46.12 (docs/PLAN_UI_AVANZADA.md §7.3): Hoy cuenta desde la última foto.
 * Las respuestas de progreso y misiones se simulan (una cuenta nueva no tiene
 * skills dominadas ni misiones completas); la foto de la visita anterior se
 * escribe en localStorage como la dejaría Hoy. La lógica de la foto tiene sus
 * tests de componente.
 */
const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

for (const lang of ['es', 'en'] as const) {
  for (const width of [390, 1280]) {
    test(`misiones, rutas y banda cuentan desde la foto (${lang}, ${width} px)`, async ({ page }) => {
      await page.setViewportSize({ width, height: 1000 });
      await registerUser(page, { username: uniqueUsername('e2e_hoy_'), displayName: 'Hoy' });
      const userId = await page.evaluate(() =>
        (window as unknown as { __whetzyStore: { getState: () => { user: { id: string } } } }).__whetzyStore.getState().user.id);
      await page.route('**/api/v1/progress/dashboard', (r) => json(r, {
        level: 3, total_xp: 400, current_streak: 4, max_streak: 4, streak_freeze_available: 1,
        last_active: null, reviews_due: 0, total_sessions: 9,
        tracks: [
          { track_id: 'track01', name_es: 'Python', name_en: 'Python', icon: '🐍', color: '#000', average_mastery: 0.4, skills_mastered: 6, total_skills: 32 },
          { track_id: 'track02', name_es: 'JavaScript', name_en: 'JavaScript', icon: '⚡', color: '#000', average_mastery: 0.2, skills_mastered: 2, total_skills: 32 },
        ],
      }));
      await page.route('**/api/v1/missions', (r) => json(r, [
        { mission: { id: 'm1', type: 'questions_answered', target_value: 10, xp_reward: 20, name_es: 'Responde 10 preguntas', name_en: 'Answer 10 questions' }, progress: 10, completed: true },
        { mission: { id: 'm2', type: 'questions_answered', target_value: 20, xp_reward: 30, name_es: 'Responde 20 preguntas', name_en: 'Answer 20 questions' }, progress: 12, completed: false },
      ]));
      await page.route('**/api/v1/progress/skills*', (r) => json(r, [
        { skill_id: 'sk010101', name_es: 'Variables', name_en: 'Variables', module_id: 'mod0101', p_known: 0.95, elo_rating: 1500, attempts: 14, correct_count: 13, accuracy: 0.93, mastered: true, fsrs_due: null },
      ]));
      const today = new Date().toISOString().slice(0, 10);
      await page.evaluate(([id, day, l]) => {
        localStorage.setItem(`whetzy_fx_missions_${id}_${day}`, JSON.stringify({ m1: false, m2: false }));
        localStorage.setItem(`whetzy_fx_tracks_${id}`, JSON.stringify({ track01: 3, track02: 2 }));
        localStorage.setItem(`whetzy_fx_bands_${id}`, JSON.stringify({ sk010101: 'developing' }));
        (window as unknown as { __whetzyStore: { setState: (f: (s: { user: object }) => object) => void } })
          .__whetzyStore.setState((s) => ({ user: { ...s.user, language: l } }));
      }, [userId, today, lang] as const);
      await page.reload();
      await expect(page.getByTestId('missions-count')).toHaveAttribute('data-from', '0');
      await expect(page.getByTestId('track-mastered-track01')).toHaveAttribute('data-from', '3');
      await expect(page.getByTestId('track-icon-track01')).toHaveAttribute('data-fx', 'tap');
      await expect(page.getByTestId('track-mastered-track02')).not.toHaveAttribute('data-from');
      // El recuento dura 600 ms; aquí se captura el final, y el punto de partida
      // lo fija `data-from` arriba.
      await expect(page.getByTestId('track-mastered-track01')).toContainText('6/32');
      await page.waitForTimeout(800);
      await page.screenshot({ path: `../docs/ui-snapshots/46.12/final-${lang}-${width}.png`, fullPage: true });

      const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
      expect(axe.violations, formatViolations(axe.violations)).toHaveLength(0);
    });
  }
}
