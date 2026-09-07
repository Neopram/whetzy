import { useEffect, useState } from 'react';
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
import { AuthScreen } from './pages/AuthScreen';
import { Toast } from './components/common/Toast';
import './styles/global.css';

type AuthState = 'checking' | 'unauthed' | 'authed';

function App() {
  const currentScreen = useAppStore((s) => s.currentScreen);
  const hydrateFromApi = useAppStore((s) => s.hydrateFromApi);
  const [authState, setAuthState] = useState<AuthState>(() =>
    isAuthenticated() ? 'checking' : 'unauthed'
  );

  useEffect(() => {
    if (authState !== 'checking') return;
    hydrateFromApi()
      .then(() => setAuthState('authed'))
      .catch(() => {
        logout();
        setAuthState('unauthed');
      });
  }, [authState, hydrateFromApi]);

  async function handleAuthed() {
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

  const renderScreen = () => {
    switch (currentScreen) {
      case 'home': return <HomeScreen />;
      case 'quiz': return <QuizScreen />;
      case 'tracks': return <TracksScreen />;
      case 'stats': return <StatsScreen />;
      case 'league': return <LeagueScreen />;
      case 'profile': return <ProfileScreen />;
      case 'placement': return <PlacementScreen />;
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
