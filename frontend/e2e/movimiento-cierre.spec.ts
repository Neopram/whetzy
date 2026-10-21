import { test, expect, type Page, type Route } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

/**
 * 46.1 / 46.3 / 46.7 / 46.6a (docs/PLAN_UI_AVANZADA.md §6 y §7.2): cierre del
 * movimiento. El registro es real; lo que decide el servidor (combo, hitos,
 * misiones, cierre de sesión) se simula con `page.route`, porque una cuenta
 * nueva no llega a un combo de 7, a un nivel ni a una misión completa en un
 * test. Los eventos de analítica se interceptan en `/analytics/client-events`
 * (se fuerzan con `pagehide`, que es cuando `fxAnalytics` envía en lote).
 */
const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

type Sent = { type: string; tier?: number; fx?: string };

async function captureAnalytics(page: Page) {
  const sent: Sent[] = [];
  await page.route('**/analytics/client-events', async (route, request) => {
    const { events } = JSON.parse(request.postData() ?? '{"events":[]}') as { events: Sent[] };
    sent.push(...events);
    await json(route, { accepted: events.length });
  });
  const flush = async () => {
    await page.evaluate(() => window.dispatchEvent(new Event('pagehide')));
    await page.waitForTimeout(300);
  };
  return { sent, flush };
}

const question = (n: number) => ({
  id: `q-cierre-${n}`, skill_id: 'sk010101', type: 'mcq', difficulty_tier: 'easy',
  question_es: `Pregunta ${n}: ¿cuánto es 1 + 1?`, question_en: `Question ${n}: what is 1 + 1?`,
  options_es: ['1', '2', '3', '4'], options_en: ['1', '2', '3', '4'],
  correct_answer_es: null, correct_answer_en: null, code_es: null, code_en: null,
});

/** Sesión simulada de `total` preguntas; `events[i]` son los hitos de la respuesta i + 1. */
async function mockSession(page: Page, total: number, events: Record<number, unknown[]> = {}) {
  let answered = 0;
  await page.route('**/quiz/start', (r) => json(r, { session_id: 's-cierre', question: question(1), selection_reason: null }));
  await page.route('**/quiz/answer', (r) => {
    answered += 1;
    return json(r, {
      correct: true, correct_index: 1, explanation_es: 'Dos.', explanation_en: 'Two.', source: null,
      grade: 3, xp_earned: 10, combo: answered, user_elo: 1500, next_review: null,
      skill_mastery: { sk010101: 0.5 }, session_accuracy: 1,
      next_question: answered < total ? question(answered + 1) : null,
      next_selection_reason: null, events: events[answered] ?? [],
    });
  });
  await page.route('**/quiz/end', (r) => json(r, {
    total_questions: total, correct: total, accuracy: 1, max_combo: total, xp_earned: total * 10, duration_seconds: 30,
  }));
}

async function openSession(page: Page) {
  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
  await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });
}

async function answerAndNext(page: Page) {
  await page.locator('[class*="options_"] button').nth(1).click();
  await expect(page.getByTestId('feedback-panel')).toBeVisible();
  const next = page.getByRole('button', { name: /^(SIGUIENTE|VER RESULTADOS)$/ });
  const last = (await next.textContent())?.trim() === 'VER RESULTADOS';
  return { next, last };
}

test('combo: «×3» aparece en la 7.ª respuesta correcta seguida y no antes (46.1)', async ({ page }) => {
  await registerUser(page, { username: uniqueUsername('e2e_cmb_'), displayName: 'Combo' });
  await mockSession(page, 8);
  await openSession(page);
  const combo = page.getByTestId('combo');
  for (let n = 1; n <= 7; n++) {
    const { next } = await answerAndNext(page);
    await expect(combo).toContainText(`${n}`);
    if (n < 3) await expect(combo).not.toContainText('×');
    if (n >= 3 && n < 7) {
      await expect(combo).toContainText('×2');
      await expect(combo).not.toContainText('×3');
    }
    if (n === 7) {
      await expect(combo).toContainText('×3');
      await page.screenshot({ path: '../docs/ui-snapshots/46.1/combo-x3-es-1280.png' });
    }
    await next.click();
  }
});

test('misión completada: check dibujado y fx_emitted{tier 2, mission} una sola vez (46.3)', async ({ page }) => {
  const { sent, flush } = await captureAnalytics(page);
  await registerUser(page, { username: uniqueUsername('e2e_mis_'), displayName: 'Misión' });
  const userId = await page.evaluate(() =>
    (window as unknown as { __whetzyStore: { getState: () => { user: { id: string } } } }).__whetzyStore.getState().user.id);
  await page.route('**/api/v1/missions', (r) => json(r, [
    { mission: { id: 'm1', type: 'questions_answered', target_value: 10, xp_reward: 20, name_es: 'Responde 10 preguntas', name_en: 'Answer 10 questions' }, progress: 10, completed: true },
  ]));
  // La foto de la visita anterior: la misión aún no estaba completa.
  const today = new Date().toISOString().slice(0, 10);
  await page.evaluate(([id, day]) => {
    localStorage.setItem(`whetzy_fx_missions_${id}_${day}`, JSON.stringify({ m1: false }));
  }, [userId, today] as const);
  await page.reload();
  await expect(page.getByTestId('mission-check')).toBeVisible();
  await flush();
  const missions = () => sent.filter((e) => e.type === 'fx_emitted' && e.fx === 'mission');
  expect(missions()).toHaveLength(1);
  expect(missions()[0]).toMatchObject({ tier: 2 });

  // Al volver a Hoy la foto ya la tiene completa: ni check ni segundo evento.
  await page.reload();
  await expect(page.getByTestId('missions-count')).toBeVisible();
  await expect(page.getByTestId('mission-check')).toHaveCount(0);
  await flush();
  expect(missions()).toHaveLength(1);
});

test('dos hitos de nivel 4: UNA ceremonia, una tarjeta en el resumen y fx medidos (46.7, 46.6a)', async ({ page }) => {
  const { sent, flush } = await captureAnalytics(page);
  await registerUser(page, { username: uniqueUsername('e2e_cer_'), displayName: 'Ceremonia' });
  await mockSession(page, 2, {
    1: [{ type: 'level_up', payload: { level_before: 1, level: 2 } }],
    2: [{ type: 'streak_milestone', payload: { days: 7 } }],
  });
  await openSession(page);
  await (await answerAndNext(page)).next.click();
  const { next, last } = await answerAndNext(page);
  expect(last).toBe(true);
  await next.click();

  await expect(page.getByRole('dialog', { name: '¡Subes a nivel 2!' })).toBeVisible();
  await expect(page.getByRole('dialog')).toHaveCount(1);
  await expect(page.getByRole('region', { name: 'También en esta sesión' })).toContainText('7');
  await page.screenshot({ path: '../docs/ui-snapshots/46.7/dos-hitos-ceremonia-es-1280.png' });

  // «Saltar» la ceremonia: fx_skipped del nivel 4; después, el recuento (nivel 3) también se salta.
  await page.getByRole('button', { name: 'Saltar', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('button', { name: 'Saltar recuento' }).click({ timeout: 5_000 });
  await flush();

  const tier4 = sent.filter((e) => e.type === 'fx_emitted' && e.tier === 4);
  expect(tier4, JSON.stringify(sent)).toHaveLength(1);
  expect(tier4[0].fx).toBe('level_up');
  expect(sent.filter((e) => e.type === 'fx_skipped')).toEqual([
    { type: 'fx_skipped', tier: 4, fx: 'level_up' },
    { type: 'fx_skipped', tier: 3, fx: 'session_end' },
  ]);
});
