import { useEffect, useState, lazy, Suspense, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import i18n from './i18n';
import { useAppStore } from './stores/useAppStore';
import { isAuthenticated, logout } from './services/api';
import { TopBar } from './components/layout/TopBar';
import { BottomNav } from './components/layout/BottomNav';
import { Toast } from './components/common/Toast';
import './styles/global.css';

// Every screen is loaded on demand. Statically importing them put the whole
// app — quiz, Pyodide, Lottie, duels — into the landing page's first bundle,
// which is the page most likely to be opened cold on a mid-range phone over
// 4G. Each entry below is its own chunk; a visitor downloads the one screen
// they are actually looking at.
const HomeScreen = lazy(() => import('./pages/HomeScreen').then((m) => ({ default: m.HomeScreen })));
const QuizScreen = lazy(() => import('./pages/QuizScreen').then((m) => ({ default: m.QuizScreen })));
const StatsScreen = lazy(() => import('./pages/StatsScreen').then((m) => ({ default: m.StatsScreen })));
const LeagueScreen = lazy(() => import('./pages/LeagueScreen').then((m) => ({ default: m.LeagueScreen })));
const ProfileScreen = lazy(() => import('./pages/ProfileScreen').then((m) => ({ default: m.ProfileScreen })));
const PlacementScreen = lazy(() => import('./pages/PlacementScreen').then((m) => ({ default: m.PlacementScreen })));
const TracksScreen = lazy(() => import('./pages/TracksScreen').then((m) => ({ default: m.TracksScreen })));
const DuelScreen = lazy(() => import('./pages/DuelScreen').then((m) => ({ default: m.DuelScreen })));
const AuthScreen = lazy(() => import('./pages/AuthScreen').then((m) => ({ default: m.AuthScreen })));
const DeleteAccountScreen = lazy(() =>
  import('./pages/DeleteAccountScreen').then((m) => ({ default: m.DeleteAccountScreen }))
);
const LegalScreen = lazy(() => import('./pages/LegalScreen').then((m) => ({ default: m.LegalScreen })));
const OnboardingScreen = lazy(() =>
  import('./pages/OnboardingScreen').then((m) => ({ default: m.OnboardingScreen }))
);
const LandingScreen = lazy(() => import('./pages/LandingScreen').then((m) => ({ default: m.LandingScreen })));
const MockExamScreen = lazy(() =>
  import('./pages/MockExamScreen').then((m) => ({ default: m.MockExamScreen }))
);
const LessonScreen = lazy(() =>
  import('./pages/LessonScreen').then((m) => ({ default: m.LessonScreen }))
);

// URL-based routing for standalone pages (no React Router needed)
const STANDALONE_DOC: Record<string, string> = {
  '/delete-account': 'deleteAccount',
  '/privacy': 'privacy',
  '/terms': 'terms',
  '/landing': 'landing',
};

type AuthState = 'checking' | 'unauthed' | 'authed';

/**
 * These pages used to be returned straight out of `App`, above the effect that
 * calls `i18n.changeLanguage`. That effect therefore never ran for them, so the
 * privacy policy, the terms, the deletion flow and the landing always rendered
 * in the fallback language whatever the user had chosen — and `<html lang>`
 * stayed wrong with it. Giving them their own component means the language is
 * applied before anything is painted.
 */
function StandalonePage({ path }: { path: string }) {
  const userLanguage = useAppStore((s) => s.user.language);
  const { t } = useTranslation();

  useEffect(() => {
    void i18n.changeLanguage(userLanguage);
    document.documentElement.lang = userLanguage;
  }, [userLanguage]);

  useEffect(() => {
    const doc = STANDALONE_DOC[path];
    if (doc) document.title = t(`docTitle.${doc}`);
  }, [path, t, userLanguage]);

  if (path === '/delete-account') return <Screen><DeleteAccountScreen /></Screen>;
  if (path === '/privacy') return <Screen><LegalScreen doc="privacy" /></Screen>;
  if (path === '/terms') return <Screen><LegalScreen doc="terms" /></Screen>;
  return <Screen><LandingScreen /></Screen>;
}

function needsOnboarding(userId: string): boolean {
  try {
    return !localStorage.getItem(`whetzy_onboarded_${userId}`);
  } catch {
    return false;
  }
}

function App() {
  // Standalone pages routed by URL path
  const path = window.location.pathname;
  if (path in STANDALONE_DOC) return <StandalonePage path={path} />;

  const currentScreen = useAppStore((s) => s.currentScreen);
  const setScreen = useAppStore((s) => s.setScreen);
  const mockExamTrackId = useAppStore((s) => s.mockExamTrackId);
  const mockExamQuestionCount = useAppStore((s) => s.mockExamQuestionCount);
  const mockExamDurationMinutes = useAppStore((s) => s.mockExamDurationMinutes);
  const lessonSkillId = useAppStore((s) => s.lessonSkillId);
  const startQuiz = useAppStore((s) => s.startQuiz);
  const hydrateFromApi = useAppStore((s) => s.hydrateFromApi);
  const userLanguage = useAppStore((s) => s.user.language);
  const userId = useAppStore((s) => s.user.id);

  useEffect(() => {
    void i18n.changeLanguage(userLanguage);
    document.documentElement.lang = userLanguage;
  }, [userLanguage]);
  const [authState, setAuthState] = useState<AuthState>(() =>
    isAuthenticated() ? 'checking' : 'unauthed'
  );
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    if (authState !== 'checking') return;
    hydrateFromApi()
      .then(() => {
        const userId = useAppStore.getState().user.id;
        setShowOnboarding(needsOnboarding(userId));
        setAuthState('authed');
      })
      .catch(() => {
        logout();
        setAuthState('unauthed');
      });
  }, [authState, hydrateFromApi]);

  // `signOut` (useAppStore) clears the stored tokens and resets the store, but
  // it has no way to reach this component's local `authState`, so without this
  // the app kept rendering the authenticated shell around a reset placeholder
  // user until the next reload. Watch the store's user instead: whenever it
  // changes while we believe we are authed, re-read the only real source of
  // truth — whether a token still exists — and fall back to the auth screen.
  useEffect(() => {
    if (authState === 'authed' && !isAuthenticated()) {
      setShowOnboarding(false);
      setAuthState('unauthed');
    }
  }, [userId, authState]);

  function handleAuthed() {
    setAuthState('checking');
  }

  if (authState === 'unauthed') {
    return (
      <>
        <Screen><AuthScreen onAuthed={handleAuthed} /></Screen>
        <Toast />
      </>
    );
  }

  if (authState === 'checking') {
    return <BootSplash />;
  }

  if (showOnboarding) {
    return (
      <>
        <Screen><OnboardingScreen onDone={() => setShowOnboarding(false)} /></Screen>
        <Toast />
      </>
    );
  }

  const renderScreen = () => {
    switch (currentScreen) {
      case 'home': return <HomeScreen />;
      case 'quiz': return <QuizScreen />;
      case 'tracks': return <TracksScreen />;
      case 'stats': return <StatsScreen />;
      case 'league': return <LeagueScreen />;
      case 'profile': return <ProfileScreen />;
      case 'placement': return <PlacementScreen />;
      case 'duels': return <DuelScreen />;
      case 'mockexam':
        return <MockExamScreen trackId={mockExamTrackId ?? 'track08'} questionCount={mockExamQuestionCount} durationMinutes={mockExamDurationMinutes} onExit={() => setScreen('tracks')} />;
      case 'lesson':
        return (
          <LessonScreen
            skillId={lessonSkillId ?? ''}
            onExit={() => setScreen('tracks')}
            onStartQuiz={() => {
              startQuiz('study', 10, { skillId: lessonSkillId ?? undefined });
              setScreen('quiz');
            }}
          />
        );
      default: return <HomeScreen />;
    }
  };

  const prevScreenRef = useRef(currentScreen);
  const dir = screenOrder(currentScreen) >= screenOrder(prevScreenRef.current) ? 1 : -1;
  useEffect(() => { prevScreenRef.current = currentScreen; }, [currentScreen]);

  return (
    <>
      <TopBar />
      <main className="app-content">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={currentScreen}
            initial={{ opacity: 0, x: dir * 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: dir * -20 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            style={{ height: '100%' }}
          >
            <Screen>{renderScreen()}</Screen>
          </motion.div>
        </AnimatePresence>
      </main>
      {currentScreen !== 'quiz' && currentScreen !== 'placement' && currentScreen !== 'mockexam' && currentScreen !== 'lesson' && <BottomNav />}
      <Toast />
    </>
  );
}

const SCREEN_ORDER: Record<string, number> = {
  home: 0, tracks: 1, stats: 2, league: 3, profile: 4,
  quiz: 5, placement: 6, duels: 7, mockexam: 8, lesson: 9,
};
function screenOrder(s: string) { return SCREEN_ORDER[s] ?? 0; }

/** Suspense boundary for a lazily loaded screen. */
function Screen({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<BootSplash />}>{children}</Suspense>;
}

function BootSplash() {
  return (
    <div style={{
      minHeight: '100dvh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column',
      gap: 16,
      background: 'var(--le-bg)',
    }}>
      <div style={{
        width: 64, height: 64, borderRadius: 20,
        background: 'linear-gradient(135deg, var(--le-brand-2), var(--le-brand-dark))',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#fff', fontWeight: 900, fontSize: 28,
        animation: 'pulse 1.2s ease-in-out infinite',
      }}>N</div>
      <span style={{ color: 'var(--le-text-muted)', fontWeight: 700, fontSize: 13 }}>Whetzy</span>
    </div>
  );
}

export default App;
