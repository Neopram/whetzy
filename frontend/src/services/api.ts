// Same-origin by default: in dev, Vite proxies /api → backend (see vite.config.ts);
// in production set VITE_API_URL to the deployed backend origin + /api/v1.
/** Error de API que conserva el código HTTP.
 *
 *  Sin esto, quien llama recibe un `Error` con un mensaje y no puede separar
 *  «tus credenciales no valen» (401, hay que cerrar sesión) de «el servidor
 *  está reiniciando» (502, hay que esperar). `status` es `null` cuando la
 *  petición ni siquiera llegó a salir.
 */
/** Forma del `detail` del 429 de cupo Free (`content_quota.quota_detail`, 39.4/39.34). */
export interface QuotaErrorDetail {
  code: 'free_daily_quota';
  kind: 'questions' | 'lessons';
  limit: number;
  resets_at: string;
}

export class ApiError extends Error {
  readonly status: number | null;
  /** El `detail` crudo del backend — string en la mayoría de errores, o un
   *  objeto estructurado como `QuotaErrorDetail` para el cupo Free. `message`
   *  siempre queda como una cadena comparable (el `code` cuando `detail` es
   *  un objeto), así que el patrón `err.message === 'tutor_daily_limit'` que
   *  ya usa WhyButton.tsx sigue funcionando sin cambios. */
  readonly detail: unknown;

  constructor(message: string, status: number | null, detail?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }

  /** Fallo de red o servidor caído: reintentar tiene sentido. */
  get esTransitorio(): boolean {
    return this.status === null || this.status >= 500;
  }
}

/** True si este error es el 429 del cupo diario Free (39.4/39.34), con el
 *  `detail` estructurado (kind, limit, resets_at) ya validado. */
export function isQuotaError(err: unknown): err is ApiError & { detail: QuotaErrorDetail } {
  return (
    err instanceof ApiError &&
    err.status === 429 &&
    typeof err.detail === 'object' &&
    err.detail !== null &&
    (err.detail as { code?: unknown }).code === 'free_daily_quota'
  );
}

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

/** Origen de la API para cualquier `fetch` fuera de este modulo. Una ruta
 *  relativa ('/api/v1/...') en produccion va a Cloudflare, no al backend
 *  (incidente de login 2026-09-24); `test/api.baseUrl.test.ts` lo vigila. */
export const API_BASE_URL = BASE_URL;

// Migration cleanup: remove legacy localStorage tokens from pre-cookie auth.
// The backend now sets HttpOnly cookies; these keys are no longer written.
(function clearLegacyTokens() {
  try {
    localStorage.removeItem('whetzy_access_token');
    localStorage.removeItem('whetzy_refresh_token');
  } catch {
    /* storage unavailable */
  }
})();

const LOGGED_IN_COOKIE = 'whetzy_logged_in';

function hasCookie(name: string): boolean {
  try {
    return document.cookie.split(';').some((c) => c.trim().startsWith(name + '='));
  } catch {
    return false;
  }
}

/** Solo fiable cuando frontend y backend comparten dominio (desarrollo local):
 *  `whetzy_logged_in` es un cookie host-only del dominio que respondió al
 *  login, así que en producción (`whetzy.com` contra
 *  `api-production-9751.up.railway.app`, dominios distintos) nunca es
 *  visible aquí, entre o no la sesión (30.9). `App.tsx` ya no confía en
 *  esto para decidir el estado inicial: siempre pregunta a `/auth/me`. */
export function isAuthenticated(): boolean {
  return hasCookie(LOGGED_IN_COOKIE);
}

/** Antes no llamaba a nada («el servidor limpia los cookies vía
 *  /auth/logout» era el comentario, pero /auth/logout nunca se invocaba):
 *  cerrar sesión solo borraba el estado local, y las cookies HttpOnly
 *  seguían siendo válidas en el navegador — al recargar, la sesión "cerrada"
 *  volvía. Best-effort: si ya no hay sesión que revocar, el 401 se ignora. */
export async function logout(): Promise<void> {
  try {
    await request('/auth/logout', { method: 'POST' });
  } catch {
    /* la sesión ya no era válida, o no hay red: no hay nada más que hacer aquí */
  }
}

function getHeaders(): HeadersInit {
  return { 'Content-Type': 'application/json' };
}

async function tryRefresh(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    });
    if (!res.ok) return false;
    return true;
  } catch {
    return false;
  }
}

async function request<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { ...getHeaders(), ...options.headers },
    credentials: 'include',
  });

  if (res.status === 401 && retry && path !== '/auth/refresh') {
    if (await tryRefresh()) {
      return request<T>(path, options, false);
    }
    throw new ApiError('Unauthorized', 401);
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail: unknown = body.detail;
    // `detail` es casi siempre un string (FastAPI HTTPException), pero
    // content_quota.py (39.4) lo manda como objeto {code, kind, limit,
    // resets_at} para que la UI pueda construir el mensaje del cupo (39.34).
    // Antes esta rama descartaba el objeto entero y dejaba `message` como
    // "HTTP 429" sin ningún dato aprovechable.
    const message =
      typeof detail === 'string'
        ? detail
        : detail && typeof detail === 'object' && typeof (detail as { code?: unknown }).code === 'string'
          ? (detail as { code: string }).code
          : `HTTP ${res.status}`;
    throw new ApiError(message, res.status, detail);
  }

  return res.json();
}

export interface UserRead {
  id: string;
  email: string;
  username: string;
  display_name: string;
  language: 'es' | 'en';
  avatar_emoji: string;
  level: number;
  total_xp: number;
  current_streak: number;
  max_streak: number;
  streak_freeze_available: number;
  last_active: string | null;
  created_at: string;
  is_premium: boolean;
  /** Plan ganado con referidos (ADR-57), solo mientras está en fecha. */
  granted_tier?: 'plus' | 'pro' | null;
  granted_tier_expires_at?: string | null;
  /** true si se dio de baja de los correos de ofertas. */
  marketing_emails_opt_out?: boolean;
  is_admin?: boolean;
}

export interface RegisterPayload {
  email: string;
  username: string;
  display_name: string;
  password: string;
  language: 'es' | 'en';
  age_confirmed: boolean;
}

export interface UpdateMePayload {
  display_name?: string;
  avatar_emoji?: string;
  language?: 'es' | 'en';
  /** Índice de la opción elegida en el onboarding (0-2). */
  onboarding_experience?: number;
  onboarding_goal?: number;
  onboarding_weekly_time?: number;
}

export type OAuthProvider = 'github' | 'google';

export const auth = {
  async register(payload: RegisterPayload) {
    return request<{ access_token: string; refresh_token: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async login(email: string, password: string) {
    const form = new URLSearchParams();
    form.set('username', email);
    form.set('password', password);
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
      credentials: 'include',
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(typeof body.detail === 'string' ? body.detail : 'Incorrect email or password');
    }
    return (await res.json()) as { access_token: string; refresh_token: string };
  },

  async me() {
    return request<UserRead>('/auth/me');
  },

  /** Guarda en el servidor lo editable del perfil. Sin esto el idioma elegido
   *  solo vivía en el estado local y al recargar volvía el del registro. */
  async updateMe(patch: UpdateMePayload) {
    return request<UserRead>('/auth/me', { method: 'PATCH', body: JSON.stringify(patch) });
  },

  /** Correos de ofertas (hoy, el de reactivación). Los de la cuenta no se apagan. */
  async setMarketingEmails(marketing: boolean) {
    return request<{ marketing: boolean }>('/email/preferences', {
      method: 'PATCH',
      body: JSON.stringify({ marketing }),
    });
  },

  /** Proveedores OAuth con credenciales en el servidor. Vacío si no hay ninguno. */
  async oauthProviders() {
    return request<{ providers: OAuthProvider[] }>('/auth/oauth/providers');
  },

  /** Navigate the browser to the OAuth provider start URL (full page redirect, no SDK). */
  startOAuth(provider: OAuthProvider) {
    window.location.href = `${BASE_URL}/auth/oauth/${provider}/start`;
  },

  async requestPasswordReset(email: string) {
    return request<{ message: string }>(`/auth/forgot-password`, {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  },

  async resetPassword(token: string, new_password: string) {
    return request<{ message: string }>(`/auth/reset-password`, {
      method: 'POST',
      body: JSON.stringify({ token, new_password }),
    });
  },
};

export interface QuestionPublic {
  id: string;
  skill_id: string;
  /** `multiple_choice` es el mismo formato que `mcq`; el banco usa los dos
   *  nombres (1.015 preguntas con el segundo), y faltaba en este union. */
  type:
    | 'mcq'
    | 'multiple_choice'
    | 'true_false'
    | 'code_output'
    | 'fill_blank'
    | 'fill_blank_exec'
    | 'fix_bug'
    | 'sql_exec'
    | 'js_exec';
  difficulty_tier: 'easy' | 'medium' | 'hard' | 'expert';
  question_es: string;
  question_en: string;
  options_es: string[] | null;
  options_en: string[] | null;
  /** Expected stdout for exec types (fill_blank_exec, fix_bug). Used for client-side Pyodide grading. */
  correct_answer_es: string | null;
  correct_answer_en: string | null;
  /** Runnable template for types that don't embed a fenced ``` block in the
   *  prose (sql_exec). `fill_blank_exec`/`fix_bug` carry theirs inside
   *  question_es/question_en instead, so these stay absent for them. */
  code_es?: string | null;
  code_en?: string | null;
  expected_time_ms: number;
}

export interface SelectionReason {
  pool: string;
  skill_strategy: string | null;
  difficulty_target: number | null;
  expected_p: number | null;
}

export interface QuizStartResponse {
  session_id: string;
  mode: string;
  question: QuestionPublic | null;
  reviews_due: number;
  selection_reason: SelectionReason | null;
}

export interface QuizAnswerResponse {
  correct: boolean;
  correct_index: number | null;
  explanation_es: string;
  explanation_en: string;
  source: string | null;
  grade: number;
  xp_earned: number;
  combo: number;
  user_elo: number;
  next_review: string | null;
  skill_mastery: Record<string, number>;
  session_accuracy: number;
  next_question: QuestionPublic | null;
  next_selection_reason: SelectionReason | null;
  /** Free daily quota used up (39.4): no next question until the next UTC day. */
  quota_reached?: boolean;
}

export interface QuizEndResponse {
  total_questions: number;
  correct: number;
  accuracy: number;
  max_combo: number;
  xp_earned: number;
  duration_seconds: number;
}

export const quiz = {
  async start(mode: string, trackId?: string, skillId?: string) {
    return request<QuizStartResponse>('/quiz/start', {
      method: 'POST',
      body: JSON.stringify({ mode, track_id: trackId ?? null, skill_id: skillId ?? null }),
    });
  },

  async answer(
    sessionId: string,
    questionId: string,
    selectedIndex: number | null,
    responseTimeMs: number,
    declaredUnknown = false,
    eventId?: string,
  ) {
    return request<QuizAnswerResponse>('/quiz/answer', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        question_id: questionId,
        selected_index: selectedIndex,
        response_time_ms: responseTimeMs,
        declared_unknown: declaredUnknown,
        ...(eventId ? { event_id: eventId } : {}),
      }),
    });
  },

  async end(sessionId: string) {
    return request<QuizEndResponse>('/quiz/end', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    });
  },

  async reviewDue() {
    return request<{ due_count: number }>('/quiz/review-due');
  },
};

export interface TrackMastery {
  track_id: string;
  name_es: string;
  name_en: string;
  icon: string;
  color: string;
  average_mastery: number;
  skills_mastered: number;
  total_skills: number;
}

export interface DashboardResponse {
  level: number;
  total_xp: number;
  current_streak: number;
  max_streak: number;
  streak_freeze_available: number;
  last_active: string | null;
  reviews_due: number;
  tracks: TrackMastery[];
  total_sessions: number;
  total_questions_answered: number;
  overall_accuracy: number;
}

export interface SkillMasteryDetail {
  skill_id: string;
  name_es: string;
  name_en: string;
  module_id: string;
  p_known: number;
  elo_rating: number;
  attempts: number;
  correct_count: number;
  accuracy: number;
  mastered: boolean;
  fsrs_due: string | null;
}

export interface CurriculumSkill {
  skill_id: string;
  name_es: string;
  name_en: string;
  order: number;
  p_known: number;
  mastered: boolean;
  attempts: number;
  /** 32.4: si ya abrió la lección de este skill — el backend bloquea el quiz si no. */
  lesson_seen: boolean;
}

export interface CurriculumModule {
  id: string;
  name_es: string;
  name_en: string;
  order: number;
  description_es: string;
  description_en: string;
  min_mastery_to_unlock: number;
  level: number;
  average_mastery: number;
  status: 'locked' | 'available' | 'completed';
  prerequisite_id: string | null;
  prerequisite_met: boolean;
  skills: CurriculumSkill[];
}

export interface CurriculumResponse {
  track_id: string;
  name_es: string;
  name_en: string;
  icon: string;
  color: string;
  mastery_threshold: number;
  modules: CurriculumModule[];
}

export interface DecayingSkill {
  skill_id: string;
  name_es: string;
  name_en: string;
  track_id: string;
  p_known: number;
  due_at: string;
  /** Negative when the review is already overdue. */
  days_until_due: number;
}

export const progress = {
  async dashboard() {
    return request<DashboardResponse>('/progress/dashboard');
  },
  async decaying(withinDays = 7, limit = 5) {
    return request<DecayingSkill[]>(`/progress/decaying?within_days=${withinDays}&limit=${limit}`);
  },
  async skills(trackId?: string, moduleId?: string) {
    const qs = new URLSearchParams();
    if (trackId) qs.set('track_id', trackId);
    if (moduleId) qs.set('module_id', moduleId);
    const suffix = qs.toString() ? `?${qs}` : '';
    return request<SkillMasteryDetail[]>(`/progress/skills${suffix}`);
  },
  async curriculum(trackId: string) {
    return request<CurriculumResponse>(`/progress/curriculum?track_id=${encodeURIComponent(trackId)}`);
  },
};

export interface GlossaryTerm {
  id: string;
  track_id: string;
  term_es: string;
  term_en: string;
  definition_es: string;
  definition_en: string;
  source: string | null;
  order: number;
}

export const glossary = {
  async forTrack(trackId: string) {
    return request<GlossaryTerm[]>(`/glossary/${encodeURIComponent(trackId)}`);
  },
};

export interface LessonRead {
  id: string;
  skill_id: string;
  title_es: string;
  title_en: string;
  body_es: string;
  body_en: string;
  example_code: string | null;
  example_output: string | null;
  source: string;
  order: number;
}

export const lessonsApi = {
  async forSkill(skillId: string) {
    return request<LessonRead[]>(`/lessons/${encodeURIComponent(skillId)}`);
  },
};

export interface PlacementStartResponse {
  session_id: string;
  track_id: string;
  question: QuestionPublic | null;
  questions_answered: number;
}

export interface PlacementAnswerResponse {
  correct: boolean;
  ability_estimate: number;
  ability_se: number;
  questions_answered: number;
  finished: boolean;
  next_question: QuestionPublic | null;
}

export interface ModuleSkipRecommendation {
  module_id: string;
  module_name_es: string;
  module_name_en: string;
  accuracy: number;
  questions_seen: number;
  can_skip: boolean;
}

export interface PlacementResult {
  session_id: string;
  track_id: string;
  ability_estimate: number;
  ability_se: number;
  total_questions: number;
  correct: number;
  accuracy: number;
  /** 0-1. Baja cuando el motor se quedo sin preguntas antes de estabilizar. */
  reliability: number;
  skill_mastery: Record<string, number>;
  module_recommendations: ModuleSkipRecommendation[];
}

/** Prueba de nivel adaptativa (CAT con IRT) — el motor vive en el servidor.
 *
 *  Las tres funciones tenian una forma que el backend nunca expuso: `start` no
 *  mandaba `track_id`, `answer` mandaba `answer_index` en vez de
 *  `selected_index` y sin el tiempo de respuesta, y `result` pedia
 *  `/placement/{id}/result`, que devolvia 404. Los tests no lo vieron porque
 *  moquean `fetch`; ahora lo cubre `backend/tests/test_contrato_frontend.py`.
 */
export const placement = {
  async start(trackId: string) {
    return request<PlacementStartResponse>('/placement/start', {
      method: 'POST',
      body: JSON.stringify({ track_id: trackId }),
    });
  },

  async answer(sessionId: string, questionId: string, selectedIndex: number, responseTimeMs: number) {
    return request<PlacementAnswerResponse>('/placement/answer', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        question_id: questionId,
        selected_index: selectedIndex,
        // El motor lo guarda con la respuesta; mandar algo negativo es un 422.
        response_time_ms: Math.max(0, Math.round(responseTimeMs)),
      }),
    });
  },

  async result(sessionId: string) {
    const qs = new URLSearchParams({ session_id: sessionId });
    return request<PlacementResult>(`/placement/result?${qs}`);
  },
};

export interface LeagueStandingEntry {
  rank: number;
  user_id: string;
  username: string;
  display_name: string;
  avatar_emoji: string;
  xp_earned: number;
  is_current_user: boolean;
}

export interface LeagueStandingsResponse {
  league: { id: string; name: string; tier: string; min_xp: number };
  week_start: string;
  standings: LeagueStandingEntry[];
  promotion_zone: number;
  demotion_zone: number;
  /** false = salió de las ligas (35.4): `standings` viene vacío. */
  participating: boolean;
}

export interface UserMissionRead {
  mission: { id: string; type: string; target_value: number; xp_reward: number; name_es: string; name_en: string };
  progress: number;
  completed: boolean;
  date: string;
}

export interface UserBadgeWithDetail {
  badge: {
    id: string; name_es: string; name_en: string; icon: string;
    description_es: string; description_en: string; criteria_type: string; criteria_value: number;
  };
  earned_at: string;
}

export interface ExplainResponse {
  explanation: string;
  provider: string;
  grounded: boolean;
  times_missed: number;
}

export const tutor = {
  async explain(questionId: string) {
    return request<ExplainResponse>('/tutor/explain', {
      method: 'POST',
      body: JSON.stringify({ question_id: questionId }),
    });
  },
};

/** Comodín de racha (35.3). `blocked_by` es un código estable que la UI traduce. */
export type StreakFreezeBlock = 'insufficient_credits' | 'max_held' | 'weekly_limit';

export interface StreakFreezeQuote {
  price: number;
  balance: number;
  held: number;
  max_held: number;
  purchases_this_week: number;
  max_per_week: number;
  can_buy: boolean;
  blocked_by: StreakFreezeBlock | null;
}

export interface CreditBalance {
  balance: number;
  currency: string;
  expires_in_days: number;
}

export interface ReferralCodeInfo {
  code: string;
  share_url: string;
}

export interface PromoRedeemResult {
  credits: number;
  balance: number;
  message: string;
}

export interface CreditPrices {
  credit_value_usd: number;
  /** `milestones`: hitos de la escalera de referidos (ADR-35): n.º de abonados → premio. */
  grifos: { event: string; credits: number; cap: string; milestones?: { at: number; reward: string }[] }[];
  sumideros: { item: string; cost: number }[];
}

export const economy = {
  async balance() {
    return request<CreditBalance>('/economy/balance');
  },
  async prices() {
    return request<CreditPrices>('/economy/prices');
  },
  async referralCode() {
    return request<ReferralCodeInfo>('/economy/referral/code');
  },
  async redeemPromo(code: string) {
    return request<PromoRedeemResult>('/economy/promo/redeem', {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
  },
  async streakFreeze() {
    return request<StreakFreezeQuote>('/economy/streak-freeze');
  },
  async buyStreakFreeze(requestId: string) {
    return request<StreakFreezeQuote & { replayed: boolean }>('/economy/streak-freeze', {
      method: 'POST',
      body: JSON.stringify({ request_id: requestId }),
    });
  },
  async activateReferral(referralCode: string) {
    return request<{ activated: boolean; message?: string }>('/economy/referral/activate', {
      method: 'POST',
      body: JSON.stringify({ referral_code: referralCode }),
    });
  },
};

/** Motivos de reporte (backend: models/question_report.py VALID_REASONS). */
export type ReportReason = 'wrong_answer' | 'typo' | 'outdated' | 'confusing' | 'other' | 'ai_explanation';

export const reports = {
  /** Reporta una pregunta defectuosa o una explicación del tutor IA (`ai_explanation`). */
  async question(questionId: string, reason: ReportReason, notes?: string) {
    return request<{ id: string; message: string }>('/reports/question', {
      method: 'POST',
      body: JSON.stringify({ question_id: questionId, reason, notes: notes?.trim() || undefined }),
    });
  },
};

export const league = {
  async current() {
    return request<LeagueStandingsResponse>('/league/current');
  },
  /** Entrar o salir de las ligas. Salir no toca XP, nivel ni racha. */
  async setParticipation(participate: boolean) {
    return request<LeagueStandingsResponse>('/league/participation', {
      method: 'PUT',
      body: JSON.stringify({ participate }),
    });
  },
};

export const gamification = {
  async missions() {
    return request<UserMissionRead[]>('/missions');
  },
  async badges() {
    return request<UserBadgeWithDetail[]>('/badges');
  },
};

export interface DuelChallengeRequest {
  opponent_username: string;
  skill_id?: string;
}

export interface DuelChallengeResponse {
  duel_id: string;
  skill_id: string;
  questions: QuestionPublic[];
  opponent_username: string;
}

export interface DuelAnswerRequest {
  question_id: string;
  selected_index: number;
  response_time_ms: number;
}

export interface DuelAnswerResponse {
  duel_id: string;
  answers_so_far: number;
  completed: boolean;
  opponent_completed: boolean;
}

export interface DuelPlayerResult {
  user_id: string;
  username: string;
  display_name: string;
  avatar_emoji: string;
  correct: number;
  total_time_ms: number;
}

export interface DuelResultResponse {
  duel_id: string;
  status: string;
  skill_id: string;
  challenger: DuelPlayerResult;
  opponent: DuelPlayerResult;
  winner_id: string | null;
  is_draw: boolean;
  created_at: string;
}

export interface DuelSummary {
  duel_id: string;
  status: string;
  skill_id: string;
  opponent_username: string;
  opponent_avatar: string;
  your_correct: number | null;
  opponent_correct: number | null;
  winner_id: string | null;
  is_your_turn: boolean;
  created_at: string;
}

export const duels = {
  async challenge(payload: DuelChallengeRequest) {
    return request<DuelChallengeResponse>('/duels/challenge', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  async my() {
    return request<DuelSummary[]>('/duels/my');
  },
  async answer(duelId: string, payload: DuelAnswerRequest) {
    return request<DuelAnswerResponse>(`/duels/${duelId}/answer`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  async join(duelId: string) {
    return request<DuelChallengeResponse>(`/duels/${duelId}/join`);
  },
  async result(duelId: string) {
    return request<DuelResultResponse>(`/duels/${duelId}/result`);
  },
};

// ── Tracks (Q.14) ─────────────────────────────────────────────────────────────

export interface TrackRead {
  id: string;
  name_es: string;
  name_en: string;
  order: number;
  icon: string;
  color: string;
  total_questions: number;
  /** Certification tracks only; null on a learning track. The client uses this
   *  to decide whether to offer a mock exam, instead of keeping its own list. */
  is_certification: boolean;
  cert_provider: string | null;
  exam_question_count: number | null;
  exam_duration_minutes: number | null;
}

export const content = {
  async tracks() {
    return request<TrackRead[]>('/content/tracks');
  },
};

// ── Certification mock exam (10.3) ────────────────────────────────────────────

export interface MockExamStartResponse {
  attempt_id: string;
  track_id: string;
  duration_minutes: number;
  started_at: string;
  /** The deadline is the server's, not the browser's: a timed mock whose clock
   *  lives in the client is only timed until someone reloads. */
  expires_at: string;
  questions: QuestionPublic[];
}

export interface MockExamDomainResult {
  domain_id: string;
  name_es: string;
  name_en: string;
  weight_pct: number;
  correct: number;
  total: number;
  pct: number | null;
  /** False when the domain carries too few questions for its percentage to
   *  mean anything — the exam guide asks for caution reading section feedback. */
  enough_questions_to_judge: boolean;
}

export interface MockExamReport {
  track_id: string;
  questions: number;
  answered: number;
  unanswered: number;
  correct: number;
  raw_pct: number;
  per_domain: MockExamDomainResult[];
  elapsed_seconds: number;
  duration_minutes: number;
  scoring_note_es: string;
  scoring_note_en: string;
  per_domain_caveat_es: string;
  per_domain_caveat_en: string;
  /** Only the certifying exam declares a pass; the mock leaves these null. */
  pass_pct?: number | null;
  passed?: boolean | null;
  pass_note_es?: string | null;
  pass_note_en?: string | null;
}

export interface MockExamSubmitResponse {
  attempt_id: string;
  status: string;
  expired: boolean;
  report: MockExamReport;
  /** Set only when a certifying exam was passed on time. */
  certificate?: CertificatePublic | null;
}

// ── Track final exam and module test-out (17.2) ─────────────────────────────

export interface TrackExamBlueprint {
  track_id: string;
  skills: number;
  questions: number;
  duration_minutes: number;
  pass_pct: number;
}

export interface TrackExamStartResponse {
  attempt_id: string;
  track_id: string;
  module_id: string | null;
  kind: 'track_final' | 'test_out';
  duration_minutes: number;
  pass_pct: number;
  started_at: string;
  expires_at: string;
  questions: QuestionPublic[];
}

export interface TrackExamSkillResult {
  skill_id: string;
  name_es: string;
  name_en: string;
  correct: number;
  total: number;
  pct: number | null;
}

export interface TrackExamReport {
  track_id: string;
  module_id: string | null;
  kind: string;
  questions: number;
  answered: number;
  unanswered: number;
  correct: number;
  raw_pct: number;
  pass_pct: number;
  passed: boolean;
  per_skill: TrackExamSkillResult[];
  elapsed_seconds: number;
  duration_minutes: number;
  scoring_note_es: string;
  scoring_note_en: string;
}

export interface TrackExamSubmitResponse {
  attempt_id: string;
  status: string;
  expired: boolean;
  report: TrackExamReport;
  /** Only ever set for a passed, on-time track final. */
  certificate: CertificatePublic | null;
  /** Skill id -> mastery after the sitting. Only a passed test-out fills this. */
  mastery_updated: Record<string, number>;
}

export const exams = {
  async startMock(trackId: string) {
    return request<MockExamStartResponse>('/exams/mock/start', {
      method: 'POST',
      body: JSON.stringify({ track_id: trackId }),
    });
  },

  async submitMock(attemptId: string, answers: Record<string, number>) {
    return request<MockExamSubmitResponse>(`/exams/mock/${attemptId}/submit`, {
      method: 'POST',
      body: JSON.stringify({
        answers: Object.entries(answers).map(([question_id, selected_index]) => ({
          question_id,
          selected_index,
        })),
      }),
    });
  },

  async getMock(attemptId: string) {
    return request<MockExamSubmitResponse>(`/exams/mock/${attemptId}`);
  },

  // ── Certifying exam, one-time payment (38.7, ADR-49) ─────────────────────

  async certificationAccess(trackId: string) {
    return request<CertificationAccess>(`/exams/certification/${trackId}/access`);
  },

  /** Same draw and clock as the mock; submit it with `submitMock`. 402 = not bought. */
  async startCertifying(trackId: string) {
    return request<MockExamStartResponse>(`/exams/certification/${trackId}/start`, {
      method: 'POST',
    });
  },

  // ── Track final exam and module test-out (17.2) ───────────────────────────

  /** What the sitting will look like, so the learner can decide before starting. */
  async trackBlueprint(trackId: string) {
    return request<TrackExamBlueprint>(`/exams/track/${trackId}/blueprint`);
  },

  async startTrackExam(trackId: string) {
    return request<TrackExamStartResponse>(`/exams/track/${trackId}/start`, { method: 'POST' });
  },

  async startTestOut(moduleId: string) {
    return request<TrackExamStartResponse>(`/exams/module/${moduleId}/test-out/start`, {
      method: 'POST',
    });
  },

  async certificationReadiness(trackId: string) {
    return request<CertificationReadiness>(`/exams/certification/${trackId}/readiness`);
  },

  /** Submits a sitting — the attempt id, not the track: you can sit a track twice. */
  async submitTrackExam(attemptId: string, answers: Record<string, number>) {
    return request<TrackExamSubmitResponse>(`/exams/track/${attemptId}/submit`, {
      method: 'POST',
      body: JSON.stringify({
        answers: Object.entries(answers).map(([question_id, selected_index]) => ({
          question_id,
          selected_index,
        })),
      }),
    });
  },
};

// ── Certification readiness (18.1) ──────────────────────────────────────────

export interface DomainReadiness {
  domain_id: string;
  name_es: string;
  name_en: string;
  weight_pct: number;
  p_known_mean: number;
  skills_assessed: number;
  skills_total: number;
  ready: boolean;
}

export interface CertificationReadiness {
  track_id: string;
  domains: DomainReadiness[];
  overall_p_known: number;
}

// ── Certificates (17.2) ─────────────────────────────────────────────────────

export interface CertificatePublic {
  code: string;
  username: string;
  track_id: string;
  track_name_es: string;
  track_name_en: string;
  score_pct: number;
  questions: number;
  issued_at: string;
  revoked: boolean;
  /** A certification track's certificate is a "Whetzy preparation certificate". */
  is_certification?: boolean;
}

export interface CertificationAccess {
  track_id: string;
  price_usd: number;
  paywall_enabled: boolean;
  purchased: boolean;
  can_start: boolean;
}

export const certificates = {
  /** Public on purpose — whoever verifies a certificate has no account here.
   *
   * No special "anonymous" path is needed: the endpoint declares no auth
   * dependency, so a visitor with no token is served exactly like one with a
   * token, and the 401-refresh branch above can never fire on it.
   */
  async verify(code: string) {
    return request<CertificatePublic>(`/exams/certificates/${code}`);
  },
};


export interface InstructorCourse {
  id: string;
  instructor_id: string;
  title: string;
  description: string | null;
  price_cents: number;
  video_url: string | null;
  materials_url: string | null;
  enrolled_count: number;
  revenue_cents: number;
  status: string;
  created_at: string;
}

export interface InstructorAnalytics {
  total_earnings_cents: number;
  pending_payout_cents: number;
  active_courses: number;
  total_students: number;
  avg_completion_percent: number;
}

export interface InstructorPayout {
  id: string;
  period_start: string;
  period_end: string;
  earnings_cents: number;
  status: string;
  payout_date: string | null;
}

/** Marketplace de instructores (serie 28).
 *
 *  El reparto es 80/20 (ADR-41) tras la comisión de Paddle y la retención que fija
 *  H.29; ese cálculo vive en el backend a propósito, para que el cliente no
 *  pueda enseñar una cifra que no sea la que se va a pagar.
 */
export const instructor = {
  async courses() {
    return request<InstructorCourse[]>('/instructor/courses');
  },

  async createCourse(payload: {
    title: string;
    description?: string | null;
    price_cents: number;
    video_url?: string | null;
    materials_url?: string | null;
  }) {
    return request<InstructorCourse>('/instructor/courses', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async analytics() {
    return request<InstructorAnalytics>('/instructor/analytics');
  },

  async payouts() {
    return request<InstructorPayout[]>('/instructor/payouts');
  },
};

// ── Projects (18.8 / 19.6) ────────────────────────────────────────────

export interface ProjectStepRead {
  id: string;
  step_number: number;
  title_es: string;
  title_en: string;
  instructions_es: string;
  instructions_en: string;
  starter_code: string;
  test_code: string;
}

export interface ProjectRead {
  id: string;
  slug: string;
  track_id: string;
  runtime: 'python' | 'sql' | 'js';
  name_es: string;
  name_en: string;
  description_es: string;
  description_en: string;
  difficulty: number;
  source_url: string;
  source_license: string;
  order: number;
}

export interface ProjectDetail extends ProjectRead {
  steps: ProjectStepRead[];
}

export interface ProjectSubmissionRead {
  id: string;
  project_id: string;
  current_step: number;
  completed: boolean;
  started_at: string;
  completed_at: string | null;
}

export const projects = {
  async list(trackId?: string, runtime?: string) {
    const params = new URLSearchParams();
    if (trackId) params.set('track_id', trackId);
    if (runtime) params.set('runtime', runtime);
    const qs = params.toString();
    const path = '/projects' + (qs ? '?' + qs : '');
    return request<ProjectRead[]>(path);
  },

  async get(slug: string) {
    return request<ProjectDetail>(`/projects/${slug}`);
  },

  async start(slug: string) {
    return request<ProjectSubmissionRead>(`/projects/${slug}/start`, { method: 'POST' });
  },

  async progress(slug: string) {
    return request<ProjectSubmissionRead>(`/projects/${slug}/progress`);
  },

  async submitStep(slug: string, stepNumber: number, passed: boolean) {
    return request<ProjectSubmissionRead>(`/projects/${slug}/submit-step`, {
      method: 'POST',
      body: JSON.stringify({ step_number: stepNumber, passed }),
    });
  },
};

// ── Privacy (21.3) ──────────────────────────────────────────────────────────

export interface CcpaOptOutResponse {
  ccpa_opt_out: boolean;
}

export interface CcpaDisclosure {
  categories_collected: string[];
  categories_shared: string[];
  business_purpose: string[];
  sale_of_data: string;
  right_to_delete: string;
  right_to_know: string;
  right_to_opt_out: string;
  non_discrimination: string;
}

export interface PrivacyRights {
  jurisdiction_note: string;
  rights: string[];
  data_export_url: string;
  delete_account_url: string;
  contact: string;
}

export const privacy = {
  ccpaOptOut: () => request<CcpaOptOutResponse>('/privacy/ccpa-opt-out', { method: 'POST' }),
  ccpaOptIn: () => request<CcpaOptOutResponse>('/privacy/ccpa-opt-out', { method: 'DELETE' }),
  ccpaDisclosure: () => request<CcpaDisclosure>('/privacy/ccpa-disclosure'),
  rights: () => request<PrivacyRights>('/privacy/rights'),
};

export interface CheckoutResponse {
  checkout_url: string;
}

export interface SubscriptionResponse {
  is_premium: boolean;
  subscription_status: string | null;
  subscription_tier: string | null;
  subscription_provider: string | null; // "stripe" | "revenuecat" | "paddle" | null (17.14, H.29)
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
}

export const billing = {
  checkout: (priceId: string, euWithdrawalWaiver: boolean = false) =>
    request<CheckoutResponse>('/billing/checkout', {
      method: 'POST',
      body: JSON.stringify({ price_id: priceId, eu_withdrawal_waiver: euWithdrawalWaiver }),
    }),
  subscription: () => request<SubscriptionResponse>('/billing/subscription'),
  /** Público: token de cliente y precios `pri_` para abrir Paddle.js (H.29). */
  paddleConfig: () => request<PaddleConfig>('/billing/paddle/config'),
  /** Cancela al final del periodo pagado; el estado lo actualiza el webhook. */
  cancelPaddle: () =>
    request<{ cancel_requested: boolean; access_until: string | null }>('/billing/paddle/cancel', { method: 'POST' }),
};

export interface PaddleConfig {
  enabled: boolean;
  environment: 'sandbox' | 'production';
  client_token: string | null;
  prices: { plus: string | null; pro: string | null; certification: string | null };
}
