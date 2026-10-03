#!/usr/bin/env node
/**
 * Deploy verification against a live URL (task 12.12).
 *
 * "Is what we built actually what is being served?" has been answered by hand,
 * in prose, in this repo's ledger, more than once — and got it wrong more than
 * once. It is the question behind task 12.2 / H.11, and it is not hard to
 * answer; it was just never automated, so each session re-derived it with ad-hoc
 * curls and a paragraph of interpretation.
 *
 * This asks every part of it in one command and prints a verdict per check, so
 * "the deploy is stale" stops being an opinion. Each check says what it means
 * for a user, not just which string was missing — a failing line should tell
 * whoever runs it what is broken for real people.
 *
 * Usage:
 *   node scripts/check-deployed.mjs                      # https://whetzy.com vs origin/master
 *   node scripts/check-deployed.mjs https://whetzy.pages.dev
 *   node scripts/check-deployed.mjs --sha <commit>       # any git ref or a full SHA
 *   node scripts/check-deployed.mjs https://<branch>.whetzy.pages.dev --sha HEAD
 *
 * Exits non-zero if any check fails, so it can gate a deploy.
 */
import { spawnSync } from 'node:child_process';

const argv = process.argv.slice(2);
const shaFlag = argv.indexOf('--sha');
const shaArg = shaFlag >= 0 ? argv[shaFlag + 1] : undefined;
if (shaFlag >= 0 && !shaArg) {
  console.error('[deployed] --sha needs a value (a commit, a branch or a full SHA)');
  process.exit(2);
}
const positional = argv.filter((_, i) => shaFlag < 0 || (i !== shaFlag && i !== shaFlag + 1));
const BASE = (positional[0] ?? 'https://whetzy.com').replace(/\/$/, '');

/** The commit the deploy is supposed to be. A full 40-hex SHA is taken as is
 *  (no repo needed); anything else is resolved with git. With no --sha it is
 *  origin/master as this clone last fetched it, because master is what
 *  production publishes — `git fetch` first or it compares against a stale one. */
function expectedSha() {
  const ref = shaArg ?? 'origin/master';
  if (/^[0-9a-f]{40}$/i.test(ref)) return { sha: ref.toLowerCase(), ref };
  const r = spawnSync('git', ['rev-parse', '--verify', `${ref}^{commit}`], { encoding: 'utf-8' });
  if (r.status !== 0) return { sha: null, ref, error: (r.stderr || '').trim() || `git rev-parse ${ref} failed` };
  return { sha: r.stdout.trim().toLowerCase(), ref };
}
const EXPECTED = expectedSha();

const BANNED_HOSTS = ['fonts.googleapis.com', 'fonts.gstatic.com', 'cdn.jsdelivr.net'];

async function get(path) {
  const res = await fetch(`${BASE}${path}`, { redirect: 'follow' });
  return { status: res.status, type: res.headers.get('content-type') ?? '', body: await res.text() };
}

/**
 * Each check returns { ok, detail }. `impact` explains the user-visible
 * consequence of a failure; it is printed only when the check fails, where it
 * is the part that actually helps.
 */
const CHECKS = [
  {
    // The checks below look for traits of the current build (canonical, hero,
    // API URL). An older deploy that already had those traits passes them all,
    // which is how a stale frontend could read as current. The commit SHA that
    // vite.config.ts embeds is the direct answer.
    name: 'the served build is the expected commit',
    impact: 'production is serving a different commit than the one you are checking — the deploy has not happened yet, failed, or published something else',
    async run() {
      if (!EXPECTED.sha) return { ok: false, detail: `cannot resolve the expected commit ${JSON.stringify(EXPECTED.ref)}: ${EXPECTED.error}` };
      const { body } = await get('/');
      const served = body.match(/<meta name="whetzy-build" content="([^"]*)"/)?.[1] ?? null;
      if (!served) return { ok: false, detail: `no <meta name="whetzy-build"> in the served HTML (expected ${EXPECTED.sha.slice(0, 12)} from ${EXPECTED.ref})` };
      const ok = served.toLowerCase() === EXPECTED.sha;
      return { ok, detail: `served ${served.slice(0, 18)} · expected ${EXPECTED.sha.slice(0, 12)} (${EXPECTED.ref})` };
    },
  },
  {
    name: 'index.html is the current build',
    impact: 'the deployed HTML predates the SEO work (11.7) — no canonical, so the site is not indexable as intended',
    async run() {
      const { body } = await get('/');
      return { ok: body.includes('canonical'), detail: body.includes('canonical') ? 'canonical present' : 'no <link rel="canonical"> in the served HTML' };
    },
  },
  {
    name: 'landing ships the prerendered hero',
    impact: 'the landing paints only after the JS bundle boots — the LCP budget (red line 8) is measured on a page real visitors never get this fast',
    async run() {
      const { body } = await get('/landing');
      const ok = body.includes('data-lcp="hero"');
      return { ok, detail: ok ? 'data-lcp="hero" in the HTML response' : 'served the SPA shell, not dist/landing/index.html (11.11 / 12.10)' };
    },
  },
  {
    // 2026-09-24: the bundle shipped with 'https://whetzy.com' as its API, so
    // login POSTed to Cloudflare and got a 405, shown as "Incorrect email or
    // password". Every other check here passed.
    name: 'the bundle talks to a live API',
    impact: 'login, register and every API call fail — the app renders but nobody can sign in',
    async run() {
      const { body } = await get('/');
      const scripts = [...body.matchAll(/(?:src|href)="(\/assets\/[^"]+\.js)"/g)].map((m) => m[1]);
      let api = null;
      for (const src of scripts) {
        api = (await get(src)).body.match(/https?:\/\/[a-z0-9.-]+(?::\d+)?\/api\/v1/)?.[0] ?? null;
        if (api) break;
      }
      if (!api) return { ok: false, detail: `no absolute .../api/v1 URL in ${scripts.length} entry script(s) — VITE_API_URL was wrong at build time` };
      if (new URL(api).host === new URL(BASE).host) return { ok: false, detail: `${api} is the frontend itself` };
      const origin = new URL(api).origin;
      const res = await fetch(`${origin}/health`);
      const text = await res.text();
      const ok = res.status === 200 && text.includes('healthy');
      return { ok, detail: `${api} → GET ${origin}/health ${res.status} ${text.slice(0, 60)}` };
    },
  },
  {
    name: '/api/* on the frontend domain is a 404',
    impact: 'a Pages Function answers API calls on the frontend domain — on 2026-09-24 one replied 200 "Autenticado correctamente" to any POST',
    async run() {
      const res = await fetch(`${BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: '{}',
      });
      const text = await res.text();
      return { ok: res.status === 404, detail: `POST /api/v1/auth/login → ${res.status} ${text.slice(0, 60)}` };
    },
  },
  {
    name: 'sitemap.xml is a real file',
    impact: 'search engines get an HTML page where they expect XML, so nothing is submitted for indexing',
    async run() {
      const { status, type } = await get('/sitemap.xml');
      const ok = status === 200 && type.includes('xml');
      return { ok, detail: `${status} ${type || '(no content-type)'}` };
    },
  },
  {
    name: 'robots.txt is a real file',
    impact: 'crawlers get HTML instead of directives and fall back to guessing',
    async run() {
      const { status, type } = await get('/robots.txt');
      const ok = status === 200 && type.includes('text/plain');
      return { ok, detail: `${status} ${type || '(no content-type)'}` };
    },
  },
  {
    name: 'Pyodide is served from our own origin',
    impact: 'exec questions fall back to a third-party CDN — red line 5, and they cannot work offline (red line 4)',
    async run() {
      const { status, type } = await get('/pyodide/pyodide.js');
      const ok = status === 200 && type.includes('javascript');
      return { ok, detail: `${status} ${type || '(no content-type)'} — expected the 12.9 self-hosted runtime` };
    },
  },
  {
    name: 'no third-party origin in the served HTML or CSS',
    impact: 'visitor IPs reach a third party before any consent — red line 5, and GDPR exposure in the EU',
    async run() {
      const { body } = await get('/');
      const texts = [body];
      // Follow the stylesheets the page actually links, since that is where the
      // Google font import hid for months (task 12.7).
      for (const m of body.matchAll(/<link[^>]+href="([^"]+\.css)"/g)) {
        const href = m[1].startsWith('http') ? m[1] : `${m[1].startsWith('/') ? '' : '/'}${m[1]}`;
        try {
          texts.push((await get(href)).body);
        } catch {
          /* a stylesheet we cannot fetch is not evidence of a violation */
        }
      }
      const hits = BANNED_HOSTS.filter((h) => texts.some((t) => t.includes(h)));
      return { ok: hits.length === 0, detail: hits.length ? `found: ${hits.join(', ')}` : `checked HTML + ${texts.length - 1} stylesheet(s)` };
    },
  },
];

console.log(`\n[deployed] ${BASE}\n`);

let failed = 0;
for (const check of CHECKS) {
  let result;
  try {
    result = await check.run();
  } catch (err) {
    result = { ok: false, detail: `check could not run: ${err.message}` };
  }
  console.log(`  ${result.ok ? 'PASS' : 'FAIL'}  ${check.name}\n        ${result.detail}`);
  if (!result.ok) {
    failed += 1;
    console.log(`        impact: ${check.impact}`);
  }
}

console.log(
  failed === 0
    ? `\n[deployed] PASS — ${BASE} is serving the current build\n`
    : `\n[deployed] FAIL — ${failed}/${CHECKS.length} checks failed. ${BASE} is not serving the current build (task 12.2 / H.11).\n`,
);
process.exit(failed === 0 ? 0 : 1);
