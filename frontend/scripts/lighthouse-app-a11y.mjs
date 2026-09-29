#!/usr/bin/env node
/**
 * Reproducible Lighthouse accessibility run for the post-login learning
 * screens (task 34.5): Home, Tracks, Lesson, Quiz.
 *
 * Why this exists: 34.5's own criterion asked for "Lighthouse a11y ≥95",
 * but the app is a single-page, state-driven SPA with no per-screen
 * routing (Home/Tracks/Lesson/Quiz are React component state, not URLs —
 * see `App.tsx`'s `screen` state and `IMMERSIVE_SCREENS`). A plain
 * `lighthouse <url>` CLI run can only ever navigate to whatever the app
 * shows by default; it cannot click through to Tracks or a Lesson. The
 * only supported way to get a real Lighthouse *score* (not just an
 * axe-core violation count, which `e2e/accessibility.spec.ts` already
 * covers) for a screen reached by clicking is Lighthouse's user-flow API
 * (`startFlow` + `.snapshot()`), driven by Puppeteer against the exact
 * same authenticated page — not a fresh navigation per screen.
 *
 * `e2e/accessibility.spec.ts` already proves 0 axe-core WCAG 2.2 AA
 * violations on these screens with Playwright. This script answers a
 * narrower, literal question the ledger asked for: what number does the
 * Lighthouse tool itself report, weighted the way Lighthouse weights it.
 * They can legitimately differ (Lighthouse's accessibility category is a
 * curated, weighted subset of axe rules, not every rule this project
 * enables), so this is not a duplicate check.
 *
 * `puppeteer-core` and `lighthouse` are not project dependencies (see
 * `lighthouse-landing.mjs` for the same reasoning — CI does not need them
 * on every install). Install them locally before running:
 *   npm install --no-save puppeteer-core@23 lighthouse@13.4.1
 *
 * Needs a running backend + frontend dev server (defaults match
 * `playwright.config.ts`'s webServer: backend on :8000, frontend on
 * :5199) and a real Chrome. Set CHROME_PATH if Playwright's bundled
 * Chromium is not at the default install path this script probes.
 *
 * Usage:
 *   node scripts/lighthouse-app-a11y.mjs
 *   node scripts/lighthouse-app-a11y.mjs http://localhost:5199 http://127.0.0.1:8000
 */
import { existsSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const FRONTEND_URL = process.argv[2] ?? 'http://localhost:5199';
const A11Y_BUDGET = 95;
// A plain 4-option MCQ in track01 — same fixture accessibility.spec.ts uses,
// so a quiz screen audit does not depend on which question the adaptive
// picker happens to serve, or on Pyodide booting for an exec question.
const FORCED_MCQ_ID = 'q010101001';

function findChrome() {
  if (process.env.CHROME_PATH && existsSync(process.env.CHROME_PATH)) return process.env.CHROME_PATH;
  const candidates = [
    '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome',
    '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  ];
  for (const c of candidates) if (existsSync(c)) return c;
  throw new Error(
    'No Chrome binary found. Set CHROME_PATH, e.g. to the output of:\n' +
      '  find /opt/pw-browsers -maxdepth 2 -name chrome',
  );
}

async function registerTestUser() {
  const suffix = Date.now().toString(36) + Math.floor(Math.random() * 1000);
  const username = `lh_a11y_${suffix}`;
  const res = await fetch(`${FRONTEND_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: `${username}@example.com`,
      username,
      display_name: 'Lighthouse A11y',
      password: 'e2e-test-pass-123',
      age_confirmed: true,
    }),
  });
  if (!res.ok) throw new Error(`register failed: HTTP ${res.status}: ${await res.text()}`);
  const setCookie = res.headers.getSetCookie?.() ?? [];
  if (setCookie.length === 0) throw new Error('register response carried no Set-Cookie header');
  const cookies = setCookie.map((c) => {
    const [pair] = c.split(';');
    const eq = pair.indexOf('=');
    return { name: pair.slice(0, eq), value: pair.slice(eq + 1) };
  });
  const body = await res.json();
  // The JWT's `sub` claim is the user id — decode it to build the
  // per-user onboarding-suppression localStorage key without a second
  // round trip to /auth/me.
  const payload = JSON.parse(Buffer.from(body.access_token.split('.')[1], 'base64url').toString('utf-8'));
  return { userId: payload.sub, cookies };
}

async function main() {
  const chromePath = findChrome();
  const { userId, cookies } = await registerTestUser();
  console.log(`Registered test user ${userId}`);

  // These are dynamic imports, not top-level, so the script gives its own
  // "install them first" error message instead of Node's raw
  // ERR_MODULE_NOT_FOUND when they are missing.
  let puppeteer, startFlow;
  try {
    ({ default: puppeteer } = await import('puppeteer-core'));
    ({ startFlow } = await import('lighthouse'));
  } catch {
    console.error(
      '\n[lighthouse-app-a11y] puppeteer-core / lighthouse not installed.\n' +
        '  Run: npm install --no-save puppeteer-core@23 lighthouse@13.4.1\n',
    );
    process.exitCode = 1;
    return;
  }

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox'],
  });

  try {
    const page = await browser.newPage();
    await page.setCookie(...cookies.map((c) => ({ ...c, url: FRONTEND_URL })));
    // Pre-empt the first-run onboarding gate (App.tsx's needsOnboarding):
    // a per-user localStorage flag, set before the app's first script runs
    // so it never shows onboarding for this fresh account. Real returning
    // users get here by having visited before; a scripted run has to set
    // it explicitly the same way suppressOnboarding() does in e2e/helpers.ts.
    await page.evaluateOnNewDocument((uid) => {
      localStorage.setItem(`whetzy_onboarded_${uid}`, '1');
    }, userId);

    // maxWaitForFcp/maxWaitForLoad raised somewhat above Lighthouse's
    // defaults (10s/45s) as a margin for a shared/loaded machine — this box
    // also runs the project's own background CI (scripts/ci_local.sh,
    // triggered by a git push) sharing the same 4 cores. (An earlier
    // version of this comment blamed a since-disproven NO_FCP entirely on
    // that contention; the real cause was flow.startNavigation()/
    // endNavigation() around the SPA's client-side screen changes below —
    // see the comment there. This margin is now just defensive headroom,
    // not a fix for anything.)
    const flow = await startFlow(page, {
      name: 'Whetzy learning screens — accessibility',
      config: {
        extends: 'lighthouse:default',
        settings: { maxWaitForFcp: 45_000, maxWaitForLoad: 90_000 },
      },
    });

    // -- Home ---------------------------------------------------------
    await flow.navigate(FRONTEND_URL);
    await page.waitForFunction(
      () => Array.from(document.querySelectorAll('button')).some((b) => b.textContent?.includes('ESTUDIAR AHORA')),
      { timeout: 15_000 },
    );
    await flow.snapshot({ name: 'Home' });

    // -- Tracks ---------------------------------------------------------
    // Not flow.startNavigation()/endNavigation(): that pair is for a real
    // browser navigation (Lighthouse waits for a fresh First Contentful
    // Paint trace event). Clicking "Rutas" is a client-side React state
    // change inside the same already-painted SPA document — no new FCP
    // event will ever fire, so startNavigation() here reliably hit NO_FCP.
    // flow.snapshot() audits the current DOM without expecting one.
    await clickButtonByText(page, 'Rutas');
    await page.waitForSelector('[class*="moduleHeader_"]', { timeout: 20_000 });
    await flow.snapshot({ name: 'Tracks' });

    // -- Lesson -----------------------------------------------------
    // Expand the first module, then follow its "Aprender" (learn) CTA —
    // the same path TracksScreen.tsx's `startLesson` button uses. Same
    // reasoning as Tracks above: a client-side state change, not a
    // navigation, so plain snapshot() rather than startNavigation().
    await page.click('[class*="moduleHeader_"]');
    await page.waitForSelector('[class*="learnBtn_"]', { timeout: 10_000 });
    await page.click('[class*="learnBtn_"]');
    await page.waitForSelector('h1', { timeout: 15_000 });
    await flow.snapshot({ name: 'Lesson' });

    // -- Quiz (answer-feedback panel) --------------------------------
    // Close the lesson, then force the same plain-MCQ fixture
    // accessibility.spec.ts uses so the audit is not at the mercy of
    // whichever question the adaptive picker serves.
    await page.setRequestInterception(true);
    page.on('request', (req) => {
      if (req.url().includes('/quiz/start') && req.method() === 'POST') {
        const original = JSON.parse(req.postData() || '{}');
        req.continue({ postData: JSON.stringify({ ...original, force_question_id: FORCED_MCQ_ID }) });
      } else {
        req.continue();
      }
    });
    const closeBtn = await page.$('[class*="btnClose_"]');
    if (closeBtn) await closeBtn.click();
    // Closing the lesson returns to wherever it was opened from (Tracks,
    // with the module still expanded), not necessarily Home — go there
    // explicitly rather than assume, since "ESTUDIAR AHORA" only lives there.
    await clickButtonByText(page, 'Inicio');
    await clickButtonByText(page, 'ESTUDIAR AHORA');
    await page.waitForSelector('[class*="questionCard_"]', { timeout: 20_000 });
    await page.click('[class*="options_"] button');
    await page.waitForSelector('[class*="explanation_"]', { timeout: 20_000 });
    await flow.snapshot({ name: 'Quiz (answer feedback)' });

    const summary = summarizeSteps(await flow.createFlowResult());

    const reportHtml = await flow.generateReport();
    const outDir = mkdtempSync(join(tmpdir(), 'whetzy-lh-a11y-'));
    const outPath = join(outDir, 'report.html');
    writeFileSync(outPath, reportHtml);

    console.log('\nAccessibility scores (Lighthouse, 0-100):');
    let worst = 100;
    for (const s of summary) {
      console.log(`  ${s.name.padEnd(24)} ${String(s.score).padStart(3)}`);
      if (s.score !== null) worst = Math.min(worst, s.score);
    }
    console.log(`\nFull report: ${outPath}`);
    const verdict = worst >= A11Y_BUDGET ? 'PASS' : 'FAIL';
    console.log(`\nBudget ${A11Y_BUDGET} → ${verdict} (worst screen: ${worst})`);
    process.exitCode = worst >= A11Y_BUDGET ? 0 : 1;
  } finally {
    await browser.close();
  }
}

async function clickButtonByText(page, text) {
  await page.waitForFunction(
    (t) => Array.from(document.querySelectorAll('button')).some((b) => b.textContent?.includes(t)),
    { timeout: 15_000 },
    text,
  );
  const handles = await page.$$('button');
  for (const h of handles) {
    const t = await page.evaluate((el) => el.textContent, h);
    if (t?.includes(text)) {
      await h.click();
      return;
    }
  }
  throw new Error(`No <button> with text ${JSON.stringify(text)} found`);
}

function summarizeSteps(flowResult) {
  return flowResult.steps.map((step) => {
    const cat = step.lhr?.categories?.accessibility;
    return { name: step.name, score: cat ? Math.round(cat.score * 100) : null };
  });
}

main().catch((err) => {
  console.error(`\n[lighthouse-app-a11y] ${err.stack ?? err.message}\n`);
  if (err.friendlyMessage) console.error('friendlyMessage:', err.friendlyMessage);
  if (err.cause) console.error('cause:', err.cause);
  process.exitCode = 1;
});
