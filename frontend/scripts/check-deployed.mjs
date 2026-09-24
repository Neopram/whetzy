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
 *   node scripts/check-deployed.mjs                      # https://whetzy.com
 *   node scripts/check-deployed.mjs https://whetzy.pages.dev
 *
 * Exits non-zero if any check fails, so it can gate a deploy.
 */
const BASE = (process.argv[2] ?? 'https://whetzy.com').replace(/\/$/, '');

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
