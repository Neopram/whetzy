import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { answerCurrentQuestion, formatViolations, markLessonSeen, registerUser, uniqueUsername } from './helpers';

/**
 * Tutor por modos (ola 2, 2026-10-21). Contra el backend real para registro y
 * sesión; el plan y el tutor se simulan en la red (`/auth/me` con Pro o Pro
 * Max y `/tutor/explain` con un texto por modo), porque en local no hay
 * pagos ni clave del LLM. Lo que se mira es la interfaz: los tres modos, el
 * aviso de Pro Max sin llamar al servidor y axe 0.
 */
const SHOTS = '../docs/ui-snapshots/tutor-modos';

async function asPlan(page: Page, deep: boolean, calls: string[]) {
  await page.route('**/api/v1/auth/me', async (route) => {
    if (route.request().method() !== 'GET') return route.continue();
    const res = await route.fetch();
    const body = { ...(await res.json()), is_premium: true, tutor_deep_access: deep };
    await route.fulfill({ response: res, json: body });
  });
  await page.route('**/api/v1/tutor/explain', async (route) => {
    const { mode } = route.request().postDataJSON() as { mode: string };
    calls.push(mode);
    const text: Record<string, string> = {
      why: 'Porque `len("Python")` cuenta los caracteres: son 6.',
      how: '1. Escribe la cadena.\n2. Cuenta sus caracteres.\n3. `len` devuelve ese número: 6.',
      deep: 'Concepto: `len` devuelve el número de elementos… (respuesta larga de ejemplo)',
    };
    await route.fulfill({ json: { explanation: text[mode], provider: 'demo', grounded: true, times_missed: 0, mode } });
  });
}

async function openTutor(page: Page) {
  await markLessonSeen(page);
  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
  await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });
  await answerCurrentQuestion(page);
  await page.getByRole('button', { name: '¿Por qué?', expanded: false }).click();
  return page.getByRole('group', { name: 'Modo del tutor' });
}

async function axe0(page: Page) {
  const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  expect(r.violations, formatViolations(r.violations)).toHaveLength(0);
}

for (const width of [390, 1280]) {
  test(`Pro: ¿Por qué?, ¿Cómo? y el aviso de «A fondo» (${width} px)`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    const calls: string[] = [];
    await asPlan(page, false, calls);
    await registerUser(page, { username: uniqueUsername('e2e_tmodo_'), displayName: 'Modos' });
    await page.reload();
    const modes = await openTutor(page);
    await expect(page.getByText('son 6.')).toBeVisible();
    await modes.getByRole('button', { name: '¿Cómo?' }).click();
    await expect(page.getByText('Cuenta sus caracteres')).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/pro-como-es-${width}.png`, fullPage: true });
    await axe0(page);
    await modes.getByRole('button', { name: /A fondo/ }).click();
    await expect(page.getByText('«A fondo» es de Pro Max')).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/pro-a-fondo-aviso-es-${width}.png`, fullPage: true });
    await axe0(page);
    expect(calls).toEqual(['why', 'how']);
  });
}

test('Pro Max: «A fondo» se pide (390 px)', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  const calls: string[] = [];
  await asPlan(page, true, calls);
  await registerUser(page, { username: uniqueUsername('e2e_tmodo_max_'), displayName: 'Modos' });
  await page.reload();
  const modes = await openTutor(page);
  await modes.getByRole('button', { name: 'A fondo' }).click();
  await expect(page.getByText('respuesta larga de ejemplo')).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/promax-a-fondo-es-390.png`, fullPage: true });
  await axe0(page);
  expect(calls).toEqual(['why', 'deep']);
});
