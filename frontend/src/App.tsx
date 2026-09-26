import { useEffect, useState, lazy, Suspense, useRef } from 'react';
import { AnimatePresence, motion, MotionConfig } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import i18n from './i18n';
import { useAppStore } from './stores/useAppStore';
import { ApiError, isAuthenticated, logout } from './services/api';
import { TopBar } from './components/layout/TopBar';
import { BottomNav } from './components/layout/BottomNav';
import { Toast } from './components/common/Toast';
import './styles/global.css';
import { OfflineIndicator } from './components/common/OfflineIndicator';
import { useGestures } from './hooks/useGestures';

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
  import('./pages/OnboardingScreen')
);
const LandingScreen = lazy(() => import('./pages/LandingScreen'));
const TrackExamScreen = lazy(() =>
  import('./pages/TrackExamScreen').then((m) => ({ default: m.TrackExamScreen }))
);
// Lazy like the other standalone pages: a visitor checking somebody else's
// certificate should not download the quiz engine to read one card.
const CertificateScreen = lazy(() =>
  import('./pages/CertificateScreen').then((m) => ({ default: m.CertificateScreen }))
);
const PublicProfileScreen = lazy(() =>
  import('./pages/PublicProfileScreen').then((m) => ({ default: m.default }))
);
const MockExamScreen = lazy(() =>
  import('./pages/MockExamScreen').then((m) => ({ default: m.MockExamScreen }))
);
const LessonScreen = lazy(() =>
  import('./pages/LessonScreen').then((m) => ({ default: m.LessonScreen }))
);
const EvidenceScreen = lazy(() =>
  import('./pages/EvidenceScreen').then((m) => ({ default: m.EvidenceScreen }))
);
const ReadinessScreen = lazy(() =>
  import('./pages/ReadinessScreen').then((m) => ({ default: m.ReadinessScreen }))
);
const AdminScreen = lazy(() => import('./pages/AdminScreen').then((m) => ({ default: m.AdminScreen })));
const InstructorScreen = lazy(() => import('./pages/InstructorScreen'));
const MarketplaceScreen = lazy(() => import('./pages/MarketplaceScreen').then((m) => ({ default: m.MarketplaceScreen })));
const WalletScreen = lazy(() => import('./pages/WalletScreen'));
const PlaygroundScreen = lazy(() =>
  import('./pages/PlaygroundScreen').then((m) => ({ default: m.PlaygroundScreen }))
);
// Public, unauthenticated status page — checked before any auth machinery so
// it stays reachable even when the backend is down.
const StatusPage = lazy(() => import('./pages/StatusPage'));

// URL-based routing for standalone pages (no React Router needed)
const STANDALONE_DOC: Record<string, string> = {
  '/delete-account': 'deleteAccount',
  '/privacy': 'privacy',
  '/terms': 'terms',
  '/landing': 'landing',
  '/evidence': 'evidence',
};

type AuthState = 'checking' | 'retrying' | 'unauthed' | 'authed';

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
  if (path === '/evidence') return <Screen><EvidenceScreen /></Screen>;
  if (path === '/landing') return <Screen><LandingScreen /></Screen>;

  if (path === '/admin') {
    return (
      <Screen>
        <Suspense fallback={<BootSplash />}>
          <AdminScreen />
        </Suspense>
      </Screen>
    );
  }

  return <Screen><LandingScreen /></Screen>;
}

/** `/certificate/<code>` — the public verification page (17.2).
 *
 *  Separate from `STANDALONE_DOC` because it is a prefix route rather than an
 *  exact path, and separate from `StandalonePage` because it takes the code out
 *  of the URL. It is standalone for the same reason the legal pages are: it has
 *  to render for a visitor with no account and no session.
 */
const CERTIFICATE_PATH = '/certificate/';

function StandaloneCertificate({ code }: { code: string }) {
  const userLanguage = useAppStore((s) => s.user.language);

  useEffect(() => {
    void i18n.changeLanguage(userLanguage);
    document.documentElement.lang = userLanguage;
  }, [userLanguage]);

  return <Screen><CertificateScreen code={code} /></Screen>;
}

function needsOnboarding(userId: string): boolean {
  try {
    return !localStorage.getItem(`whetzy_onboarded_${userId}`);
  } catch {
    return false;
  }
}

function normalizePath(pathname: string): string {
  if (pathname.endsWith('/') && pathname !== '/') return pathname.slice(0, -1);
  return pathname;
}

function AuthRoute() {
  return (
    <>
      <Screen>
        <AuthScreen onAuthed={() => { window.location.assign('/'); }} />
      </Screen>
      <Toast />
    </>
  );
}

function App() {
  // Standalone pages routed by URL path
  const path = normalizePath(window.location.pathname);
  // Public marketing + auth sit above every hook: a visitor on /landing must
  // never enter the session machine, and Cloudflare's 308 to /landing/ used
  // to miss the exact-match and hydrate the register form instead.
  if (path === '/landing') return <Screen><LandingScreen /></Screen>;

  if (path === '/admin') {
    return (
      <Screen>
        <Suspense fallback={<BootSplash />}>
          <AdminScreen />
        </Suspense>
      </Screen>
    );
  }

  // Public status page: no auth, no store, reachable even if the backend
  // that the rest of the app depends on is the very thing that's down.
  if (path === '/status') return <Screen><StatusPage /></Screen>;

  if (path.startsWith('/r/')) {
    const code = path.slice(3);
    if (code) {
      try { localStorage.setItem('whetzy_ref', code); } catch { /* private mode */ }
      const lang = navigator.language?.startsWith('es') ? 'es' : 'en';
      i18n.changeLanguage(lang);
    }
    window.location.assign('/register');
    return null;
  }

  if (path === '/auth' || path === '/login' || path === '/register') return <AuthRoute />;
  if (path in STANDALONE_DOC) return <StandalonePage path={path} />;
  // Both returns sit above every hook in this component, which is the only
  // arrangement React allows: an early return *between* hooks is what blanked
  // the screen for every signed-in user in 16.8.
  if (path.startsWith(CERTIFICATE_PATH)) {
    return <StandaloneCertificate code={path.slice(CERTIFICATE_PATH.length)} />;
  }
  if (path.startsWith('/verify/')) {
    return <StandaloneCertificate code={path.slice(8)} />;
  }
  if (path.startsWith('/u/')) {
    return <Screen><PublicProfileScreen handle={path.slice(3)} /></Screen>;
  }

  const currentScreen = useAppStore((s) => s.currentScreen);
  const placementTrackId = useAppStore((s) => s.placementTrackId);
  const setScreen = useAppStore((s) => s.setScreen);
  const mockExamTrackId = useAppStore((s) => s.mockExamTrackId);
  const mockExamQuestionCount = useAppStore((s) => s.mockExamQuestionCount);
  const mockExamDurationMinutes = useAppStore((s) => s.mockExamDurationMinutes);
  const trackExamKind = useAppStore((s) => s.trackExamKind);
  const trackExamTargetId = useAppStore((s) => s.trackExamTargetId);
  const trackExamQuestionCount = useAppStore((s) => s.trackExamQuestionCount);
  const trackExamDurationMinutes = useAppStore((s) => s.trackExamDurationMinutes);
  const trackExamPassPct = useAppStore((s) => s.trackExamPassPct);
  const lessonSkillId = useAppStore((s) => s.lessonSkillId);
  const readinessTrackId = useAppStore((s) => s.readinessTrackId);
  const startQuiz = useAppStore((s) => s.startQuiz);
  const hydrateFromApi = useAppStore((s) => s.hydrateFromApi);
  const userLanguage = useAppStore((s) => s.user.language);
  const userId = useAppStore((s) => s.user.id);

  useEffect(() => {
    void i18n.changeLanguage(userLanguage);
    document.documentElement.lang = userLanguage;
  }, [userLanguage]);

  // Tracks the previous screen so the transition below knows which way to
  // slide. These two hooks must stay ABOVE the early returns for `unauthed` /
  // `checking` / `showOnboarding`: they used to sit next to the markup that
  // consumes them, which meant the authenticated render called two more hooks
  // than the unauthenticated one. React aborts that render with "Rendered more
  // hooks than during the previous render", so the whole tree blanked the
  // moment anyone signed in and the bottom nav never appeared.
  const prevScreenRef = useRef(currentScreen);
  useEffect(() => { prevScreenRef.current = currentScreen; }, [currentScreen]);

  useGestures({
    onSwipeRight: () => { if (currentScreen !== 'home') setScreen('home'); },
    onSwipeLeft: () => { if (currentScreen !== 'marketplace') setScreen('marketplace'); },
  });

  const [authState, setAuthState] = useState<AuthState>(() =>
    isAuthenticated() ? 'checking' : 'unauthed'
  );
  const [showOnboarding, setShowOnboarding] = useState(false);
  const reintentos = useRef(0);

  useEffect(() => {
    if (authState !== 'checking') return;
    hydrateFromApi()
      .then(() => {
        const userId = useAppStore.getState().user.id;
        setShowOnboarding(needsOnboarding(userId));
        setAuthState('authed');
      })
      .catch((err: unknown) => {
        // Un 401 significa que el token ya no vale: ahí sí hay que salir. Un
        // fallo de red o un 5xx significa que el servidor no está, y tirar el
        // refresh token por eso obliga a volver a entrar por algo que se
        // arregla solo en treinta segundos.
        const transitorio = err instanceof ApiError && err.esTransitorio;
        if (transitorio && reintentos.current < 3) {
          reintentos.current += 1;
          setTimeout(() => setAuthState('checking'), 1500 * reintentos.current);
          setAuthState('retrying');
          return;
        }
        if (!transitorio) logout();
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

  function finishOnboarding() {
    try {
      localStorage.setItem(`whetzy_onboarded_${userId}`, '1');
    } catch {
      // Modo privado o almacenamiento bloqueado: se sigue adelante. Volver a
      // ver el onboarding molesta; quedarse encallado en el, no se puede.
    }
    setShowOnboarding(false);
  }

  function handleAuthed() {
    setAuthState('checking');
  }

  if (authState === 'unauthed') {
    const oauthError = new URLSearchParams(window.location.search).get('oauth_error');
    // `/` is the public home. Login/register live at `/auth` so the marketing
    // page is what an anonymous visitor actually sees. OAuth error returns
    // still land on `/` with a query flag and must show the form.
    if (path === '/' && !oauthError) {
      return <Screen><LandingScreen /></Screen>;
    }
    return (
      <>
        <Screen><AuthScreen onAuthed={handleAuthed} /></Screen>
        <Toast />
      </>
    );
  }

  if (authState === 'checking' || authState === 'retrying') {
    return <BootSplash />;
  }

  if (showOnboarding) {
    return (
      <>
        <Screen><OnboardingScreen onDone={finishOnboarding} /></Screen>
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
      case 'placement':
        // El motor CAT es por ruta: sin `track_id` no hay pool que elegir.
        if (!placementTrackId) return <HomeScreen />;
        return <PlacementScreen trackId={placementTrackId} />;
      case 'duels': return <DuelScreen />;
      case 'mockexam':
        if (!mockExamTrackId) return null;
        return <MockExamScreen trackId={mockExamTrackId} questionCount={mockExamQuestionCount} durationMinutes={mockExamDurationMinutes} onExit={() => setScreen('tracks')} />;
      case 'trackexam':
        // Without a target there is nothing to sit; bouncing to the catalogue
        // beats rendering an exam screen that can only fail on start.
        return trackExamTargetId ? (
          <TrackExamScreen
            kind={trackExamKind}
            targetId={trackExamTargetId}
            questionCount={trackExamQuestionCount}
            durationMinutes={trackExamDurationMinutes}
            passPct={trackExamPassPct}
            onExit={() => setScreen('tracks')}
          />
        ) : (
          <TracksScreen />
        );
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
      case 'readiness':
        return readinessTrackId ? (
          <ReadinessScreen trackId={readinessTrackId} onExit={() => setScreen('tracks')} />
        ) : (
          <TracksScreen />
        );
      case 'admin': return <AdminScreen />;
      case 'instructor': return <InstructorScreen />;
      case 'marketplace': return <MarketplaceScreen />;
      case 'wallet': return <WalletScreen />;
      case 'playground': return <PlaygroundScreen />;
      default: return <HomeScreen />;
    }
  };

  const dir = screenOrder(currentScreen) >= screenOrder(prevScreenRef.current) ? 1 : -1;

  return (
    // `reducedMotion="user"` es lo unico que hace que framer-motion respete
    // prefers-reduced-motion. El bloque de global.css solo apaga animaciones y
    // transiciones CSS; framer escribe transforms en linea desde JS, asi que
    // sin esto los `repeat: Infinity` de lib/motion.ts (pulso del nodo actual,
    // parpadeo de la racha) siguen moviendose para quien pidio que no.
    <MotionConfig reducedMotion="user">
      <TopBar />
      <main className="app-content">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={currentScreen}
            initial={{ opacity: 0, x: dir * 24, scale: 0.985 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: dir * -16, scale: 0.99 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
            style={{ height: '100%' }}
          >
            <Screen>{renderScreen()}</Screen>
          </motion.div>
        </AnimatePresence>
      </main>
      {!IMMERSIVE_SCREENS.has(currentScreen) && <BottomNav />}
      <Toast />
      <OfflineIndicator />
    </MotionConfig>
  );
}

/** Screens that hide the bottom nav: one task, one way out, no wandering off
 *  mid-exam. It is a set rather than a chain of `!==` so adding a screen is one
 *  entry instead of one more clause nobody remembers to extend — 'trackexam'
 *  was the fifth, and the chain was already four deep. */
const IMMERSIVE_SCREENS = new Set(['quiz', 'placement', 'mockexam', 'trackexam', 'lesson', 'readiness', 'playground']);

const SCREEN_ORDER: Record<string, number> = {
  home: 0, tracks: 1, stats: 2, league: 3, profile: 4, marketplace: 14,
  quiz: 5, placement: 6, duels: 7, mockexam: 8, lesson: 9, trackexam: 10, readiness: 11, admin: 12, instructor: 13, playground: 15,
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




