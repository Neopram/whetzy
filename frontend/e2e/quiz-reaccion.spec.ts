import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, markLessonSeen, registerUser, uniqueUsername } from './helpers';

/**
 * 46.10 (docs/PLAN_UI_AVANZADA.md §7.3): la opción reacciona a la respuesta y
 * el «+XP» vuela de la tarjeta al marcador. Contra el backend real, con la
 * pregunta q010101001 forzada como en accessibility.spec.ts (opciones
 * 2var / my-var / class / _my_var; correcta, la última).
 */
const FORCED_MCQ_ID = 'q010101001';

async function openForcedQuestion(page: Page, lang: 'es' | 'en') {
  await registerUser(page, { username: uniqueUsername('e2e_fx_'), displayName: 'Fx' });
  await markLessonSeen(page);
  await page.route('**/quiz/start', async (route, request) => {
    const body = JSON.parse((await request.postData()) ?? '{}') as Record<string, unknown>;
    await route.continue({ postData: JSON.stringify({ ...body, force_question_id: FORCED_MCQ_ID }) });
  });
  if (lang === 'en') {
    // La interfaz sigue a `user.language` (App.tsx); el store solo existe en desarrollo.
    await page.evaluate(() => {
      type Store = { setState: (f: (s: { user: object }) => object) => void };
      (window as unknown as { __whetzyStore: Store }).__whetzyStore.setState((s) => ({
        user: { ...s.user, language: 'en' },
      }));
    });
  }
  await page.getByRole('button', { name: lang === 'es' ? 'ESTUDIAR AHORA' : 'STUDY NOW' }).click();
  await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 20_000 });
}

const option = (page: Page, text: string) =>
  page.locator('[class*="options_"] button').filter({ hasText: new RegExp(`^[A-D]${text}`) });

for (const lang of ['es', 'en'] as const) {
  for (const width of [390, 1280]) {
    test(`acierto: la correcta late y el «+XP» aterriza en el marcador (${lang}, ${width} px)`, async ({ page }) => {
      await page.setViewportSize({ width, height: 900 });
      await openForcedQuestion(page, lang);
      await option(page, '_my_var').click();
      await expect(option(page, '_my_var')).toHaveAttribute('data-fx', 'pulse');
      // A mitad del vuelo: la opción late y el «+XP» va camino del marcador.
      await page.waitForTimeout(180);
      await page.screenshot({ path: `../docs/ui-snapshots/46.10/acierto-${lang}-${width}.png` });
      await expect(page.getByTestId('xp-badge').getByRole('status')).toHaveText(/^\+\d+ XP$/);
      await expect(page.getByTestId('feedback-panel').getByText(/^\+\d+ XP$/)).toHaveCount(0);

      const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
      expect(axe.violations, formatViolations(axe.violations)).toHaveLength(0);
    });
  }
}

for (const width of [390, 1280]) {
  test(`fallo: la elegida tiembla y la correcta late (es, ${width} px)`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await openForcedQuestion(page, 'es');
    await option(page, '2var').click();
    await expect(option(page, '2var')).toHaveAttribute('data-fx', 'shake');
    await expect(option(page, '_my_var')).toHaveAttribute('data-fx', 'pulse');
    await page.waitForTimeout(150);
    await page.screenshot({ path: `../docs/ui-snapshots/46.10/fallo-es-${width}.png` });
    // Reaccionar no puede borrar la opción: framer devolvía `opacity` al `initial`
    // (oculto) al pasar a la variante de reacción, y la elegida desaparecía.
    for (const text of ['2var', 'my-var', 'class', '_my_var']) {
      await expect(option(page, text)).toHaveCSS('opacity', '1');
    }
  });
}

test('movimiento reducido: ni late ni tiembla, y el «+XP» sale ya en el marcador', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await openForcedQuestion(page, 'es');
  await option(page, '_my_var').click();
  await expect(page.getByTestId('xp-badge').getByRole('status')).toHaveText(/^\+\d+ XP$/);
  await expect(option(page, '_my_var')).not.toHaveAttribute('data-fx', /.+/);
});
