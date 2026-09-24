// Same-origin by default: in dev, Vite proxies /api → backend (see vite.config.ts);
// in production set VITE_API_URL to the deployed backend origin + /api/v1.
/** Error de API que conserva el código HTTP.
 *
 *  Sin esto, quien llama recibe un `Error` con un mensaje y no puede separar
 *  «tus credenciales no valen» (401, hay que cerrar sesión) de «el servidor
 *  está reiniciando» (502, hay que esperar). `status` es `null` cuando la
 *  petición ni siquiera llegó a salir.
 */
export class ApiError extends Error {
  readonly status: number | null;

  constructor(message: string, status: number | null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }

  /** Fallo de red o servidor caído: reintentar tiene sentido. */
  get esTransitorio(): boolean {
    return this.status === null || this.status >= 500;
  }
}

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

/** Origen de la API para cualquier `fetch` fuera de este modulo. Una ruta
 *  relativa ('/api/v1/...') en produccion va a Cloudflare, no al backend
 *  (incidente de login 2026-09-24); `test/api.baseUrl.test.ts` lo vigila. */
export const API_BASE_URL = BASE_URL;

// Consume OAuth tokens from URL params immediately at module-import time.
// The backend redirects here after OAuth callback with ?oauth_token=...&oauth_refresh=...
// Writing directly to localStorage (not via persistTokens) avoids the TDZ problem:
// `accessToken` / `refreshToken` are declared with `let` AFTER this code, so they
// are in the Temporal Dead Zone here. localStorage is always available.
(function consumeOAuthParams() {
  try {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('oauth_token');
    const refresh = params.get('oauth_refresh');
    if (token) {
      localStorage.setItem('whetzy_access_token', token);
      if (refresh) localStorage.setItem('whetzy_refresh_token', refresh);
      window.history.replaceState(null, '', window.location.pathname + window.location.hash);
    }
  } catch {
    /* storage unavailable in this context */
  }
})();

const ACCESS_KEY = 'whetzy_access_token';
const REFRESH_KEY = 'whetzy_refresh_token';

let accessToken: string | null = readStorage(ACCESS_KEY);
let refreshToken: string | null = readStorage(REFRESH_KEY);

function readStorage(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function persistTokens(access: string | null, refresh: string | null) {
  accessToken = access;
  refreshToken = refresh;
  try {
    if (access) localStorage.setItem(ACCESS_KEY, access);
    else localStorage.removeItem(ACCESS_KEY);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
    else localStorage.removeItem(REFRESH_KEY);
  } catch {
    /* storage unavailable — tokens still held in memory */
  }
}

/** El token de acceso vigente, el mismo que usa este modulo (clave `whetzy_access_token`). */
export function getAccessToken(): string | null {
  return accessToken;
}

export function isAuthenticated(): boolean {
  return accessToken !== null;
}

export function logout() {
  persistTokens(null, null);
}

function getHeaders(): HeadersInit {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;
  return headers;
}

async function tryRefresh(): Promise<boolean> {
  if (!refreshToken) return false;
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = (await res.json()) as { access_token: string; refresh_token: string };
    persistTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

async function request<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { ...getHeaders(), ...options.headers },
  });

  if (res.status === 401 && retry && path !== '/auth/refresh') {
    if (await tryRefresh()) {
      return request<T>(path, options, false);
    }
    persistTokens(null, null);
    throw new ApiError('Unauthorized', 401);
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === 'string' ? body.detail : `HTTP ${res.status}`;
    throw new ApiError(detail, res.status);
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
  is_admin?: boolean;
}

export interface RegisterPayload {
  email: string;
  username: string;
  display_name: string;
  password: string;
  language: 'es' | 'en';
}

export type OAuthProvider = 'github' | 'google';

export const auth = {
  async register(payload: RegisterPayload) {
    const data = await request<{ access_token: string; refresh_token: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    persistTokens(data.access_token, data.refresh_token);
    return data;
  },

  async login(email: string, password: string) {
    // Backend uses OAuth2PasswordRequestForm → form-encoded, `username` field carries the email.
    const form = new URLSearchParams();
    form.set('username', email);
    form.set('password', password);
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(typeof body.detail === 'string' ? body.detail : 'Incorrect email or password');
    }
    const data = (await res.json()) as { access_token: string; refresh_token: string };
    persistTokens(data.access_token, data.refresh_token);
    return data;
  },

  async me() {
    return request<UserRead>('/auth/me');
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

export interface QuizStartResponse {
  session_id: string;
  mode: string;
  question: QuestionPublic | null;
  reviews_due: number;
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
  ) {
    return request<QuizAnswerResponse>('/quiz/answer', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        question_id: questionId,
        selected_index: selectedIndex,
        response_time_ms: responseTimeMs,
        declared_unknown: declaredUnknown,
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

export const league = {
  async current() {
    return request<LeagueStandingsResponse>('/league/current');
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
}

export interface MockExamSubmitResponse {
  attempt_id: string;
  status: string;
  expired: boolean;
  report: MockExamReport;
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
 *  El reparto es 70/30 tras la comisión de Paddle y la retención que fija
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


