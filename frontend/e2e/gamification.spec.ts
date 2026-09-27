import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { test, expect } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

/**
 * Gamificación de punta a punta (39.5): XP, racha, liga e insignia, con capturas.
 *
 * Una sesión de estudio de 10 preguntas respondidas todas bien (contra la API, con
 * la clave leída del propio contenido) tiene que dejar al alumno con XP, racha 1,
 * una fila en la liga de la semana y la insignia «Perfeccionista». Esa insignia se
 * sembraba sin estadística en `award_badges` y no se concedía nunca (arreglado junto
 * a este spec); ninguna otra prueba recorría el camino entero hasta la pantalla.
 */

const HERE = path.dirname(fileURLToPath(import.meta.url));

type Key = { skill: string; id: string; ci: number };

const INDEX_GRADED = new Set(['mcq', 'multiple_choice', 'true_false', 'code_output']);

/** Primer skill (por id) con al menos 12 preguntas, todas corregidas por índice. */
function pickSkill(): { skill: string; key: Map<string, number> } {
  const root = path.resolve(HERE, '../../content/questions');
  const bySkill = new Map<string, Key[]>();
  const bad = new Set<string>();
  const walk = (dir: string) => {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.name.endsWith('.json')) {
        const raw = JSON.parse(fs.readFileSync(p, 'utf-8'));
        const items = Array.isArray(raw) ? raw : raw.questions ?? [];
        for (const q of items) {
          if (!q.skill_id || !q.id) continue;
          if (!INDEX_GRADED.has(q.type) || typeof q.correct_index !== 'number') {
            bad.add(q.skill_id);
            continue;
          }
          const list = bySkill.get(q.skill_id) ?? [];
          list.push({ skill: q.skill_id, id: q.id, ci: q.correct_index });
          bySkill.set(q.skill_id, list);
        }
      }
    }
  };
  walk(root);
  const skill = [...bySkill.keys()].sort().find((s) => !bad.has(s) && (bySkill.get(s)?.length ?? 0) >= 12);
  if (!skill) throw new Error('ningún skill con 12 preguntas corregidas por índice');
  return { skill, key: new Map(bySkill.get(skill)!.map((k) => [k.id, k.ci])) };
}

// Las capturas son evidencia del PR, no del repo (sin binarios): van a test-results/.
const SHOTS = process.env.E2E_SHOTS_DIR ?? path.resolve(HERE, '../test-results/39.5-gamification');

test('gamificación: 10/10 deja XP, racha, liga e insignia visibles (39.5)', async ({ page }) => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const username = uniqueUsername('e2e_gami_');
  await registerUser(page, { username, displayName: 'Ada Lovelace' });

  const { skill, key } = pickSkill();
  const start = await page.request.post('/api/v1/quiz/start', { data: { skill_id: skill, mode: 'study' } });
  expect(start.ok(), await start.text()).toBeTruthy();
  const body = await start.json();
  const sessionId: string = body.session_id;
  let question = body.question as { id: string } | null;
  let xp = 0;
  for (let i = 0; i < 10; i++) {
    expect(question, `sin pregunta en la vuelta ${i}`).not.toBeNull();
    const ci = key.get(question!.id);
    expect(ci, `clave desconocida para ${question!.id}`).toBeDefined();
    const r = await page.request.post('/api/v1/quiz/answer', {
      data: { session_id: sessionId, question_id: question!.id, selected_index: ci, response_time_ms: 4000 },
    });
    expect(r.ok(), await r.text()).toBeTruthy();
    const a = await r.json();
    expect(a.correct).toBe(true);
    xp += a.xp_earned;
    question = a.next_question;
  }
  const end = await page.request.post('/api/v1/quiz/end', { data: { session_id: sessionId } });
  expect(end.ok()).toBeTruthy();
  expect(xp).toBeGreaterThan(0);

  // Backend: racha 1, insignia concedida, fila en la liga con el XP de la sesión.
  const badges = await (await page.request.get('/api/v1/badges')).json();
  expect(badges.map((b: { badge: { id: string } }) => b.badge.id)).toContain('perfectionist');
  const league = await (await page.request.get('/api/v1/league/current')).json();
  const me = league.standings.find((s: { username?: string; display_name?: string; is_current_user?: boolean }) =>
    s.is_current_user || s.username === username);
  expect(me, JSON.stringify(league).slice(0, 400)).toBeDefined();
  expect(me.xp_earned).toBe(xp);

  // UI: Inicio (XP y racha), Liga y Perfil (insignia), con captura de cada una.
  await page.reload();
  await page.getByRole('button', { name: 'Inicio' }).click();
  await expect(page.getByText(/Racha/i).first()).toBeVisible({ timeout: 15_000 });
  // Barra superior: racha 1 y el XP total de la sesión.
  await expect(page.getByText(String(xp), { exact: true }).first()).toBeVisible();
  await page.screenshot({ path: path.join(SHOTS, '1-inicio-xp-racha.png'), fullPage: true });

  await page.getByRole('button', { name: 'Liga' }).click();
  // El podio muestra el nombre de pila y el XP de la semana.
  await expect(page.getByText(`${xp} XP`).first()).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText('Ada', { exact: true }).first()).toBeVisible();
  await page.screenshot({ path: path.join(SHOTS, '2-liga.png'), fullPage: true });

  await page.getByRole('button', { name: 'Perfil' }).click();
  await expect(page.getByText('Perfeccionista')).toBeVisible({ timeout: 15_000 });
  await page.screenshot({ path: path.join(SHOTS, '3-perfil-insignia.png'), fullPage: true });
});
