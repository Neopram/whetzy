import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { auth, logout as apiLogout, type UserRead } from '../services/api';

type Language = 'es' | 'en';
export type Screen = 'home' | 'quiz' | 'stats' | 'league' | 'profile' | 'placement' | 'tracks' | 'duels' | 'mockexam' | 'lesson' | 'trackexam' | 'readiness' | 'admin' | 'instructor' | 'marketplace' | 'wallet' | 'playground' | 'projects';
type LeagueTier = 'bronze' | 'silver' | 'gold' | 'platinum' | 'diamond';

interface UserProfile {
  id: string;
  username: string;
  displayName: string;
  avatarEmoji: string;
  email: string;
  level: number;
  totalXp: number;
  xpToNextLevel: number;
  currentStreak: number;
  maxStreak: number;
  streakFreezeAvailable: number;
  lastActive: string;
  /** Desbloquea funciones: plan de pago o plan ganado con referidos. El
   *  checkout no lo usa: pregunta a `/auth/me` por el de pago. */
  isPremium: boolean;
  /** Plan ganado con referidos y hasta cuándo (ADR-57); null si no hay. */
  grantedTier: 'plus' | 'pro' | null;
  grantedUntil: string | null;
  /** Recibir correos de ofertas (la baja se hace desde Ajustes o desde el correo). */
  marketingEmails: boolean;
  /** «Instructor» en Perfil: solo creadores (plan Creador, dueño o admin). */
  canCreateCourses: boolean;
  /** «Admin» en Perfil: solo el dueño. `/auth/me` no mandaba `is_admin`, así
   *  que el enlace no se veía nunca (auditoría de pantallas, 2026-10-16). */
  isOwner: boolean;
  /** 43.3 (D2): el servidor guarda que terminó el onboarding (`onboarding_completed_at`). */
  onboardingCompleted: boolean;
  /** 43.3 (D2): horas por semana (0 <3 h, 1 3-10 h, 2 >10 h); se elige en Perfil. */
  weeklyTime: number | null;
  language: Language;
  league: LeagueTier;
}

interface QuizState {
  currentQuestion: number;
  totalQuestions: number;
  score: number;
  combo: number;
  maxCombo: number;
  xpEarned: number;
  answered: boolean;
  timerValue: number;
  mode: 'study' | 'review' | 'placement' | 'exam';
  recentAccuracy: boolean[];
  trackId: string | null;
  skillId: string | null;
}

interface Mission {
  id: string;
  type: string;
  targetValue: number;
  progress: number;
  xpReward: number;
  completed: boolean;
}

interface AppState {
  // Navigation
  currentScreen: Screen;
  previousScreen: Screen;
  setScreen: (screen: Screen) => void;

  // User
  user: UserProfile;
  updateUser: (updates: Partial<UserProfile>) => void;
  addXp: (amount: number) => void;
  hydrateFromApi: () => Promise<void>;
  signOut: () => void;

  // Quiz
  quiz: QuizState;
  startQuiz: (mode: QuizState['mode'], totalQuestions: number, opts?: { trackId?: string; skillId?: string }) => void;
  /** Sube con cada startQuiz: la pantalla se monta de nuevo aunque ya estés en
   *  'quiz' (p. ej. «Otra sesión» desde el resumen), en vez de quedarse en él. */
  quizRun: number;
  answerQuestion: (correct: boolean, xp: number) => void;
  nextQuestion: () => void;
  resetQuiz: () => void;

  // Mock exam
  mockExamTrackId: string | null;
  mockExamQuestionCount: number;
  mockExamDurationMinutes: number;
  startMockExam: (trackId: string, questionCount?: number, durationMinutes?: number) => void;

  // Track final exam / module test-out (17.2). One slice for both: they are the
  // same sitting with a different blueprint, and `trackExamKind` is what the
  // screen switches on.
  trackExamKind: 'track_final' | 'test_out';
  trackExamTargetId: string | null;
  trackExamQuestionCount: number;
  trackExamDurationMinutes: number;
  trackExamPassPct: number;
  startTrackExam: (
    kind: 'track_final' | 'test_out',
    targetId: string,
    blueprint: { questions: number; durationMinutes: number; passPct: number },
  ) => void;

  // Lesson
  lessonSkillId: string | null;
  startLesson: (skillId: string) => void;

  // Certification readiness (18.1)
  readinessTrackId: string | null;
  startReadiness: (trackId: string) => void;
  /** Track sobre el que corre la prueba de nivel; el motor CAT es por track. */
  placementTrackId: string | null;
  startPlacement: (trackId: string) => void;
  /** Ruta abierta en «Rutas». Vive aquí y no en la pantalla: al volver de un
   *  simulacro o de una lección, la pantalla se monta de nuevo y antes caía
   *  siempre en track01, aunque vinieras de AWS. */
  selectedTrackId: string;
  /** 43.4 (ADR-65 D5): la ruta activa, la de `target_track_id` en el servidor.
   *  Distinta de `selectedTrackId`, que es la que se está mirando en Rutas:
   *  abrir una ruta para verla no la hace tuya. null hasta que se elige. */
  activeTrackId: string | null;
  /** Hace de `trackId` la ruta activa y la guarda en el servidor. */
  setActiveTrack: (trackId: string) => void;
  /** Abre Rutas en el catálogo (para cambiar de ruta), no en el detalle. */
  browseTracks: () => void;
  tracksBrowse: boolean;
  /** 43.6 (ADR-65 D8): Proyectos abierto desde el detalle de una ruta enseña
   *  solo los de esa ruta; desde Hoy, todos (null). */
  projectsTrackId: string | null;
  openProjects: (trackId: string | null) => void;
  /** 43.7 (ADR-65 D9): ejemplo con el que se abre el playground desde una
   *  lección; null desde Rutas (playground libre). */
  playgroundSeed: { runtime: 'python' | 'sql' | 'js'; code: string; skillId: string } | null;
  openPlayground: (seed: { runtime: 'python' | 'sql' | 'js'; code: string; skillId: string } | null) => void;
  /** 43.7: paso de la lección desde el que se abrió el playground, para volver a él. */
  lessonReturn: { skillId: string; step: number } | null;
  openTrack: (trackId: string) => void;

  // Missions
  missions: Mission[];
  updateMission: (id: string, progress: number) => void;

  // Settings
  language: Language;
  setLanguage: (lang: Language) => void;
  soundEnabled: boolean;
  toggleSound: () => void;
  /** Mostrar el «¿Por qué?» del tutor IA (Ajustes). Solo afecta a este dispositivo. */
  aiExplanations: boolean;
  toggleAiExplanations: () => void;
  hapticEnabled: boolean;
  toggleHaptic: () => void;
}

function xpForNextLevel(level: number): number {
  return Math.round(1000 * Math.pow(1.15, Math.max(0, level - 1)));
}

function mapApiUser(u: UserRead): UserProfile {
  return {
    id: u.id,
    username: u.username,
    displayName: u.display_name,
    avatarEmoji: u.avatar_emoji || '🧠',
    email: u.email,
    level: u.level,
    totalXp: u.total_xp,
    xpToNextLevel: xpForNextLevel(u.level),
    currentStreak: u.current_streak,
    maxStreak: u.max_streak,
    streakFreezeAvailable: u.streak_freeze_available,
    lastActive: u.last_active ?? new Date().toISOString(),
    isPremium: u.is_premium || Boolean(u.granted_tier),
    grantedTier: u.granted_tier ?? null,
    grantedUntil: u.granted_tier_expires_at ?? null,
    marketingEmails: !u.marketing_emails_opt_out,
    canCreateCourses: u.can_create_courses ?? false,
    isOwner: u.is_owner ?? false,
    onboardingCompleted: Boolean(u.onboarding_completed_at),
    weeklyTime: u.onboarding_weekly_time ?? null,
    language: u.language,
    league: 'bronze',
  };
}

/** El id del perfil de muestra antes de hidratar contra `/auth/me` y después
 *  de `signOut()`. `App.tsx` lo usa para saber que la sesión real terminó,
 *  en vez de la cookie `whetzy_logged_in` (invisible entre dominios en
 *  producción — 30.9). */
export const DEFAULT_USER_ID = 'demo-user';

const defaultUser: UserProfile = {
  id: DEFAULT_USER_ID,
  username: 'federico',
  displayName: 'Federico G.',
  avatarEmoji: '🧠',
  email: '',
  level: 12,
  totalXp: 4320,
  xpToNextLevel: 6600,
  currentStreak: 14,
  maxStreak: 23,
  streakFreezeAvailable: 1,
  lastActive: new Date().toISOString(),
  isPremium: false,
  grantedTier: null,
  grantedUntil: null,
  marketingEmails: true,
  canCreateCourses: false,
  isOwner: false,
  onboardingCompleted: false,
  weeklyTime: null,
  language: 'es',
  league: 'gold',
};

const defaultQuiz: QuizState = {
  currentQuestion: 0,
  totalQuestions: 10,
  score: 0,
  combo: 0,
  maxCombo: 0,
  xpEarned: 0,
  answered: false,
  timerValue: 30,
  mode: 'study',
  recentAccuracy: [],
  trackId: null,
  skillId: null,
};

const defaultMissions: Mission[] = [
  { id: 'm1', type: 'answer_questions', targetValue: 10, progress: 7, xpReward: 30, completed: false },
  { id: 'm2', type: 'get_combo', targetValue: 5, progress: 5, xpReward: 20, completed: true },
  { id: 'm3', type: 'review_due', targetValue: 3, progress: 1, xpReward: 20, completed: false },
];

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      currentScreen: 'home',
      previousScreen: 'home',
      setScreen: (screen) =>
        set((s) => ({ previousScreen: s.currentScreen, currentScreen: screen })),

      user: defaultUser,
      updateUser: (updates) =>
        set((s) => ({ user: { ...s.user, ...updates } })),
      hydrateFromApi: async () => {
        const apiUser = await auth.me();
        // D-20: la ruta elegida vive en el servidor; el localStorage solo la recuerda.
        set(apiUser.target_track_id
          ? { user: mapApiUser(apiUser), selectedTrackId: apiUser.target_track_id, activeTrackId: apiUser.target_track_id }
          : { user: mapApiUser(apiUser), activeTrackId: null });
      },
      signOut: () => {
        apiLogout();
        set({ user: defaultUser, currentScreen: 'home', activeTrackId: null });
      },
      addXp: (amount) =>
        set((s) => {
          const newXp = s.user.totalXp + amount;
          let level = s.user.level;
          let xpToNext = s.user.xpToNextLevel;
          if (newXp >= xpToNext) {
            level += 1;
            xpToNext = Math.round(xpToNext * 1.15);
          }
          return {
            user: { ...s.user, totalXp: newXp, level, xpToNextLevel: xpToNext },
          };
        }),

      quiz: defaultQuiz,
      quizRun: 0,
      startQuiz: (mode, totalQuestions, opts) =>
        set((s) => ({
          quizRun: s.quizRun + 1,
          quiz: {
            ...defaultQuiz,
            mode,
            totalQuestions,
            trackId: opts?.trackId ?? null,
            skillId: opts?.skillId ?? null,
          },
          currentScreen: 'quiz',
        })),
      answerQuestion: (correct, xp) =>
        set((s) => ({
          quiz: {
            ...s.quiz,
            answered: true,
            score: correct ? s.quiz.score + 1 : s.quiz.score,
            combo: correct ? s.quiz.combo + 1 : 0,
            maxCombo: correct
              ? Math.max(s.quiz.maxCombo, s.quiz.combo + 1)
              : s.quiz.maxCombo,
            xpEarned: s.quiz.xpEarned + xp,
            recentAccuracy: [...s.quiz.recentAccuracy, correct],
          },
        })),
      nextQuestion: () =>
        set((s) => ({
          quiz: {
            ...s.quiz,
            currentQuestion: s.quiz.currentQuestion + 1,
            answered: false,
            timerValue: 30,
          },
        })),
      resetQuiz: () => set({ quiz: defaultQuiz }),

      mockExamTrackId: null,
      mockExamQuestionCount: 65,
      mockExamDurationMinutes: 90,
      startMockExam: (trackId, questionCount = 65, durationMinutes = 90) =>
        set((s) => ({ mockExamTrackId: trackId, mockExamQuestionCount: questionCount, mockExamDurationMinutes: durationMinutes, previousScreen: s.currentScreen, currentScreen: 'mockexam' })),

      trackExamKind: 'track_final',
      trackExamTargetId: null,
      // Defaults match the service's floors (MIN_TRACK_EXAM_QUESTIONS = 20 at
      // 90 s each, DEFAULT_PASS_PCT = 70) so a first paint before the blueprint
      // arrives shows plausible figures rather than zeros. The server is the
      // authority once the sitting starts.
      trackExamQuestionCount: 20,
      trackExamDurationMinutes: 30,
      trackExamPassPct: 70,
      startTrackExam: (kind, targetId, blueprint) =>
        set((s) => ({
          trackExamKind: kind,
          trackExamTargetId: targetId,
          trackExamQuestionCount: blueprint.questions,
          trackExamDurationMinutes: blueprint.durationMinutes,
          trackExamPassPct: blueprint.passPct,
          previousScreen: s.currentScreen,
          currentScreen: 'trackexam',
        })),

      lessonSkillId: null,
      startLesson: (skillId) =>
        set((s) => ({ lessonSkillId: skillId, previousScreen: s.currentScreen, currentScreen: 'lesson' })),

      readinessTrackId: null,
      startReadiness: (trackId) =>
        set((s) => ({ readinessTrackId: trackId, previousScreen: s.currentScreen, currentScreen: 'readiness' })),

      placementTrackId: null,
      startPlacement: (trackId) =>
        set((s) => ({ placementTrackId: trackId, previousScreen: s.currentScreen, currentScreen: 'placement' })),

      selectedTrackId: 'track01',
      activeTrackId: null,
      tracksBrowse: false,
      projectsTrackId: null,
      playgroundSeed: null,
      lessonReturn: null,
      openPlayground: (seed) =>
        set((s) => ({ playgroundSeed: seed, previousScreen: s.currentScreen, currentScreen: 'playground' })),
      openProjects: (trackId) =>
        set((s) => ({ projectsTrackId: trackId, previousScreen: s.currentScreen, currentScreen: 'projects' })),
      browseTracks: () =>
        set((s) => ({ tracksBrowse: true, previousScreen: s.currentScreen, currentScreen: 'tracks' })),
      setActiveTrack: (trackId) => {
        set({ activeTrackId: trackId, selectedTrackId: trackId });
        // Nunca se borra progreso al cambiar: todo vive por skill y por track.
        void auth.updateMe({ target_track_id: trackId }).catch(() => { /* sin red: vale en este dispositivo */ });
      },
      openTrack: (trackId) =>
        set((s) => ({ selectedTrackId: trackId, previousScreen: s.currentScreen, currentScreen: 'tracks' })),

      missions: defaultMissions,
      updateMission: (id, progress) =>
        set((s) => ({
          missions: s.missions.map((m) =>
            m.id === id
              ? { ...m, progress, completed: progress >= m.targetValue }
              : m
          ),
        })),

      language: 'es',
      setLanguage: (lang) => set({ language: lang }),
      soundEnabled: true,
      toggleSound: () => set((s) => ({ soundEnabled: !s.soundEnabled })),
      aiExplanations: true,
      toggleAiExplanations: () => set((s) => ({ aiExplanations: !s.aiExplanations })),
      hapticEnabled: true,
      toggleHaptic: () => set((s) => ({ hapticEnabled: !s.hapticEnabled })),
    }),
    {
      name: 'learning-engine-store',
      partialize: (state) => ({
        user: state.user,
        language: state.language,
        soundEnabled: state.soundEnabled,
        aiExplanations: state.aiExplanations,
        hapticEnabled: state.hapticEnabled,
        missions: state.missions,
        selectedTrackId: state.selectedTrackId,
        activeTrackId: state.activeTrackId,
      }),
    }
  )
);
