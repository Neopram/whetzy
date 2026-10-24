import { useState, type ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import { useHideOnScroll } from '../../hooks/useHideOnScroll';
import { useAppStore } from '../../stores/useAppStore';
import styles from './BottomNav.module.css';

type Screen = ReturnType<typeof useAppStore.getState>['currentScreen'];

// Cinco pestañas (design/v2): cada una agrupa las pantallas que viven debajo,
// para que la pestaña siga marcada al entrar en una de ellas — Ranking reúne
// liga y duelos; Yo, perfil, estadísticas, cartera y paneles.
const NAV_ITEMS: ReadonlyArray<{
  id: 'home' | 'tracks' | 'quiz' | 'league' | 'profile';
  labelKey: string;
  group: ReadonlyArray<Screen>;
  icon: ReactElement;
}> = [
  {
    id: 'home',
    labelKey: 'nav.home',
    group: ['home'],
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
        <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" />
      </svg>
    ),
  },
  {
    id: 'tracks',
    labelKey: 'nav.tracks',
    group: ['tracks'],
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
        <path d="M9 2 3 4v18l6-2 6 2 6-2V2l-6 2-6-2zm0 2.3 6 2v13.4l-6-2V4.3z" />
      </svg>
    ),
  },
  {
    id: 'quiz',
    labelKey: 'nav.practice',
    group: ['quiz'],
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
        <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm0 2a8 8 0 1 1 0 16 8 8 0 0 1 0-16zm0 3a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6z" />
      </svg>
    ),
  },
  {
    id: 'league',
    labelKey: 'nav.ranking',
    group: ['league', 'duels'],
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
        <path d="M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94.63 1.5 1.98 2.63 3.61 2.96V19H7v2h10v-2h-4v-3.1c1.63-.33 2.98-1.46 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2zM5 8V7h2v3.82C5.84 10.4 5 9.3 5 8zm14 0c0 1.3-.84 2.4-2 2.82V7h2v1z" />
      </svg>
    ),
  },
  {
    id: 'profile',
    labelKey: 'nav.profile',
    group: ['profile', 'stats', 'wallet', 'marketplace', 'instructor', 'admin'],
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
      </svg>
    ),
  },
];

export function BottomNav() {
  const { t } = useTranslation('common');
  const currentScreen = useAppStore((s) => s.currentScreen);
  const setScreen = useAppStore((s) => s.setScreen);
  const startQuiz = useAppStore((s) => s.startQuiz);
  // Se aparta al bajar por la página y vuelve al subir; con el foco dentro
  // (teclado) no se esconde nunca.
  const scrolledAway = useHideOnScroll(currentScreen);
  const [focused, setFocused] = useState(false);
  const hidden = scrolledAway && !focused;

  const handleClick = (id: typeof NAV_ITEMS[number]['id']) => {
    if (id === 'quiz') {
      startQuiz('study', 10);
    } else {
      setScreen(id);
    }
  };

  return (
    <nav
      className={`${styles.nav} ${hidden ? styles.hidden : ''}`}
      role="navigation"
      aria-label={t('nav.main')}
      data-hidden={hidden ? 'true' : undefined}
      onFocus={() => setFocused(true)}
      onBlur={(e) => { if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setFocused(false); }}
    >
      {NAV_ITEMS.map((item) => {
        const label = t(item.labelKey);
        const active = item.group.includes(currentScreen);
        return (
          <button
            key={item.id}
            className={`${styles.item} ${active ? styles.active : ''}`}
            onClick={() => handleClick(item.id)}
            aria-label={label}
            aria-current={active ? 'page' : undefined}
          >
            <span className={styles.icon}>{item.icon}</span>
            <span className={styles.label}>{label}</span>
          </button>
        );
      })}
    </nav>
  );
}
