#!/usr/bin/env node
/**
 * Reproducible Lighthouse run for the landing page (tasks 11.11 / 11.6).
 *
 * Why this exists: the "LCP 3.5 s on mobile" figure that drove decision #10 in
 * docs/AUTONOMOUS_STATE.md came from an ad-hoc Lighthouse run that was never
 * committed, so nobody could repeat it — and a later session, measuring with a
 * hand-rolled CDP throttle, got ~1.6 s and wrongly concluded the original
 * number was an artefact of Lighthouse's *simulated* throttling. It was not.
 * Running Lighthouse both ways gives ~3.1 s and ~3.2 s: the real difference was
 * that the hand-rolled profile used a 150 ms latency, where Lighthouse's mobile
 * preset applies a 562.5 ms per-request latency (a ~3.75x inflation of the
 * nominal 150 ms RTT).
 *
 * Pinned to an exact Lighthouse version and run through npx, so it stays
 * reproducible without adding ~50 MB of devDependency to every CI install.
 *
 * Usage:
 *   npm run lighthouse:landing                      # against production
 *   npm run lighthouse:landing -- http://localhost:4188/landing
 *
 * Needs a Chrome; set CHROME_PATH if it is not on the default install path.
 */
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const LIGHTHOUSE_VERSION = '13.4.1';
const DEFAULT_URL = 'https://whetzy.com/landing';
const LCP_BUDGET_MS = 2500;

const url = process.argv[2] ?? DEFAULT_URL;
const workDir = mkdtempSync(join(tmpdir(), 'whetzy-lh-'));

/** One Lighthouse run; `method` is 'simulate' (Lantern) or 'devtools' (applied). */
function run(method) {
  const outPath = join(workDir, `lh-${method}.json`);
  // shell: true because on Windows `npx` is a .cmd shim, which execFile cannot
  // spawn directly. Every interpolated value is a literal from this file or the
  // URL argument, so it is quoted rather than passed raw.
  execFileSync(
    'npx',
    [
      '--yes',
      `lighthouse@${LIGHTHOUSE_VERSION}`,
      JSON.stringify(url),
      '--only-categories=performance',
      '--form-factor=mobile',
      '--screenEmulation.mobile',
      `--throttling-method=${method}`,
      '--output=json',
      `--output-path=${JSON.stringify(outPath)}`,
      '--chrome-flags="--headless=new --no-sandbox"',
      '--quiet',
    ],
    { stdio: ['ignore', 'ignore', 'inherit'], shell: true },
  );

  const report = JSON.parse(readFileSync(outPath, 'utf-8'));
  const audit = (id) => report.audits[id].numericValue;
  return {
    method,
    performance: Math.round(report.categories.performance.score * 100),
    lcp: Math.round(audit('largest-contentful-paint')),
    fcp: Math.round(audit('first-contentful-paint')),
    tbt: Math.round(audit('total-blocking-time')),
    throttling: report.configSettings.throttling,
  };
}

try {
  console.log(`Lighthouse ${LIGHTHOUSE_VERSION} · mobile · ${url}\n`);

  const results = [run('simulate'), run('devtools')];
  for (const r of results) {
    console.log(
      `${r.method.padEnd(9)} perf=${String(r.performance).padStart(3)}  ` +
        `LCP=${String(r.lcp).padStart(5)} ms  FCP=${String(r.fcp).padStart(5)} ms  ` +
        `TBT=${String(r.tbt).padStart(4)} ms`,
    );
  }

  const { rttMs, requestLatencyMs, downloadThroughputKbps, cpuSlowdownMultiplier } =
    results[0].throttling;
  console.log(
    `\nthrottling: rtt=${rttMs} ms · requestLatency=${requestLatencyMs} ms · ` +
      `down=${downloadThroughputKbps.toFixed(0)} kbps · cpu=${cpuSlowdownMultiplier}x`,
  );

  const worstLcp = Math.max(...results.map((r) => r.lcp));
  const verdict = worstLcp < LCP_BUDGET_MS ? 'PASS' : 'FAIL';
  console.log(`\nLCP budget ${LCP_BUDGET_MS} ms → ${verdict} (worst of the two: ${worstLcp} ms)`);

  // Reporting only: this is a measurement tool, not a CI gate. Exiting non-zero
  // would make it look like the script broke rather than that the page is slow.
  process.exitCode = 0;
} finally {
  rmSync(workDir, { recursive: true, force: true });
}
