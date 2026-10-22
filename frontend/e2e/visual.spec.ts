import { test, expect, type Page, type Route } from '@playwright/test';

/**
 * 46.5 (docs/PLAN_UI_AVANZADA.md §7): regresión visual. 8 pantallas × 390/1280 ×
 * ES/EN × oscuro/claro = 64 capturas contra baselines en `e2e/__screenshots__/`.
 *
 * Sin backend: toda la API se simula aquí con `page.route`, con cifras fijas y el
 * reloj congelado, así que el resultado depende solo del CSS y del JSX. Se corre
 * con `playwright.visual.config.ts` (su propio servidor, :5197) desde el nivel 2
 * de `scripts/ci_local.sh`; nunca desde el hook de push.
 *
 * Las 8 pantallas son las que un alumno ve cada día más las dos puertas de
 * entrada, y juntas pisan casi todo el sistema de tokens: portada y acceso (la
 * primera impresión, con sus superficies propias), Hoy (tarjetas, banda de
 * marca, misiones), pregunta y resumen del quiz (la pieza central: opciones,
 * botones, recuento), Rutas (rejilla de tarjetas con color por ruta), Perfil
 * (formularios, interruptores, insignias) y Liga (lista y podio). Se capta el
 * viewport (no la página entera): el pliegue es donde un cambio de token se ve
 * y mantiene las imágenes pequeñas.
 */

const json = (route: Route, body: unknown, status = 200) =>
  route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });

const USER = {
  id: 'u-visual', email: 'ana@example.com', username: 'ana', display_name: 'Ana',
  language: 'es', avatar_emoji: '🦊', level: 3, total_xp: 1240, current_streak: 4, max_streak: 9,
  streak_freeze_available: 1, last_active: null, created_at: '2026-01-01T00:00:00Z',
  is_premium: false, email_verified: true, onboarding_completed_at: '2026-01-02T00:00:00Z',
  target_track_id: 'track01',
};

const TRACKS = [
  { id: 'track01', name_es: 'Python', name_en: 'Python', order: 1, icon: '🐍', color: '#3776AB', total_questions: 320, is_certification: false, cert_provider: null, exam_question_count: null, exam_duration_minutes: null },
  { id: 'track02', name_es: 'JavaScript', name_en: 'JavaScript', order: 2, icon: '⚡', color: '#B8A600', total_questions: 320, is_certification: false, cert_provider: null, exam_question_count: null, exam_duration_minutes: null },
  { id: 'track03', name_es: 'SQL', name_en: 'SQL', order: 3, icon: '🗄️', color: '#E48916', total_questions: 320, is_certification: false, cert_provider: null, exam_question_count: null, exam_duration_minutes: null },
  { id: 'track04', name_es: 'Git', name_en: 'Git', order: 4, icon: '🌿', color: '#3DD68C', total_questions: 320, is_certification: false, cert_provider: null, exam_question_count: null, exam_duration_minutes: null },
];

const MASTERY = TRACKS.map((t, i) => ({
  track_id: t.id, name_es: t.name_es, name_en: t.name_en, icon: t.icon, color: t.color,
  average_mastery: [0.42, 0.2, 0.05, 0][i], skills_mastered: [6, 2, 0, 0][i], total_skills: 32,
}));

const skill = (n: number, p: number, mastered = false) => ({
  skill_id: `sk0101${String(n).padStart(2, '0')}`, name_es: `Habilidad ${n}`, name_en: `Skill ${n}`, order: n,
  p_known: p, mastered, attempts: 10, correct_count: 8, lesson_seen: true, practice_unlocked: true,
});

const QUESTION = {
  id: 'q-visual', skill_id: 'sk010101', type: 'mcq', difficulty_tier: 'easy',
  question_es: '¿Qué imprime `print(2 + 3)`?', question_en: 'What does `print(2 + 3)` print?',
  options_es: ['5', '23', '2 + 3', 'Error'], options_en: ['5', '23', '2 + 3', 'Error'],
  correct_answer_es: null, correct_answer_en: null, expected_time_ms: 20000,
};

const LEAGUE = {
  league: { id: 'l2', name: 'Plata', tier: 'silver', min_xp: 0 }, week_start: '2026-10-19',
  standings: ['Lucía', 'Marco', 'Ana', 'Iván', 'Sofía', 'Hugo'].map((n, i) => ({
    rank: i + 1, user_id: n === 'Ana' ? 'u-visual' : `u${i}`, username: n.toLowerCase(), display_name: n,
    avatar_emoji: ['🦉', '🐼', '🦊', '🐯', '🐸', '🐙'][i], xp_earned: 900 - i * 120, is_current_user: n === 'Ana',
  })),
  promotion_zone: 3, demotion_zone: 5, total_members: 6, participating: true,
};

/** Toda la API que tocan estas pantallas; lo que no esté aquí devuelve 404. */
async function mockApi(page: Page, opts: { signedIn: boolean; lang: 'es' | 'en' }) {
  const user = { ...USER, language: opts.lang };
  await page.route('**/api/v1/**', (route) => {
    const { pathname: p } = new URL(route.request().url());
    const m = route.request().method();
    if (p.endsWith('/auth/me')) return opts.signedIn ? json(route, user) : json(route, { detail: 'Not authenticated' }, 401);
    if (p.endsWith('/auth/refresh')) return json(route, { detail: 'no' }, 401);
    if (p.endsWith('/auth/oauth/providers')) return json(route, { providers: [] });
    if (p.endsWith('/economy/streak-freeze')) return json(route, { price: 50, balance: 120, held: 1, max_held: 2, purchases_this_week: 0, max_per_week: 2, can_buy: true, blocked_by: null });
    if (p.endsWith('/progress/dashboard')) return json(route, { level: 3, total_xp: 1240, current_streak: 4, max_streak: 9, streak_freeze_available: 1, last_active: null, reviews_due: 3, tracks: MASTERY, total_sessions: 12, total_questions_answered: 140, overall_accuracy: 0.78 });
    if (p.endsWith('/missions')) return json(route, [
      { mission: { id: 'm1', type: 'questions_answered', target_value: 10, xp_reward: 20, name_es: 'Responde 10 preguntas', name_en: 'Answer 10 questions' }, progress: 10, completed: true, date: '2026-10-21' },
      { mission: { id: 'm2', type: 'questions_answered', target_value: 20, xp_reward: 30, name_es: 'Responde 20 preguntas', name_en: 'Answer 20 questions' }, progress: 12, completed: false, date: '2026-10-21' },
    ]);
    if (p.endsWith('/progress/decaying')) return json(route, []);
    if (p.endsWith('/progress/skills')) return json(route, [1, 2, 3].map((n) => ({
      skill_id: `sk0101${String(n).padStart(2, '0')}`, name_es: `Habilidad ${n}`, name_en: `Skill ${n}`, module_id: 'mod0101',
      p_known: [0.9, 0.5, 0.1][n - 1], elo_rating: 1200, attempts: 10, correct_count: 8, accuracy: 0.8, mastered: n === 1, fsrs_due: null,
    })));
    if (p.endsWith('/progress/curriculum')) return json(route, {
      track_id: 'track01', name_es: 'Python', name_en: 'Python', icon: '🐍', color: '#3776AB', mastery_threshold: 0.8,
      modules: [{
        id: 'mod0101', name_es: 'Fundamentos', name_en: 'Basics', order: 1, description_es: 'Variables y tipos', description_en: 'Variables and types',
        min_mastery_to_unlock: 0, level: 1, average_mastery: 0.5, status: 'available', prerequisite_id: null, prerequisite_met: true,
        skills: [skill(1, 0.9, true), skill(2, 0.5), skill(3, 0.1)],
      }],
    });
    if (p.endsWith('/content/tracks')) return json(route, TRACKS);
    if (p.endsWith('/league/current')) return json(route, LEAGUE);
    if (p.endsWith('/badges')) return json(route, []);
    if (p.endsWith('/auth/2fa/status')) return json(route, { enabled: false, backup_codes_left: 0 });
    if (p.endsWith('/billing/paddle/config')) return json(route, { enabled: false, environment: 'sandbox', client_token: null, prices: { plus: null, pro: null, certification: null, plus_annual: null, pro_annual: null } });
    if (p.endsWith('/quiz/start') && m === 'POST') return json(route, { session_id: 's1', mode: 'study', question: QUESTION, reviews_due: 0, selection_reason: null });
    if (p.endsWith('/quiz/answer') && m === 'POST') return json(route, {
      correct: true, correct_index: 0, explanation_es: 'La suma se evalúa antes de imprimir.', explanation_en: 'The sum is evaluated before printing.',
      source: null, grade: 4, xp_earned: 10, combo: 1, user_elo: 1200, next_review: null, skill_mastery: {}, session_accuracy: 1,
      next_question: null, next_selection_reason: null,
    });
    if (p.endsWith('/quiz/end') && m === 'POST') return json(route, { total_questions: 10, correct: 8, accuracy: 0.8, max_combo: 5, xp_earned: 80, duration_seconds: 240 });
    if (m === 'POST') return json(route, {});
    return json(route, { detail: 'not mocked' }, 404);
  });
}

const goto = (page: Page, screen: string) =>
  page.evaluate((s) => (window as unknown as { __whetzyStore: { getState: () => { setScreen: (x: string) => void } } }).__whetzyStore.getState().setScreen(s), screen);

type Pantalla = { id: string; signedIn: boolean; url: string; abre: (page: Page) => Promise<void>; listo: RegExp | string };

const PANTALLAS: Pantalla[] = [
  { id: 'landing', signedIn: false, url: '/landing', abre: async () => {}, listo: 'h1' },
  { id: 'auth', signedIn: false, url: '/auth', abre: async () => {}, listo: 'form' },
  { id: 'hoy', signedIn: true, url: '/', abre: async (p) => { await expect(p.getByTestId('home-next')).toBeVisible(); }, listo: '[data-testid="home-next"]' },
  {
    id: 'quiz-pregunta', signedIn: true, url: '/',
    abre: async (p) => {
      await p.evaluate(() => (window as unknown as { __whetzyStore: { getState: () => { startQuiz: (m: string, n: number) => void } } }).__whetzyStore.getState().startQuiz('study', 1));
    },
    listo: '[class*="questionCard_"]',
  },
  {
    id: 'quiz-resumen', signedIn: true, url: '/',
    abre: async (p) => {
      await p.evaluate(() => (window as unknown as { __whetzyStore: { getState: () => { startQuiz: (m: string, n: number) => void } } }).__whetzyStore.getState().startQuiz('study', 1));
      await p.locator('[class*="options_"] button').first().click();
      await p.getByRole('button', { name: /^(SIGUIENTE|VER RESULTADOS|NEXT|SEE RESULTS|VIEW RESULTS)$/ }).click();
      await p.getByRole('button', { name: /^(Saltar recuento|Skip count)/ }).click({ timeout: 5000 }).catch(() => {});
    },
    listo: '[data-testid="summary-grade"]',
  },
  { id: 'rutas', signedIn: true, url: '/', abre: async (p) => { await goto(p, 'tracks'); }, listo: '[role="progressbar"]' },
  { id: 'perfil', signedIn: true, url: '/', abre: async (p) => { await goto(p, 'profile'); }, listo: 'h1:has-text("Ana")' },
  { id: 'liga', signedIn: true, url: '/', abre: async (p) => { await goto(p, 'league'); }, listo: '[data-testid="league-rows"]' },
];

for (const lang of ['es', 'en'] as const) {
  for (const theme of ['dark', 'light'] as const) {
    for (const width of [390, 1280]) {
      test.describe(`${lang} · ${theme} · ${width}`, () => {
        test.use({ locale: lang === 'es' ? 'es-ES' : 'en-US', viewport: { width, height: width === 390 ? 844 : 800 } });

        for (const s of PANTALLAS) {
          test(s.id, async ({ page }) => {
            await page.clock.setFixedTime(new Date('2026-10-21T10:00:00Z'));
            await page.addInitScript(([th, lg]) => {
              try { localStorage.setItem('whetzy_theme', th); localStorage.setItem('whetzy_lang', lg); } catch { /* sin storage */ }
            }, [theme, lang] as const);
            // Una pantalla que revienta deja el lienzo en blanco y la captura «cuadra»
            // con una baseline en blanco: los errores de página fallan el test.
            const errores: string[] = [];
            page.on('pageerror', (e) => errores.push(e.message));
            await mockApi(page, { signedIn: s.signedIn, lang });
            await page.goto(s.url);
            await s.abre(page);
            await expect(page.locator(String(s.listo)).first()).toBeVisible({ timeout: 15_000 });
            await page.evaluate(() => document.fonts.ready);
            await page.waitForTimeout(500);
            // Cifras vivas (racha, XP, contadores, puestos): fijas por el mock, pero
            // enmascaradas igual para que un reparto nuevo de la liga no ensucie el diff.
            const mask = [
              page.locator('[class*="topbar_"] [class*="stat"]'),
              page.getByTestId('missions-count'),
              page.getByTestId('summary-grade'),
            ];
            expect(errores, 'la pantalla lanzó una excepción').toEqual([]);
            await expect(page).toHaveScreenshot(`${s.id}-${lang}-${theme}-${width}.png`, { mask });
          });
        }
      });
    }
  }
}
