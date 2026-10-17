import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { test, expect, type Page } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

/**
 * 43.6 (ADR-65 D8), contra el backend real: el progreso de un proyecto vive en
 * el servidor y `passed=true` sin pasar los tests no completa.
 *
 * Antes: `submit-step` se creía el `passed` del cliente y cualquier
 * `step_number`, y la pantalla guardaba el paso y el código solo en memoria.
 *
 * El catálogo no trae proyectos (y `content_loader` no los carga), así que el
 * spec siembra uno SQL de dos pasos con `backend/scripts/seed_e2e_project.py`.
 */

const SLUG = 'e2e-sql-mascotas';
const STEP1 = "CREATE TABLE pets(name TEXT, age INT); INSERT INTO pets VALUES ('Rex', 9), ('Mia', 2);";

test.beforeAll(() => {
  execFileSync('python', ['scripts/seed_e2e_project.py'], {
    cwd: path.resolve(process.cwd(), '../backend'),
    env: process.env,
    stdio: 'inherit',
  });
});

/** POST desde la página: lleva la sesión (cookie o token) y el Origin. */
async function submit(page: Page, n: number, code: string, passed: boolean) {
  return page.evaluate(
    async ({ slug, n, code, passed }) => {
      const r = await fetch(`/api/v1/projects/${slug}/submit-step`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ step_number: n, code, passed }),
      });
      return { status: r.status, body: await r.json() };
    },
    { slug: SLUG, n, code, passed },
  );
}

async function openProject(page: Page) {
  await page.getByRole('button', { name: /Proyectos/ }).first().click();
  await page.getByText('Mascotas (E2E)').click();
}

test('el progreso del proyecto sobrevive a salir y el servidor decide en SQL', async ({ page }) => {
  await registerUser(page, { username: uniqueUsername('proy'), displayName: 'Proyectos E2E' });

  // Abrirlo lo empieza en el servidor.
  await openProject(page);
  await expect(page.getByText('Paso 1: Crea la tabla')).toBeVisible();
  await expect(page.getByText(/Tu progreso y tu código se guardan/)).toBeVisible();

  // El servidor ejecuta los tests: decir que pasa no basta.
  const lie = await submit(page, 1, 'SELECT 1;', true);
  expect(lie.status).toBe(200);
  expect(lie.body.step_passed).toBe(false);
  expect(lie.body.current_step).toBe(1);

  // Saltar al último paso tampoco.
  expect((await submit(page, 2, 'SELECT 1;', true)).status).toBe(409);

  // El código bueno pasa aunque el cliente diga que no.
  const ok = await submit(page, 1, STEP1, false);
  expect(ok.body.step_passed).toBe(true);
  expect(ok.body.current_step).toBe(2);

  // Salir del todo y volver: retoma en el paso 2, con el 1 hecho y su código.
  await page.reload();
  await expect(page.getByRole('button', { name: 'Hoy', exact: true })).toBeVisible({ timeout: 15_000 });
  await openProject(page);
  await expect(page.getByText('Paso 2: La mayor')).toBeVisible();
  await expect(page.getByText('1/2')).toBeVisible();
  await page.getByRole('button', { name: '1 ✓' }).click();
  await expect(page.locator('.monaco-editor .view-lines')).toContainText('CREATE TABLE pets', { timeout: 15_000 });
});
