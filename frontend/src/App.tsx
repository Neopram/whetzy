import { useEffect, useState } from 'react';
import i18n from './i18n';
import { useAppStore } from './stores/useAppStore';
import { isAuthenticated, logout } from './services/api';
import { TopBar } from './components/layout/TopBar';
import { BottomNav } from './components/layout/BottomNav';
import { HomeScreen } from './pages/HomeScreen';
import { QuizScreen } from './pages/QuizScreen';
import { StatsScreen } from './pages/StatsScreen';
import { LeagueScreen } from './pages/LeagueScreen';
import { ProfileScreen } from './pages/ProfileScreen';
import { PlacementScreen } from './pages/PlacementScreen';
import { TracksScreen } from './pages/TracksScreen';
import { DuelScreen } from './pages/DuelScreen';
import { AuthScreen } from './pages/AuthScreen';
import { DeleteAccountScreen } from './pages/DeleteAccountScreen';
import { LegalScreen } from './pages/LegalScreen';
import { OnboardingScreen } from './pages/OnboardingScreen';
import { LandingScreen } from './pages/LandingScreen';
import { Toast } from './components/common/Toast';
import './styles/global.css';

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
  if (path === '/delete-account') return <DeleteAccountScreen />;
  if (path === '/privacy') return <LegalScreen doc="privacy" />;
  if (path === '/terms') return <LegalScreen doc="terms" />;
  if (path === '/landing') return <LandingScreen />;

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
        <AuthScreen onAuthed={handleAuthed} />
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
        <OnboardingScreen onDone={() => setShowOnboarding(false)} />
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
        {renderScreen()}
      </main>
      {currentScreen !== 'quiz' && currentScreen !== 'placement' && <BottomNav />}
      <Toast />
    </>
  );
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
