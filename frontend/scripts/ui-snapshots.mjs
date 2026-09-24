#!/usr/bin/env node
/**
 * Capturas de todas las pantallas (serie 34, tarea 34.8).
 *
 * Para revisar la interfaz sin clicar a mano: registra un usuario nuevo contra
 * el backend local, abre cada pantalla y guarda una captura por pantalla,
 * idioma y tamaño. Es el bucle de trabajo de la serie 34: cambiar CSS → correr
 * esto → mirar las capturas → repetir.
 *
 * Requisitos (los mismos que los e2e): backend en :8000 con contenido cargado
 * y `npm run dev -- --port 5199`. Las pantallas internas se abren con el gancho
 * `window.__whetzyStore` que `main.tsx` expone SOLO en desarrollo.
 *
 * Uso:
 *   node scripts/ui-snapshots.mjs                       # todo → ui-snapshots/
 *   node scripts/ui-snapshots.mjs --only auth,home      # algunas pantallas
 *   node scripts/ui-snapshots.mjs --lang es --vp mobile
 *   UI_BASE=http://localhost:5199 UI_API=http://127.0.0.1:8000/api/v1 CHROMIUM_PATH=/opt/pw-browsers/chromium ...
 */
import { mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { chromium } from '@playwright/test';

const BASE = process.env.UI_BASE ?? 'http://localhost:5199';
const API = process.env.UI_API ?? 'http://127.0.0.1:8000/api/v1';
const OUT = resolve(process.env.UI_OUT ?? 'ui-snapshots');

const arg = (name) => {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 ? process.argv[i + 1] : undefined;
};
const only = arg('only')?.split(',');
const LANGS = (arg('lang') ?? 'es,en').split(',');
const VIEWPORTS = { mobile: { width: 390, height: 844 }, desktop: { width: 1280, height: 800 } };
const VPS = (arg('vp') ?? 'mobile,desktop').split(',');

/** Pantallas públicas: URL propia, sin sesión. */
const PUBLIC = [
  { name: 'landing', path: '/landing' },
  { name: 'auth', path: '/auth' },
  { name: 'privacy', path: '/privacy' },
  { name: 'terms', path: '/terms' },
  { name: 'evidence', path: '/evidence' },
  { name: 'delete-account', path: '/delete-account' },
  { name: 'admin', path: '/admin' },
];
/** Pantallas internas: se abren con setScreen(). */
const INTERNAL = [
  'home', 'tracks', 'quiz', 'stats', 'league', 'profile', 'duels', 'marketplace', 'instructor',
  'lesson', 'placement', 'readiness', 'mockexam', 'trackexam',
];
/** Cómo se abre cada pantalla interna (por defecto, setScreen). */
const OPEN = {
  quiz: (st) => st.startQuiz('study', 10, { trackId: 'track01' }),
  lesson: (st) => st.startLesson('sk010101'),
  placement: (st) => st.startPlacement('track01'),
  readiness: (st) => st.startReadiness('track08'),
  mockexam: (st) => st.startMockExam('track08', 10, 20),
  trackexam: (st) => st.startTrackExam('track', 'track01', { questions: 10, durationMinutes: 20, passPct: 70 }),
};

async function newUser(lang) {
  const id = `ui${Date.now()}${Math.floor(Math.random() * 1e4)}`;
  const res = await fetch(`${API}/auth/register`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      email: `${id}@example.com`,
      username: id,
      display_name: 'UI Snapshot',
      password: 'snapshot-password-123',
      language: lang,
    }),
  });
  if (!res.ok) throw new Error(`register ${res.status}: ${await res.text()}`);
  const tokens = await res.json();
  const me = await (await fetch(`${API}/auth/me`, { headers: { authorization: `Bearer ${tokens.access_token}` } })).json();
  return { ...tokens, userId: me.id };
}

/** Pantallas con scroll horizontal (ancho del documento > viewport): en móvil es un fallo. */
const overflow = [];
async function checkOverflow(page, label) {
  const { sw, vw } = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, vw: document.documentElement.clientWidth }));
  if (sw > vw + 1) overflow.push(`${label}: ${sw}px > ${vw}px`);
}

const want = (name) => !only || only.includes(name) || (name === 'quiz-feedback' && only.includes('quiz'));

async function main() {
  mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch(
    process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
  );
  const shots = [];
  try {
    for (const lang of LANGS) {
      const user = await newUser(lang);
      for (const vp of VPS) {
        for (const p of PUBLIC.filter((x) => want(x.name))) {
          const ctx = await browser.newContext({ viewport: VIEWPORTS[vp], locale: lang });
          await ctx.addInitScript((l) => localStorage.setItem('i18nextLng', l), lang);
          const page = await ctx.newPage();
          try {
            // `load` y no `networkidle`: /admin sondea el backend sin parar.
            await page.goto(`${BASE}${p.path}${p.path.includes('?') ? '&' : '?'}lang=${lang}`, { waitUntil: 'load' });
            await page.waitForTimeout(1500);
            const file = `${OUT}/${p.name}-${lang}-${vp}.png`;
            await checkOverflow(page, `${p.name}-${lang}-${vp}`);
            await page.screenshot({ path: file, fullPage: true });
            shots.push(file);
          } catch (err) {
            console.error(`[ui-snapshots] ${p.name}: ${err.message.split('\n')[0]}`);
          }
          await ctx.close();
        }
        const internal = INTERNAL.filter(want);
        if (!internal.length) continue;
        const ctx = await browser.newContext({ viewport: VIEWPORTS[vp], locale: lang });
        await ctx.addInitScript(
          ({ u, l }) => {
            localStorage.setItem('whetzy_access_token', u.access_token);
            localStorage.setItem('whetzy_refresh_token', u.refresh_token);
            localStorage.setItem(`whetzy_onboarded_${u.userId}`, '1');
            localStorage.setItem('i18nextLng', l);
          },
          { u: user, l: lang },
        );
        const page = await ctx.newPage();
        await page.goto(`${BASE}/`, { waitUntil: 'networkidle' });
        await page.waitForFunction(() => '__whetzyStore' in window, null, { timeout: 20_000 });
        for (const screen of internal) {
          // El quiz necesita una sesión: setScreen('quiz') a secas se queda en «Cargando…».
          await page.evaluate(
            ({ s, fn }) => {
              const st = window.__whetzyStore.getState();
              if (fn) new Function('st', `(${fn})(st)`)(st);
              else st.setScreen(s);
            },
            { s: screen, fn: OPEN[screen]?.toString() },
          );
          await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});
          await page.waitForTimeout(1200);
          const file = `${OUT}/${screen}-${lang}-${vp}.png`;
          await checkOverflow(page, `${screen}-${lang}-${vp}`);
          await page.screenshot({ path: file, fullPage: true });
          shots.push(file);
          if (screen === 'quiz' && want('quiz-feedback')) {
            // Responder la primera opción para capturar el feedback (correcto o no).
            const opt = page.locator('[class*="option_"]').first();
            if (await opt.isVisible().catch(() => false)) {
              await opt.click();
              const verify = page.locator('[class*="btnVerify_"]');
              if (await verify.isVisible().catch(() => false)) await verify.click();
              await page.waitForTimeout(800);
              const fb = `${OUT}/quiz-feedback-${lang}-${vp}.png`;
              await page.screenshot({ path: fb, fullPage: true });
              shots.push(fb);
            }
          }
        }
        await ctx.close();
        if (want('onboarding')) {
          const oc = await browser.newContext({ viewport: VIEWPORTS[vp], locale: lang });
          await oc.addInitScript(
            ({ u, l }) => {
              localStorage.setItem('whetzy_access_token', u.access_token);
              localStorage.setItem('whetzy_refresh_token', u.refresh_token);
              localStorage.removeItem(`whetzy_onboarded_${u.userId}`);
              localStorage.setItem('i18nextLng', l);
            },
            { u: user, l: lang },
          );
          const op = await oc.newPage();
          await op.goto(`${BASE}/`, { waitUntil: 'networkidle' });
          await op.waitForTimeout(1200);
          const file = `${OUT}/onboarding-${lang}-${vp}.png`;
          await op.screenshot({ path: file, fullPage: true });
          shots.push(file);
          await oc.close();
        }
      }
    }
  } finally {
    await browser.close();
  }
  console.log(`[ui-snapshots] ${shots.length} capturas en ${OUT}`);
  if (overflow.length) {
    console.error(`[ui-snapshots] FAIL — scroll horizontal en ${overflow.length}:\n  ${overflow.join('\n  ')}`);
    process.exitCode = 1;
  }
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
