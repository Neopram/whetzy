import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { completeOnboarding, formatViolations, registerUser, uniqueUsername } from './helpers';

/**
 * 46.15 bloque B (docs/PLAN_UI_AVANZADA.md §7.5), contra el backend real:
 * - Lección: el ejemplo se copia de verdad (portapapeles) y dice «Copiado».
 * - Rutas: la skill que subió de banda desde la última visita late una vez.
 *   Subir de banda pide 7 respuestas; para no contestarlas aquí se sube el
 *   número de intentos en la respuesta de `/progress/curriculum` (solo ese
 *   dato; el resto es el del servidor).
 * - Proyecto: el servidor ejecuta los tests SQL; si los da por buenos, el aviso
 *   entra con efecto. Proyecto sembrado por `backend/scripts/seed_e2e_project.py`.
 */
const SHOTS = '../docs/ui-snapshots/46.15b';
const STEP1 = "CREATE TABLE pets(name TEXT, age INT); INSERT INTO pets VALUES ('Rex', 9), ('Mia', 2);";

async function axe0(page: Page, opts: { skipEditor?: boolean } = {}) {
  let builder = new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']);
  // El resaltado del tema `vs-dark` de Monaco pinta las cadenas en #ff0000 sobre
  // #1e1e1e (4,16:1). Es del editor, no de este bloque; queda anotado en el
  // README de 46.15b como hallazgo aparte.
  if (opts.skipEditor) builder = builder.exclude('.monaco-editor');
  const r = await builder.analyze();
  expect(r.violations, formatViolations(r.violations)).toHaveLength(0);
}

test.beforeAll(() => {
  execFileSync('python', ['scripts/seed_e2e_project.py'], {
    cwd: path.resolve(process.cwd(), '../backend'),
    env: process.env,
    stdio: 'inherit',
  });
});

for (const [lang, width] of [['es', 390], ['en', 1280]] as const) {
  test.describe(`lección (${lang})`, () => {
    test.use({ locale: lang === 'es' ? 'es-ES' : 'en-US' });

    test(`copiar el ejemplo: va al portapapeles y dice «Copiado» (${width} px)`, async ({ page, context }) => {
      await context.grantPermissions(['clipboard-read', 'clipboard-write']);
      await page.setViewportSize({ width, height: 900 });
      const username = uniqueUsername('e2e_copia_');
      await page.goto('/auth');
      await page.getByLabel(lang === 'es' ? 'Nombre' : 'Name', { exact: true }).fill('Copia');
      await page.getByLabel(lang === 'es' ? 'Usuario' : 'Username').fill(username);
      await page.getByLabel(lang === 'es' ? 'Correo electrónico' : 'Email').fill(`${username}@example.com`);
      await page.getByLabel(lang === 'es' ? 'Contraseña' : 'Password').fill('e2e-test-pass-123');
      await page.getByRole('checkbox').check();
      await page.getByRole('button', { name: lang === 'es' ? 'EMPEZAR A APRENDER' : 'START LEARNING' }).click();
      await completeOnboarding(page, { lang });
      await page.getByRole('button', { name: lang === 'es' ? 'ESTUDIAR AHORA' : 'STUDY NOW' }).click();

      // → avanza un paso y se para en el último, que es el ejemplo.
      await expect(page.getByRole('progressbar', { name: /Paso|Step/ })).toBeVisible({ timeout: 15_000 });
      for (let i = 0; i < 12; i++) await page.keyboard.press('ArrowRight');
      const copy = page.getByRole('button', { name: lang === 'es' ? 'Copiar código' : 'Copy code' });
      await copy.click();
      await expect(page.getByRole('status').filter({ hasText: lang === 'es' ? 'Copiado' : 'Copied' })).toBeVisible();
      const code = await page.locator('pre code').first().innerText();
      expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(code);
      await page.screenshot({ path: `${SHOTS}/copiado-${lang}-${width}.png` });
      await axe0(page);
    });
  });
}

/** La primera skill del primer módulo pasa a tener 8 respuestas (60 % bien): «En desarrollo». */
async function raiseFirstSkill(page: Page): Promise<string> {
  let raised = '';
  await page.route('**/progress/curriculum?**', async (route) => {
    const res = await route.fetch();
    const body = await res.json();
    const s = body.modules[0].skills[0];
    s.attempts = 8;
    s.correct_count = 5;
    raised = s.skill_id;
    await route.fulfill({ response: res, json: body });
  });
  return new Promise((resolve) => {
    const tick = () => (raised ? resolve(raised) : setTimeout(tick, 50));
    tick();
  });
}

async function seedSnapshot(page: Page, skillId: string) {
  // Primero, que la visita de verdad haya guardado su foto; si no, su efecto
  // la escribe después y pisa la que sembramos.
  await expect.poll(() => page.evaluate((id) => {
    type Store = { getState: () => { user: { id: string } } };
    const uid = (window as unknown as { __whetzyStore: Store }).__whetzyStore.getState().user.id;
    return localStorage.getItem(`whetzy_fx_bands_tracks_${uid}`)?.includes(id) ?? false;
  }, skillId)).toBe(true);
  await page.evaluate((id) => {
    type Store = { getState: () => { user: { id: string } } };
    const uid = (window as unknown as { __whetzyStore: Store }).__whetzyStore.getState().user.id;
    localStorage.setItem(`whetzy_fx_bands_tracks_${uid}`, JSON.stringify({ [id]: 'insufficient' }));
  }, skillId);
}

for (const width of [390, 1280]) {
  test(`rutas: la skill que subió late y su módulo lo avisa (es, ${width} px)`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await registerUser(page, { username: uniqueUsername('e2e_sube_'), displayName: 'Sube' });
    // Primera visita: deja la foto «real» y aprendemos qué skill se sube.
    const raisedP = raiseFirstSkill(page);
    await page.getByRole('button', { name: 'Rutas', exact: true }).click();
    const skillId = await raisedP;
    const header = page.locator('[class*="moduleHeader_"]').first();
    await expect(header).toBeVisible({ timeout: 20_000 });
    // La foto dice que esa skill estaba en «Evidencia insuficiente»; ahora está en desarrollo.
    await seedSnapshot(page, skillId);
    // Otra sesión: volver de Hoy no remonta Rutas (la pantalla sigue viva), así
    // que «desde la última visita» se prueba recargando.
    await page.reload();
    await page.getByRole('button', { name: 'Rutas', exact: true }).click();
    await expect(header).toHaveAttribute('data-fx', 'band-up', { timeout: 20_000 });
    await header.click();
    const up = page.locator('[data-testid="skill-band"][data-fx="band-up"]');
    await expect(up).toHaveCount(1);
    await expect(up).toContainText('En desarrollo');
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${SHOTS}/rutas-sube-es-${width}.png` });
    await axe0(page);
  });
}

test('rutas con movimiento reducido: nada late aunque haya subido', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await registerUser(page, { username: uniqueUsername('e2e_sube_rm_'), displayName: 'Sube' });
  const raisedP = raiseFirstSkill(page);
  await page.getByRole('button', { name: 'Rutas', exact: true }).click();
  const skillId = await raisedP;
  const header = page.locator('[class*="moduleHeader_"]').first();
  await expect(header).toBeVisible({ timeout: 20_000 });
  await seedSnapshot(page, skillId);
  await page.reload();
  await page.getByRole('button', { name: 'Rutas', exact: true }).click();
  await expect(header).toBeVisible();
  await page.waitForTimeout(500);
  await expect(header).not.toHaveAttribute('data-fx', /.+/);
});

test('proyecto: el servidor acepta el paso y el aviso entra con efecto (es, 390 px)', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  await registerUser(page, { username: uniqueUsername('e2e_pasa_'), displayName: 'Pasa' });
  await page.getByRole('button', { name: /Proyectos/ }).first().click();
  await page.getByText('Mascotas (E2E)').click();
  await expect(page.getByText('Paso 1: Crea la tabla')).toBeVisible();
  const editor = page.locator('.monaco-editor').first();
  await expect(editor).toBeVisible({ timeout: 20_000 });
  await editor.click();
  await page.keyboard.press('ControlOrMeta+A');
  await page.keyboard.insertText(STEP1);
  await page.getByRole('button', { name: 'Probar' }).click();
  const pass = page.getByText('✅ ¡Todos los tests pasaron!');
  await expect(pass).toBeVisible({ timeout: 20_000 });
  await expect(pass).toHaveAttribute('data-fx', 'pass');
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${SHOTS}/proyecto-pasa-es-390.png` });
  await axe0(page, { skipEditor: true });
});
