#!/usr/bin/env node
/**
 * Bundle-size budget check (8.3).
 *
 * Reads the Vite dist/ output, gzip-compresses each JS/CSS asset in memory,
 * and fails if any budget is exceeded.
 *
 * Two-tier JS budget (updated after adding Monaco lazy code editor):
 *   Initial chunks  — loaded on every first visit — ≤ INITIAL_TOTAL_KB total,
 *                     no single chunk > INITIAL_CHUNK_KB.
 *   Lazy chunks     — code-split, only loaded when a learner opens a code
 *                     question (Monaco Editor) — ≤ LAZY_CHUNK_KB each.
 *                     Lazy chunks do not affect first-load performance.
 *
 * Widget chunks (40.2) — one lazy chunk per `interactive` widget registered in
 *                     src/widgets/registry.ts — ≤ WIDGET_CHUNK_KB each
 *                     (docs/PLAN_UI_AVANZADA.md §46: «≤ 30 KB gz por widget»).
 *
 * "Initial" means: the chunk's filename appears in a <script type="module">
 * tag inside dist/index.html.  Everything else in dist/assets/*.js is lazy.
 *
 * Run after `npm run build`:  node scripts/check-bundle.mjs
 * CI: fails with exit code 1 if any budget is exceeded.
 */

import { readFileSync, readdirSync, statSync } from 'fs';
import { join, resolve } from 'path';
import { gzipSync } from 'zlib';

const DIST       = resolve(process.cwd(), 'dist');
const ASSETS_DIR = join(DIST, 'assets');

// ── Budgets ──────────────────────────────────────────────────────────────────
// Initial chunks: what every visitor downloads on first load.
const INITIAL_CHUNK_KB  = 300;   // no single initial chunk > 300 KB gzip
const INITIAL_TOTAL_KB  = 350;   // total initial JS gzip ≤ 350 KB

// Lazy chunks: code-split, loaded on demand (Monaco is ~1,037 KB gzip).
// No total limit — only a per-chunk cap to catch accidental over-bundling.
const LAZY_CHUNK_KB     = 1200;  // no single lazy chunk > 1,200 KB gzip

// Widgets de `interactive` (40.2): solo React + SVG/HTML, sin motor gráfico.
const WIDGET_CHUNK_KB   = 30;    // no widget chunk > 30 KB gzip
// ─────────────────────────────────────────────────────────────────────────────

function gzipKB(filePath) {
  return gzipSync(readFileSync(filePath)).length / 1024;
}

// Derive the set of initial JS filenames from dist/index.html.
function initialChunkNames() {
  const names = new Set();
  try {
    const html = readFileSync(join(DIST, 'index.html'), 'utf-8');
    for (const m of html.matchAll(/<script[^>]+src="[^"]*\/assets\/([^"]+)"[^>]*>/g)) {
      names.add(m[1]);
    }
  } catch {
    // index.html not present — treat all chunks as lazy (conservative).
  }
  return names;
}

// Widget chunks: Vite names a lazy chunk after its entry module, so the file
// names registered in registry.ts (`import('./cidr/Cidr')` → `Cidr-<hash>.js`)
// identify them. A registry without entries is a broken check, not a pass.
function widgetChunkNames() {
  const src = readFileSync(resolve(process.cwd(), 'src/widgets/registry.ts'), 'utf-8');
  return [...src.matchAll(/^\s*\w+\s*:\s*\(\)\s*=>\s*import\('\.\/[^']*?([^/']+)'\)/gm)].map((m) => m[1]);
}
const widgetNames = widgetChunkNames();
if (widgetNames.length === 0) {
  console.error('[perf-budget] no widget found in src/widgets/registry.ts — the widget budget would check nothing');
  process.exit(1);
}
const widgetOf = (f) => widgetNames.find((n) => f.startsWith(`${n}-`));

let files;
try {
  files = readdirSync(ASSETS_DIR);
} catch {
  console.error(`[perf-budget] dist/assets not found — run "npm run build" first`);
  process.exit(1);
}

const initial = initialChunkNames();

let failed        = false;
let initialJsGz   = 0;

const rows = { initial: [], widget: [], lazy: [], css: [] };

for (const f of files.sort()) {
  const ext = f.split('.').pop();
  if (!['js', 'css'].includes(ext)) continue;
  const full = join(ASSETS_DIR, f);
  if (!statSync(full).isFile()) continue;

  const kb = gzipKB(full);

  if (ext === 'css') {
    rows.css.push({ f, kb });
    continue;
  }

  if (initial.has(f)) {
    rows.initial.push({ f, kb });
    initialJsGz += kb;
  } else if (widgetOf(f)) {
    rows.widget.push({ f, kb });
  } else {
    rows.lazy.push({ f, kb });
  }
}

// ── Report ───────────────────────────────────────────────────────────────────
console.log('\n[perf-budget] Bundle size report\n');

function printSection(label, items) {
  if (items.length === 0) return;
  console.log(`  ${label}`);
  console.log(`  ${'File'.padEnd(45)} ${'gzip KB'.padStart(9)}`);
  console.log(`  ${'-'.repeat(45)} ${'-'.repeat(9)}`);
  for (const { f, kb, flag } of items) {
    console.log(`  ${f.padEnd(45)} ${kb.toFixed(1).padStart(8)} KB${flag ?? ''}`);
  }
  console.log();
}

// Initial JS
const initialRows = rows.initial.map(({ f, kb }) => {
  const over = kb > INITIAL_CHUNK_KB;
  if (over) failed = true;
  return { f, kb, flag: over ? '  ← OVER BUDGET' : '' };
});
printSection('Initial JS (loaded on first visit):', initialRows);

const initFlag = initialJsGz > INITIAL_TOTAL_KB ? '  ← OVER BUDGET' : '';
if (initialJsGz > INITIAL_TOTAL_KB) failed = true;
console.log(
  `  ${'  TOTAL initial JS (gzip)'.padEnd(45)} ${initialJsGz.toFixed(1).padStart(8)} KB${initFlag}\n`,
);

// Lazy JS
const lazyRows = rows.lazy.map(({ f, kb }) => {
  const over = kb > LAZY_CHUNK_KB;
  if (over) failed = true;
  return { f, kb, flag: over ? '  ← OVER BUDGET' : '' };
});
printSection('Lazy JS (code-split, loaded on demand):', lazyRows);

// Widgets (40.2): every registered widget must have produced its own chunk.
const missing = widgetNames.filter((n) => !rows.widget.some(({ f }) => f.startsWith(`${n}-`)));
if (missing.length) {
  failed = true;
  console.error(`  ← widget chunk not found in dist/assets: ${missing.join(', ')}`);
}
const widgetRows = rows.widget.map(({ f, kb }) => {
  const over = kb > WIDGET_CHUNK_KB;
  if (over) failed = true;
  return { f, kb, flag: over ? '  ← OVER BUDGET' : '' };
});
printSection('Widget JS (one lazy chunk per interactive widget):', widgetRows);

// CSS
printSection('CSS:', rows.css);

// Summary
console.log('  Budgets:');
console.log(`    initial chunk   ≤ ${INITIAL_CHUNK_KB} KB gzip  (first-load perf)`);
console.log(`    initial total   ≤ ${INITIAL_TOTAL_KB} KB gzip  (first-load perf)`);
console.log(`    widget chunk    ≤ ${WIDGET_CHUNK_KB} KB gzip  (interactive widgets, 40.2)`);
console.log(`    lazy chunk      ≤ ${LAZY_CHUNK_KB} KB gzip  (Monaco: ~1,037 KB gzip expected)`);

if (failed) {
  console.error('\n[perf-budget] FAIL — one or more budgets exceeded');
  process.exit(1);
} else {
  console.log('\n[perf-budget] PASS — all budgets within limit\n');
}
