#!/usr/bin/env node
/**
 * Bundle-size budget check (8.3).
 *
 * Reads the Vite dist/ output, gzip-compresses each JS/CSS asset in memory,
 * and fails if any single chunk exceeds CHUNK_LIMIT_KB or if the total JS
 * gzip size exceeds TOTAL_JS_LIMIT_KB.
 *
 * Run after `npm run build`:  node scripts/check-bundle.mjs
 * CI: fails with exit code 1 if any budget is exceeded.
 */

import { readFileSync, readdirSync, statSync } from 'fs';
import { join, resolve } from 'path';
import { gzipSync } from 'zlib';

const DIST = resolve(process.cwd(), 'dist', 'assets');

// Budgets
const CHUNK_LIMIT_KB = 300;    // no single chunk > 300 KB gzip
const TOTAL_JS_LIMIT_KB = 350; // total JS gzip < 350 KB

function gzipKB(filePath) {
  const raw = readFileSync(filePath);
  return gzipSync(raw).length / 1024;
}

let failed = false;
let totalJsGz = 0;

let files;
try {
  files = readdirSync(DIST);
} catch {
  console.error(`[perf-budget] dist/assets not found — run "npm run build" first`);
  process.exit(1);
}

console.log('\n[perf-budget] Bundle size report\n');
console.log(`  ${'File'.padEnd(40)} ${'gzip KB'.padStart(9)}`);
console.log(`  ${'-'.repeat(40)} ${'-'.repeat(9)}`);

for (const f of files.sort()) {
  const ext = f.split('.').pop();
  if (!['js', 'css'].includes(ext)) continue;
  const full = join(DIST, f);
  if (!statSync(full).isFile()) continue;

  const kb = gzipKB(full);
  const flag = kb > CHUNK_LIMIT_KB ? '  ← OVER BUDGET' : '';
  console.log(`  ${f.padEnd(40)} ${kb.toFixed(1).padStart(8)} KB${flag}`);

  if (ext === 'js') totalJsGz += kb;
  if (kb > CHUNK_LIMIT_KB) failed = true;
}

const totalFlag = totalJsGz > TOTAL_JS_LIMIT_KB ? '  ← OVER BUDGET' : '';
console.log(`\n  ${'TOTAL JS (gzip)'.padEnd(40)} ${totalJsGz.toFixed(1).padStart(8)} KB${totalFlag}`);
if (totalJsGz > TOTAL_JS_LIMIT_KB) failed = true;

console.log('\n  Budgets:');
console.log(`    single chunk  ≤ ${CHUNK_LIMIT_KB} KB gzip`);
console.log(`    total JS      ≤ ${TOTAL_JS_LIMIT_KB} KB gzip`);

if (failed) {
  console.error('\n[perf-budget] FAIL — one or more budgets exceeded');
  process.exit(1);
} else {
  console.log('\n[perf-budget] PASS — all budgets within limit\n');
}
