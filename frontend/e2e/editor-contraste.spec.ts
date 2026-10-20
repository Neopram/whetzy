import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerUser, uniqueUsername } from './helpers';

/**
 * El editor de código con el tema propio (`lib/monacoTheme.ts`), contra el
 * backend real y en Chromium: cada fragmento coloreado de una consulta SQL
 * (cadena, comentario, palabra clave, número) llega a 4,5:1 sobre el fondo del
 * editor, y axe no excluye `.monaco-editor`.
 *
 * Antes: con `vs-dark`, las cadenas SQL salían en rojo puro (#FF0000) sobre
 * #1E1E1E, 4,17:1, y los e2e de Aprender tenían que sacar el editor de axe.
 * Usa el proyecto SQL que siembra `backend/scripts/seed_e2e_project.py`.
 */
const SHOTS = '../docs/ui-snapshots/editor-contraste';

test.beforeAll(() => {
  execFileSync('python', ['scripts/seed_e2e_project.py'], {
    cwd: path.resolve(process.cwd(), '../backend'),
    env: process.env,
    stdio: 'inherit',
  });
});

test('editor SQL: cada token llega a 4,5:1 y axe lo revisa entero (es, 390 px)', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  await registerUser(page, { username: uniqueUsername('e2e_mon_'), displayName: 'Editor' });
  await page.getByRole('button', { name: /Proyectos/ }).first().click();
  await page.getByText('Mascotas (E2E)').click();
  const editor = page.locator('.monaco-editor');
  await expect(editor).toBeVisible({ timeout: 15_000 });
  await editor.click();
  await page.keyboard.press('Control+End');
  await page.keyboard.press('Enter');
  // insertText: sin eventos de tecla, el autocompletado de Monaco no se come letras.
  await page.keyboard.insertText("-- mascotas mayores\nSELECT name FROM pets WHERE age > 3 AND name <> 'Rex';");
  await expect(editor.locator('.view-lines')).toContainText("'Rex'");

  const medidas = await editor.evaluate((root) => {
    const rgb = (c: string) => (c.match(/\d+(\.\d+)?/g) ?? []).slice(0, 3).map(Number);
    const lum = ([r, g, b]: number[]) => {
      const f = (v: number) => { const s = v / 255; return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; };
      return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
    };
    const fondo = lum(rgb(getComputedStyle(root.querySelector('.monaco-editor-background') ?? root).backgroundColor));
    return [...root.querySelectorAll('.view-line span span')]
      .filter((s) => s.textContent?.trim())
      .map((s) => {
        const l = lum(rgb(getComputedStyle(s).color));
        return { texto: s.textContent!.trim(), ratio: (Math.max(l, fondo) + 0.05) / (Math.min(l, fondo) + 0.05) };
      });
  });
  expect(medidas.some((m) => m.texto.includes("'Rex'"))).toBe(true);
  expect(medidas.filter((m) => m.ratio < 4.5)).toEqual([]);

  await page.screenshot({ path: `${SHOTS}/editor-sql-es-390.png` });
  const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  expect(r.violations, formatViolations(r.violations)).toHaveLength(0);
});
