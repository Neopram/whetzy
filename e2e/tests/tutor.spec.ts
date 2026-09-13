import { readFileSync } from 'fs';
import path from 'path';
import { test, expect, type Page, type Route } from '@playwright/test';

/**
 * TASK 11.2 — Tutor VISIBLE ("¿Por qué? / Why?" inline button under quiz feedback).
 *
 * This suite runs fully against MOCKED network routes: auth, dashboard,
 * missions, quiz start/answer and /tutor/explain are all intercepted with
 * `page.route`, so it needs only the Vite dev server (no backend, no
 * Postgres). That mirrors how the real backend behaves per
 * backend/app/api/v1/endpoints/tutor.py (POST /tutor/explain, gated behind
 * `require_tier("plus")`, response = { explanation, provider, grounded,
 * times_missed }) and backend/app/core/entitlements.py (free users get a 403).
 *
 * Auth is bypassed by seeding localStorage tokens before the app boots
 * (App.tsx reads `isAuthenticated()` synchronously on mount) instead of
 * driving the login form — the login flow itself is already covered by
 * e2e/tests/auth.spec.ts.
 *
 * axe-core: @axe-core/playwright is a frontend/ devDependency but this
 * package (e2e/) has its own, separate package.json/node_modules and does
 * not declare it, so the wrapper package isn't resolvable from here. The
 * underlying axe-core ENGINE (frontend/node_modules/axe-core/axe.min.js,
 * v4.13.0 — the same engine @axe-core/playwright wraps) is loaded straight
 * into the page instead, with no network access required.
 */

const AXE_SOURCE = readFileSync(
  path.join(__dirname, '../../frontend/node_modules/axe-core/axe.min.js'),
  'utf-8'
);

type AxeViolation = { id: string; impact?: string | null; description: string; nodes: { html: string }[] };

function formatViolations(violations: AxeViolation[]): string {
  if (!violations.length) return '';
  return violations
    .map((v) => `[${v.impact ?? 'unknown'}] ${v.id}: ${v.description}\n  ${v.nodes.map((n) => n.html).join('\n  ')}`)
    .join('\n\n');
}

async function expectNoAxeViolations(page: Page, scopeSelector?: string) {
  await page.addScriptTag({ content: AXE_SOURCE });
  const violations = await page.evaluate<AxeViolation[], string | undefined>(async (selector) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const axe = (window as any).axe;
    const context = selector ?? document;
    const results = await axe.run(context, {
      runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'] },
    });
    return results.violations;
  }, scopeSelector);
  expect(violations, formatViolations(violations)).toHaveLength(0);
}

const USER_ID = 'e2e-tutor-user';

const QUESTION = {
  id: 'q-tutor-mcq-1',
  skill_id: 'skill-python-basics',
  type: 'mcq' as const,
  difficulty_tier: 'easy' as const,
  question_es: '¿Cuál es la salida de `print(2 + 2)`?',
  question_en: 'What is the output of `print(2 + 2)`?',
  options_es: ['3', '4', '5', 'Error'],
  options_en: ['3', '4', '5', 'Error'],
  correct_answer_es: null,
  correct_answer_en: null,
  expected_time_ms: 8000,
};

function authMeResponse(isPremium: boolean, language: 'es' | 'en' = 'es') {
  return {
    id: USER_ID,
    email: 'tutor-e2e@example.com',
    username: 'tutore2e',
    display_name: 'Tutor E2E',
    language,
    avatar_emoji: '🧠',
    level: 3,
    total_xp: 500,
    current_streak: 2,
    max_streak: 5,
    streak_freeze_available: 0,
    last_active: null,
    created_at: new Date().toISOString(),
    is_premium: isPremium,
  };
}

const QUIZ_START_RESPONSE = {
  session_id: 'sess-tutor-1',
  mode: 'study',
  question: QUESTION,
  reviews_due: 0,
};

const QUIZ_ANSWER_RESPONSE = {
  correct: true,
  correct_index: 1,
  explanation_es: 'Porque 2 + 2 = 4 según la aritmética estándar de enteros.',
  explanation_en: 'Because 2 + 2 = 4 under standard integer arithmetic.',
  source: 'Fundamentos de Python — Módulo 1',
  grade: 1,
  xp_earned: 10,
  combo: 1,
  user_elo: 1000,
  next_review: null,
  skill_mastery: {},
  session_accuracy: 1,
  next_question: null,
};

interface TutorMockOptions {
  isPremium: boolean;
  grounded?: boolean;
  explanation?: string;
  language?: 'es' | 'en';
}

/** Wires every /api/v1/** call the app makes during the auth → home → quiz → answer
 *  flow to a fixed mock, plus /tutor/explain per `opts`. Returns a counter object
 *  so tests can assert whether /tutor/explain was ever actually called. */
async function mockBackend(page: Page, opts: TutorMockOptions) {
  const calls = { tutorExplain: 0 };

  await page.addInitScript(
    ([userId]) => {
      localStorage.setItem('whetzy_access_token', 'e2e-fake-access-token');
      localStorage.setItem('whetzy_refresh_token', 'e2e-fake-refresh-token');
      // Skip the OnboardingScreen — App.tsx gates it on this per-user flag.
      localStorage.setItem(`whetzy_onboarded_${userId}`, '1');
    },
    [USER_ID]
  );

  await page.route('**/api/v1/**', async (route: Route) => {
    const req = route.request();
    const url = new URL(req.url());
    const p = url.pathname;
    const method = req.method();

    if (p.endsWith('/auth/me') && method === 'GET') {
      return route.fulfill({ json: authMeResponse(opts.isPremium, opts.language) });
    }
    if (p.endsWith('/progress/dashboard')) {
      return route.fulfill({ json: { tracks: [], reviews_due: 0, current_streak: 0, max_streak: 0 } });
    }
    if (p.endsWith('/missions')) {
      return route.fulfill({ json: [] });
    }
    if (p.endsWith('/badges')) {
      return route.fulfill({ json: [] });
    }
    if (p.endsWith('/quiz/start') && method === 'POST') {
      return route.fulfill({ json: QUIZ_START_RESPONSE });
    }
    if (p.endsWith('/quiz/answer') && method === 'POST') {
      return route.fulfill({ json: QUIZ_ANSWER_RESPONSE });
    }
    if (p.endsWith('/tutor/explain') && method === 'POST') {
      calls.tutorExplain += 1;
      if (!opts.isPremium) {
        // Mirrors backend/app/core/entitlements.py require_tier("plus") — a free
        // account should never even reach here given the client-side gate, but
        // if it did, the server would answer with a 403 like this.
        return route.fulfill({
          status: 403,
          json: { detail: 'This feature requires a Plus subscription.' },
        });
      }
      return route.fulfill({
        json: {
          explanation:
            opts.explanation ??
            'El operador + suma los dos enteros, tal como se explica en el módulo de aritmética.',
          provider: 'groq',
          grounded: opts.grounded ?? true,
          times_missed: 0,
        },
      });
    }

    return route.fulfill({ json: {} });
  });

  return calls;
}

/** Navigates from a fresh load through Home → start quiz → answer the MCQ,
 *  landing on the feedback panel where the WhyButton lives. Works in either
 *  language: the mocked user's `language` field drives which HomeScreen CTA
 *  text renders ("ESTUDIAR AHORA" vs "STUDY NOW"). */
async function goToAnsweredQuestion(page: Page, whyButtonName: RegExp = /¿Por qué\?/i) {
  // Also doubles as a check that the panel respects prefers-reduced-motion
  // (red line 6): with it forced on, the global CSS rule in styles/global.css
  // collapses every animation/transition to ~0, so axe never captures the
  // WhyButton panel mid fade-in with a transient low-opacity/low-contrast frame.
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  const studyBtn = page.getByRole('button', { name: /^(ESTUDIAR AHORA|STUDY NOW)$/i });
  await expect(studyBtn).toBeVisible({ timeout: 15_000 });
  await studyBtn.click();

  const options = page.getByRole('button').filter({ hasText: /^[A-D]/ });
  await expect(options.first()).toBeVisible({ timeout: 15_000 });
  await options.nth(1).click(); // "B" == "4", the mocked correct answer

  await expect(page.getByRole('button', { name: whyButtonName })).toBeVisible({ timeout: 15_000 });
}

test.describe('Tutor visible — "¿Por qué? / Why?" (GAP-5)', () => {
  test('free user: sees the button and an honest upsell, tutor API is never called, closes in one tap', async ({ page }) => {
    const calls = await mockBackend(page, { isPremium: false });
    await goToAnsweredQuestion(page);

    const whyBtn = page.getByRole('button', { name: /¿Por qué\?/i });
    await expect(whyBtn).toHaveAttribute('aria-expanded', 'false');
    await whyBtn.click();
    await expect(whyBtn).toHaveAttribute('aria-expanded', 'true');

    // Honest upsell — plainly says this is a Plus feature, no fake spinner
    // pretending the free user is about to get a real answer.
    await expect(page.getByText(/Explicaciones del tutor AI/i)).toBeVisible();
    await expect(page.getByText(/Whetzy Plus/i).first()).toBeVisible();
    expect(calls.tutorExplain).toBe(0);

    await expectNoAxeViolations(page, '[data-testid="why-button"]');

    // Closes in one tap (red line 7). Scoped to the WhyButton panel — the
    // QuizScreen header's own close ("X" out of the quiz) button shares the
    // same "Cerrar" label.
    await page.getByTestId('why-button').getByRole('button', { name: /^Cerrar$/i }).click();
    await expect(whyBtn).toHaveAttribute('aria-expanded', 'false');
    await expect(page.getByText(/Explicaciones del tutor AI/i)).toHaveCount(0);
  });

  test('plus user: gets a grounded explanation in under 3s with a source badge, axe clean', async ({ page }) => {
    await mockBackend(page, { isPremium: true, grounded: true });
    await goToAnsweredQuestion(page);

    const whyBtn = page.getByRole('button', { name: /¿Por qué\?/i });
    const start = Date.now();
    await whyBtn.click();

    await expect(page.getByText(/El operador \+ suma los dos enteros/i)).toBeVisible({ timeout: 3_000 });
    const elapsedMs = Date.now() - start;
    expect(elapsedMs).toBeLessThan(3_000);

    // Grounded === true → the UI must show the "sourced" badge, never a bare
    // unlabeled answer (red line 2).
    await expect(page.getByText(/Basado en el contenido del curso/i)).toBeVisible();

    await expectNoAxeViolations(page, '[data-testid="why-button"]');
  });

  test('plus user: a non-grounded explanation is labeled honestly, never presented as cited', async ({ page }) => {
    await mockBackend(page, {
      isPremium: true,
      grounded: false,
      explanation: 'Respuesta genérica basada en conocimiento general del modelo.',
    });
    await goToAnsweredQuestion(page);

    await page.getByRole('button', { name: /¿Por qué\?/i }).click();

    await expect(page.getByText(/Respuesta genérica basada en conocimiento general/i)).toBeVisible({ timeout: 3_000 });
    await expect(page.getByText(/no verificado contra el curso/i)).toBeVisible();
    await expect(page.getByText(/Basado en el contenido del curso/i)).toHaveCount(0);
  });

  test('bilingual: English UI shows "Why?" and the matching upsell copy end-to-end', async ({ page }) => {
    // App.tsx re-runs i18n.changeLanguage() from the hydrated user's `language`
    // field (see stores/useAppStore.ts hydrateFromApi/mapApiUser), so driving
    // language through the mocked /auth/me response exercises the real path —
    // no test-only override needed.
    await mockBackend(page, { isPremium: false, language: 'en' });
    await goToAnsweredQuestion(page, /^Why\?$/i);

    const whyBtn = page.getByRole('button', { name: /^Why\?$/i });
    await whyBtn.click();

    await expect(page.getByText(/AI tutor explanations/i)).toBeVisible();
    await expect(page.getByText(/Whetzy Plus/i).first()).toBeVisible();

    await expectNoAxeViolations(page, '[data-testid="why-button"]');
  });
});
