import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerAndCompleteAQuiz, uniqueUsername } from './helpers';

/**
 * 46.15 bloque D (docs/PLAN_UI_AVANZADA.md §7.5), contra el backend real:
 * - Perfil: las insignias entran escalonadas; la ganada desde la última visita
 *   brilla una vez (foto en localStorage, sembrada vacía). Una cuenta nueva no
 *   gana ninguna con un quiz (la más fácil, `perfectionist`, pide una sesión
 *   perfecta), así que se añade esa insignia del seed a la respuesta de `/badges`.
 * - Estadísticas: la barra de la ruta crece desde 0. Una cuenta recién creada no
 *   domina ninguna skill y sin dominadas no hay barra, así que se sube
 *   `skills_mastered` en la respuesta de `/progress/dashboard` (solo ese dato).
 * - Cartera: listas escalonadas.
 * - Certificado público: sin un examen final aprobado en local no hay código
 *   válido; se responde a la verificación con un certificado válido y otro
 *   revocado. El sello solo aparece en el válido.
 */
const SHOTS = '../docs/ui-snapshots/46.15d';

async function axe0(page: Page) {
  const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  expect(r.violations, formatViolations(r.violations)).toHaveLength(0);
}

test('perfil, estadísticas y cartera (es, 390 px)', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  await registerAndCompleteAQuiz(page, { username: uniqueUsername('e2e_prog_'), displayName: 'Progreso' });

  // Perfil: una foto vacía de insignias hace «nuevas» las que ya tiene.
  await page.evaluate(() => {
    type Store = { getState: () => { user: { id: string } } };
    const uid = (window as unknown as { __whetzyStore: Store }).__whetzyStore.getState().user.id;
    localStorage.setItem(`whetzy_fx_badges_${uid}`, '[]');
  });
  await page.route('**/api/v1/badges', async (route) => {
    const res = await route.fetch();
    const body = await res.json();
    body.push({
      badge: {
        id: 'perfectionist', name_es: 'Perfeccionista', name_en: 'Perfectionist', icon: '🌟',
        description_es: 'Sesión perfecta 10/10', description_en: 'Perfect 10/10 session',
        criteria_type: 'perfect_session', criteria_value: 1,
      },
      earned_at: new Date().toISOString(),
    });
    await route.fulfill({ response: res, json: body });
  });
  await page.getByRole('button', { name: 'Yo', exact: true }).click();
  const grid = page.getByTestId('badges-grid');
  await expect(grid).toHaveAttribute('data-enter', 'stagger');
  await expect(grid.locator('[data-fx="new"]').first()).toBeVisible({ timeout: 10_000 });
  await grid.scrollIntoViewIfNeeded();
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${SHOTS}/perfil-insignia-nueva-es-390.png` });
  await axe0(page);

  // Estadísticas.
  await page.route('**/progress/dashboard', async (route) => {
    const res = await route.fetch();
    const body = await res.json();
    for (const tr of body.tracks) if (tr.average_mastery > 0) tr.skills_mastered = Math.max(tr.skills_mastered, 2);
    await route.fulfill({ response: res, json: body });
  });
  await page.getByRole('button', { name: 'Estadísticas' }).click();
  await expect(page.locator('[data-fx="grow"]').first()).toBeVisible({ timeout: 10_000 });
  for (const list of await page.getByRole('list').all()) await expect(list).toHaveAttribute('data-enter', 'stagger');
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${SHOTS}/estadisticas-es-390.png` });
  await axe0(page);

  // Cartera.
  await page.getByRole('button', { name: 'Yo', exact: true }).click();
  await page.getByRole('button', { name: 'Cartera' }).click();
  await expect(page.getByRole('list').first()).toHaveAttribute('data-enter', 'stagger', { timeout: 10_000 });
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${SHOTS}/cartera-es-390.png` });
  await axe0(page);
});

const CERT = {
  code: 'a'.repeat(32), username: 'ada', track_id: 'track01', track_name_es: 'Python Básico',
  track_name_en: 'Python Basics', score_pct: 86.5, questions: 50, issued_at: '2026-10-20T10:00:00Z',
  revoked: false, is_certification: false,
};

// Solo ES: la página pública del certificado sale siempre en español para un
// visitante sin cuenta (aplica `user.language` del store, 'es' por defecto) —
// hallazgo aparte, en el README. Una captura «EN» en español engañaría.
for (const width of [390, 1280]) {
  const lang = 'es';
  test(`certificado válido: el sello se dibuja (${lang}, ${width} px)`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.route('**/exams/certificates/*', (route) => route.fulfill({ json: CERT }));
    await page.goto(`/certificate/${CERT.code}`);
    await expect(page.getByTestId('drawn-check')).toHaveAttribute('data-fx', 'draw');
    await page.waitForTimeout(800);
    await page.screenshot({ path: `${SHOTS}/certificado-${lang}-${width}.png` });
    await axe0(page);
  });
}

test('certificado revocado: sin sello', async ({ page }) => {
  await page.route('**/exams/certificates/*', (route) => route.fulfill({ json: { ...CERT, revoked: true } }));
  await page.goto(`/certificate/${CERT.code}`);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  await page.waitForTimeout(500);
  await expect(page.getByTestId('drawn-check')).toHaveCount(0);
});
