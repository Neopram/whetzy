// Same-origin by default: in dev, Vite proxies /api → backend (see vite.config.ts);
// in production set VITE_API_URL to the deployed backend origin + /api/v1.
const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

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
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === 'string' ? body.detail : `HTTP ${res.status}`;
    throw new Error(detail);
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
}

export interface RegisterPayload {
  email: string;
  username: string;
  display_name: string;
  password: string;
  language: 'es' | 'en';
}

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
};

export interface QuestionPublic {
  id: string;
  skill_id: string;
  type: 'mcq' | 'true_false' | 'code_output' | 'fill_blank' | 'fill_blank_exec' | 'fix_bug';
  difficulty_tier: 'easy' | 'medium' | 'hard' | 'expert';
  question_es: string;
  question_en: string;
  options_es: string[] | null;
  options_en: string[] | null;
  /** Expected stdout for exec types (fill_blank_exec, fix_bug). Used for client-side Pyodide grading. */
  correct_answer_es: string | null;
  correct_answer_en: string | null;
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

  async answer(sessionId: string, questionId: string, selectedIndex: number | null, responseTimeMs: number) {
    return request<QuizAnswerResponse>('/quiz/answer', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        question_id: questionId,
        selected_index: selectedIndex,
        response_time_ms: responseTimeMs,
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

export const progress = {
  async dashboard() {
    return request<DashboardResponse>('/progress/dashboard');
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

export const placement = {
  async start() {
    return request<{ session_id: string; question: unknown; total_questions: number }>('/placement/start', {
      method: 'POST',
    });
  },

  async answer(sessionId: string, questionId: string, answerIndex: number) {
    return request<{ correct: boolean; next_question: unknown | null; progress: number }>(
      '/placement/answer',
      {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId, question_id: questionId, answer_index: answerIndex }),
      }
    );
  },

  async result(sessionId: string) {
    return request<{ ability: number; level: string; skip_modules: string[] }>(`/placement/${sessionId}/result`);
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
  async result(duelId: string) {
    return request<DuelResultResponse>(`/duels/${duelId}/result`);
  },
};
