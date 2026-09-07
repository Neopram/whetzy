import { useAppStore } from '../../stores/useAppStore';
import styles from './BottomNav.module.css';

const NAV_ITEMS = [
  {
    id: 'duels' as const,
    label: 'Duelos',
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" width="26" height="26">
        <path d="M6.5 2h11L21 6l-9 16L3 6l3.5-4zm1.25 2L5 7.5l7 12.5 7-12.5L16.25 4H7.75zm4.75 2a2 2 0 1 1 0 4 2 2 0 0 1 0-4z"/>
      </svg>
    ),
  },
  {
    id: 'home' as const,
    label: 'Inicio',
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" width="26" height="26">
        <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" />
      </svg>
    ),
  },
  {
    id: 'quiz' as const,
    label: 'Quiz',
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" width="26" height="26">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
      </svg>
    ),
  },
  {
    id: 'tracks' as const,
    label: 'Rutas',
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" width="26" height="26">
        <path d="M9 2 3 4v18l6-2 6 2 6-2V2l-6 2-6-2zm0 2.3 6 2v13.4l-6-2V4.3z" />
      </svg>
    ),
  },
  {
    id: 'stats' as const,
    label: 'Stats',
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" width="26" height="26">
        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z" />
      </svg>
    ),
  },
  {
    id: 'league' as const,
    label: 'Liga',
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" width="26" height="26">
        <path d="M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94.63 1.5 1.98 2.63 3.61 2.96V19H7v2h10v-2h-4v-3.1c1.63-.33 2.98-1.46 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2zM5 8V7h2v3.82C5.84 10.4 5 9.3 5 8zm14 0c0 1.3-.84 2.4-2 2.82V7h2v1z" />
      </svg>
    ),
  },
  {
    id: 'profile' as const,
    label: 'Perfil',
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" width="26" height="26">
        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
      </svg>
    ),
  },
];

export function BottomNav() {
  const currentScreen = useAppStore((s) => s.currentScreen);
  const setScreen = useAppStore((s) => s.setScreen);
  const startQuiz = useAppStore((s) => s.startQuiz);

  const handleClick = (id: typeof NAV_ITEMS[number]['id']) => {
    if (id === 'quiz') {
      startQuiz('study', 10);
    } else {
      setScreen(id as Parameters<typeof setScreen>[0]);
    }
  };

  return (
    <nav className={styles.nav} role="navigation" aria-label="Main navigation">
      {NAV_ITEMS.map((item) => (
        <button
          key={item.id}
          className={`${styles.item} ${currentScreen === item.id ? styles.active : ''}`}
          onClick={() => handleClick(item.id)}
          aria-label={item.label}
          aria-current={currentScreen === item.id ? 'page' : undefined}
        >
          <span className={styles.icon}>{item.icon}</span>
          <span className={styles.label}>{item.label}</span>
        </button>
      ))}
    </nav>
  );
}
