import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, markLessonSeen, registerUser, uniqueUsername } from './helpers';
import { check } from '../src/widgets/checkers';

/**
 * 40.2 (docs/PLAN_UI_AVANZADA.md): los tres widgets del piloto, respondidos bien
 * y mal en móvil (390) y escritorio (1280), con axe en 0. La demostración NO es
 * contenido (ADR-62, ADR-67 D1): cada ítem sale de `widget_pilot_cases.json` y
 * `/quiz/start` y `/quiz/answer` se simulan con `page.route`; el usuario y la
 * sesión sí son reales. El veredicto simulado usa el checker de `widgets/checkers.ts`,
 * que el test de contrato ya iguala al del servidor.
 */
interface Item {
  widget: string; question_es: string; question_en: string; params: Record<string, unknown>;
  checker: string; target: unknown; cases: { state: unknown; expected: boolean; why: string }[];
}
const ITEMS = (JSON.parse(
  readFileSync(fileURLToPath(new URL('../../backend/tests/fixtures/widget_pilot_cases.json', import.meta.url)), 'utf-8'),
) as { items: Item[] }).items;

/** Lo que hace el alumno, solo con el teclado o el puntero, para dejar el widget en `state`. */
const DRIVE: Record<string, (page: Page, state: never) => Promise<void>> = {
  binarySearch: async (page, probes: number[]) => {
    for (const v of probes) await page.getByRole('button', { name: new RegExp(`valor ${v},`) }).click();
  },
  cidr: async (page, s: { network: string; broadcast: string }) => {
    await page.getByLabel('Dirección de red').fill(s.network);
    await page.getByLabel('Dirección de broadcast').fill(s.broadcast);
  },
  sqlJoin: async (page, pairs: number[][]) => {
    for (const [l, r] of pairs) {
      await page.locator('label').filter({ hasText: new RegExp(`^users\\(id=${l},.*con orders\\(id=${r},`) }).getByRole('checkbox').check();
    }
  },
};

async function open(page: Page, item: Item) {
  await registerUser(page, { username: uniqueUsername('e2e_wg_'), displayName: 'Wg' });
  await markLessonSeen(page);
  let answered: Record<string, unknown> | null = null;
  await page.route('**/quiz/start', (route) => route.fulfill({
    json: {
      session_id: 'demo-session',
      selection_reason: null,
      question: {
        id: `demo-${item.widget}`, skill_id: 'sk010101', type: 'interactive', difficulty_tier: 'easy',
        question_es: item.question_es, question_en: item.question_en,
        options_es: null, options_en: null, correct_answer_es: null, correct_answer_en: null,
        interactive: { widget: item.widget, params: item.params, checker: item.checker },
        expected_time_ms: 60000,
      },
    },
  }));
  await page.route('**/quiz/answer', async (route, request) => {
    answered = JSON.parse(request.postData() ?? '{}') as Record<string, unknown>;
    const correct = check(item.checker, answered.widget_state, item.target);
    await route.fulfill({
      json: {
        correct, correct_index: null, explanation_es: 'Explicación de la demostración.', explanation_en: 'Demo explanation.',
        source: null, grade: correct ? 3 : 1, xp_earned: correct ? 10 : 0, combo: correct ? 1 : 0, user_elo: 1500,
        next_review: null, skill_mastery: {}, session_accuracy: correct ? 1 : 0, next_question: null,
        next_selection_reason: null, events: [], widget_target: item.target,
      },
    });
  });
  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
  await expect(page.getByText(item.question_es)).toBeVisible({ timeout: 20_000 });
  return () => answered;
}

for (const width of [390, 1280]) {
  for (const item of ITEMS) {
    for (const caso of item.cases) {
      test(`${item.widget}: ${caso.expected ? 'acierto' : 'fallo'} (${caso.why}) a ${width} px`, async ({ page }) => {
        await page.setViewportSize({ width, height: 900 });
        const answered = await open(page, item);
        const comprobar = page.getByRole('button', { name: 'Comprobar' });
        await expect(comprobar).toBeDisabled();

        await DRIVE[item.widget](page, caso.state as never);
        // Sin scroll horizontal de la página: el widget cabe en el ancho del móvil.
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
        if (process.env.WIDGET_SHOTS) await page.screenshot({ path: `${process.env.WIDGET_SHOTS}/${item.widget}-${width}.png`, fullPage: true });
        const antes = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
        expect(antes.violations, formatViolations(antes.violations)).toHaveLength(0);

        await comprobar.click();
        await expect(page.getByTestId('feedback-panel')).toBeVisible();
        // Lo enviado es el estado del caso (en un JOIN, el orden de las filas no cuenta).
        expect(check(item.checker === 'unordered' ? 'unordered' : 'exact', answered()?.widget_state, caso.state)).toBe(true);
        await expect(page.getByTestId('feedback-panel')).toContainText(caso.expected ? '¡Correcto!' : 'Explicación de la demostración.');
        // El cliente vuelve a corregir con `widget_target` y no discrepa del servidor.
        await expect(page.locator('[data-checker-mismatch]')).toHaveCount(0);

        // El panel de feedback entra con un fundido: axe mide el contraste con la opacidad final.
        await expect(page.getByTestId('feedback-panel')).toHaveCSS('opacity', '1');
        const despues = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
        expect(despues.violations, formatViolations(despues.violations)).toHaveLength(0);
      });
    }
  }
}

test('búsqueda binaria: se opera solo con el teclado', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  await open(page, ITEMS[0]);
  const celda = page.getByRole('button', { name: /valor 7,/ });
  await celda.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('status').filter({ hasText: 'Quedan las posiciones 1 a 3' })).toBeVisible();
  await page.getByRole('button', { name: /valor 3,/ }).focus();
  await page.keyboard.press('Space');
  await expect(page.getByRole('button', { name: 'Comprobar' })).toBeEnabled();
});
