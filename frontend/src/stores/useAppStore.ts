import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { auth, logout as apiLogout, type UserRead } from '../services/api';

type Language = 'es' | 'en';
type Screen = 'home' | 'quiz' | 'stats' | 'league' | 'profile' | 'placement' | 'tracks' | 'duels' | 'mockexam' | 'lesson';
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
  isPremium: boolean;
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
  answerQuestion: (correct: boolean, xp: number) => void;
  nextQuestion: () => void;
  resetQuiz: () => void;

  // Mock exam
  mockExamTrackId: string | null;
  mockExamQuestionCount: number;
  mockExamDurationMinutes: number;
  startMockExam: (trackId: string, questionCount?: number, durationMinutes?: number) => void;

  // Lesson
  lessonSkillId: string | null;
  startLesson: (skillId: string) => void;

  // Missions
  missions: Mission[];
  updateMission: (id: string, progress: number) => void;

  // Settings
  language: Language;
  setLanguage: (lang: Language) => void;
  soundEnabled: boolean;
  toggleSound: () => void;
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
    isPremium: u.is_premium,
    language: u.language,
    league: 'bronze',
  };
}

const defaultUser: UserProfile = {
  id: 'demo-user',
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
        set({ user: mapApiUser(apiUser) });
      },
      signOut: () => {
        apiLogout();
        set({ user: defaultUser, currentScreen: 'home' });
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
      startQuiz: (mode, totalQuestions, opts) =>
        set({
          quiz: {
            ...defaultQuiz,
            mode,
            totalQuestions,
            trackId: opts?.trackId ?? null,
            skillId: opts?.skillId ?? null,
          },
          currentScreen: 'quiz',
        }),
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

      lessonSkillId: null,
      startLesson: (skillId) =>
        set((s) => ({ lessonSkillId: skillId, previousScreen: s.currentScreen, currentScreen: 'lesson' })),

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
      hapticEnabled: true,
      toggleHaptic: () => set((s) => ({ hapticEnabled: !s.hapticEnabled })),
    }),
    {
      name: 'learning-engine-store',
      partialize: (state) => ({
        user: state.user,
        language: state.language,
        soundEnabled: state.soundEnabled,
        hapticEnabled: state.hapticEnabled,
        missions: state.missions,
      }),
    }
  )
);
