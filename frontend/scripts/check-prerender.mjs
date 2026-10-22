#!/usr/bin/env node
/**
 * Prerender-output check (task 12.10).
 *
 * Task 11.11 prerenders the landing hero into dist/landing/index.html so the
 * LCP element paints with the initial HTML response instead of waiting for the
 * React bundle. It works — measured at the URL that actually serves it, mobile
 * LCP is 1.606 ms (devtools) against a 2.500 ms budget.
 *
 * The problem this check exists for is that nothing ever ran it. CI built with
 * `npx vite build`, while the prerender lives in the `build` script of
 * package.json, so `scripts/prerender-landing.mjs` never executed in CI: had it
 * started emitting a broken file, or no file, CI would have stayed green and
 * the only symptom would have been a slower landing page that nobody measured.
 * The e2e suite does not cover it either — it runs against `npm run dev`, which
 * serves from source and never looks at dist/ at all.
 *
 * So CI now builds with `npm run build` (the command that produces what gets
 * deployed) and this asserts the output is really there. Keeping the assertion
 * here rather than trusting the build script's own internal throw is the point:
 * if someone switches CI back to `npx vite build`, the file is simply absent
 * and this fails, which is exactly the regression that went unnoticed before.
 *
 * Run after a build:  node scripts/check-prerender.mjs
 */
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const LANDING = resolve(process.cwd(), 'dist', 'landing', 'index.html');

/** Each check names what breaks in the product if it fails, not just what is missing. */
const REQUIRED = [
  {
    needle: 'data-lcp="hero"',
    why: 'the prerendered hero <h1> — without it the LCP element waits for the JS bundle, which is the whole point of 11.11',
  },
  {
    needle: 'Aprende Python, IA y ciberseguridad',
    why: 'the real hero copy — a rendered-but-empty shell would pass a class-name check while painting nothing',
  },
  {
    needle: '¿Cuesta algo empezar?',
    why: 'the FAQ (2026-10-15) — its answers are <details>, so they must be in the static HTML that search engines read, not added by JS',
  },
  {
    needle: 'Evidencia insuficiente',
    why: 'the per-domain readiness bands (ADR-60) — the landing promises bands, not a percentage, and the static HTML must show them',
  },
  {
    needle: '"@type":"SoftwareApplication"',
    why: 'the schema.org JSON-LD (ola 2, 2026-10-21) — search engines read it from the static HTML, so it must be prerendered, not injected by JS',
  },
  {
    needle: 'LandingScreen',
    why: "the route-level stylesheet link — without it the hero paints at the browser's default size and repaints larger once the JS applies the real CSS, and Chrome reports that second, bigger paint as the LCP",
  },
];

if (!existsSync(LANDING)) {
  console.error(
    '\n[prerender] FAIL — dist/landing/index.html does not exist.\n' +
      '  The landing prerender did not run. It lives in the "build" script of package.json,\n' +
      '  so building with a bare `npx vite build` silently skips it (that is exactly how this\n' +
      '  went unnoticed in CI — see task 12.10). Build with `npm run build`.\n',
  );
  process.exit(1);
}

const html = readFileSync(LANDING, 'utf-8');
const missing = REQUIRED.filter(({ needle }) => !html.includes(needle));

console.log(`\n[prerender] checking dist/landing/index.html (${html.length} bytes)\n`);

/*
 * Las páginas legales (2026-10-21). La revisión de dominio de Paddle exige Términos, Privacidad y
 * Reembolsos accesibles, y un revisor o una herramienta que no ejecuta JS veía el shell vacío
 * (3.289 B sin texto). Cada una tiene que llegar con su título y con el texto de su primera sección.
 */
const LEGAL = [
  { file: 'terms', needles: ['Términos de Servicio', '1. Aceptación'] },
  { file: 'privacy', needles: ['Política de Privacidad', '1. Información que recopilamos'] },
  { file: 'refund', needles: ['Política de reembolsos'] },
];
for (const { file, needles } of LEGAL) {
  const path = resolve(process.cwd(), 'dist', file, 'index.html');
  const page = existsSync(path) ? readFileSync(path, 'utf-8') : '';
  for (const needle of needles) {
    if (!page.includes(needle)) {
      missing.push({
        needle: `dist/${file}/index.html: ${needle}`,
        why: 'the legal page must carry its text in the static HTML — Paddle\'s domain review (and any crawler) reads it without running JS',
      });
    }
  }
}

if (missing.length > 0) {
  for (const { needle, why } of missing) {
    console.error(`  FAIL  missing ${JSON.stringify(needle)}\n        ${why}`);
  }
  console.error(`\n[prerender] FAIL — ${missing.length} missing marker(s) in the prerendered pages.\n`);
  process.exit(1);
}

console.log(`[prerender] PASS — hero, copy, FAQ, bands, route stylesheet and the three legal pages all present\n`);
