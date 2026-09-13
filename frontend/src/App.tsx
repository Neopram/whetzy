import { useEffect, useState, lazy, Suspense } from 'react';
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

// URL-based routing for standalone pages (no React Router needed)
const _path = window.location.pathname;
if (_path === '/delete-account') document.title = 'Eliminar cuenta — Whetzy';
if (_path === '/privacy') document.title = 'Privacidad — Whetzy';
if (_path === '/terms') document.title = 'Términos — Whetzy';
if (_path === '/landing') document.title = 'Whetzy — Aprende lo que importa';

type AuthState = 'checking' | 'unauthed' | 'authed';

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
  if (path === '/delete-account') return <Screen><DeleteAccountScreen /></Screen>;
  if (path === '/privacy') return <Screen><LegalScreen doc="privacy" /></Screen>;
  if (path === '/terms') return <Screen><LegalScreen doc="terms" /></Screen>;
  if (path === '/landing') return <Screen><LandingScreen /></Screen>;

  const currentScreen = useAppStore((s) => s.currentScreen);
  const hydrateFromApi = useAppStore((s) => s.hydrateFromApi);
  const userLanguage = useAppStore((s) => s.user.language);

  useEffect(() => {
    void i18n.changeLanguage(userLanguage);
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
      default: return <HomeScreen />;
    }
  };

  return (
    <>
      <TopBar />
      <main className="app-content">
        <Screen>{renderScreen()}</Screen>
      </main>
      {currentScreen !== 'quiz' && currentScreen !== 'placement' && <BottomNav />}
      <Toast />
    </>
  );
}

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
