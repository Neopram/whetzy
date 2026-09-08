import { useState } from 'react';
import { useAppStore } from '../stores/useAppStore';
import { Card } from '../components/common/Card';
import { ProgressBar } from '../components/common/ProgressBar';
import { useApi } from '../hooks/useApi';
import { gamification } from '../services/api';
import { getStoredTheme, toggleTheme, type Theme } from '../theme';
import styles from './ProfileScreen.module.css';

export function ProfileScreen() {
  const user = useAppStore((s) => s.user);
  const language = useAppStore((s) => s.user.language);
  const setLanguage = useAppStore((s) => s.setLanguage);
  const updateUser = useAppStore((s) => s.updateUser);
  const signOut = useAppStore((s) => s.signOut);
  const [theme, setTheme] = useState<Theme>(getStoredTheme());
  const L = TEXT[language];

  const badges = useApi(() => gamification.badges(), []);
  const earnedIds = new Set((badges.data ?? []).map((b) => b.badge.id));

  // All badge definitions come from earned + a static catalog fallback for locked display.
  const allBadges = badges.data ?? [];

  return (
    <div className={styles.screen}>
      <div className={styles.profileHeader}>
        <div className={styles.avatar}>{user.avatarEmoji}</div>
        <h1 className={styles.name}>{user.displayName}</h1>
        <p className={styles.username}>@{user.username}</p>
        <div className={styles.levelWrap}>
          <span className={styles.levelBadge}>{L.level} {user.level}</span>
          <div className={styles.xpBar}>
            <ProgressBar value={user.totalXp % 500} max={500} color="var(--le-brand)" height={8} />
            <span className={styles.xpText}>{user.totalXp.toLocaleString()} XP · {L.nextLevel} {500 - (user.totalXp % 500)} XP</span>
          </div>
        </div>
      </div>

      <div className={styles.statsRow}>
        <div className={styles.statBox}><span className={styles.statVal}>{user.currentStreak}</span><span className={styles.statLabel}>{L.streak}</span></div>
        <div className={styles.statBox}><span className={styles.statVal}>{user.maxStreak}</span><span className={styles.statLabel}>{L.best}</span></div>
        <div className={styles.statBox}><span className={styles.statVal}>{user.totalXp.toLocaleString()}</span><span className={styles.statLabel}>{L.totalXp}</span></div>
      </div>

      {!user.isPremium && (
        <Card className={styles.proCard}>
          <div className={styles.proContent}>
            <span className={styles.proIcon}>👑</span>
            <div>
              <h3 className={styles.proTitle}>Whetzy Pro</h3>
              <p className={styles.proDesc}>{L.proDesc}</p>
            </div>
          </div>
          <button className={styles.proBtn}>$9.99/{L.month}</button>
        </Card>
      )}

      <Card>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>{L.badges}</h2>
          <span className={styles.badgeCount}>{earnedIds.size}</span>
        </div>
        {badges.loading && <p className={styles.muted}>{L.loading}</p>}
        {!badges.loading && allBadges.length === 0 && <p className={styles.muted}>{L.noBadges}</p>}
        <div className={styles.achievements}>
          {allBadges.map((b) => (
            <div key={b.badge.id} className={styles.achievement}>
              <span className={styles.achIcon}>{b.badge.icon}</span>
              <span className={styles.achName}>{language === 'es' ? b.badge.name_es : b.badge.name_en}</span>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <h2 className={styles.cardTitle}>{L.settings}</h2>
        <div className={styles.settings}>
          <div className={styles.setting}>
            <span className={styles.settingLabel}>{L.langLabel}</span>
            <div className={styles.langToggle}>
              <button className={`${styles.langBtn} ${language === 'es' ? styles.langActive : ''}`} onClick={() => { setLanguage('es'); updateUser({ language: 'es' }); }}>ES</button>
              <button className={`${styles.langBtn} ${language === 'en' ? styles.langActive : ''}`} onClick={() => { setLanguage('en'); updateUser({ language: 'en' }); }}>EN</button>
            </div>
          </div>
          <div className={styles.setting}>
            <span className={styles.settingLabel}>{L.darkMode}</span>
            <button className={`${styles.toggle} ${theme === 'dark' ? styles.toggleOn : ''}`} onClick={() => setTheme(toggleTheme())} role="switch" aria-checked={theme === 'dark'}>
              <span className={styles.toggleThumb} />
            </button>
          </div>
        </div>
      </Card>

      <button className={styles.signOut} onClick={signOut}>{L.signOut}</button>

      <div className={styles.legalLinks}>
        <a href="/privacy" className={styles.legalLink}>{L.privacy}</a>
        <span className={styles.legalSep}>·</span>
        <a href="/terms" className={styles.legalLink}>{L.terms}</a>
        <span className={styles.legalSep}>·</span>
        <a href="/delete-account" className={styles.deleteLink}>{L.deleteAccount}</a>
      </div>
    </div>
  );
}

const TEXT = {
  es: { level: 'Nivel', nextLevel: 'faltan', streak: 'Racha', best: 'Mejor', totalXp: 'XP Total',
    proDesc: 'Ilimitado, tutor AI, sin anuncios', month: 'mes', badges: 'Logros', loading: 'Cargando…',
    noBadges: 'Aún no tienes logros. ¡Empieza a estudiar!', settings: 'Ajustes', langLabel: 'Idioma',
    darkMode: 'Modo oscuro', signOut: 'Cerrar sesión',
    privacy: 'Privacidad', terms: 'Términos', deleteAccount: 'Eliminar cuenta' },
  en: { level: 'Level', nextLevel: 'to go', streak: 'Streak', best: 'Best', totalXp: 'Total XP',
    proDesc: 'Unlimited, AI tutor, no ads', month: 'mo', badges: 'Achievements', loading: 'Loading…',
    noBadges: 'No achievements yet. Start studying!', settings: 'Settings', langLabel: 'Language',
    darkMode: 'Dark mode', signOut: 'Sign out',
    privacy: 'Privacy', terms: 'Terms', deleteAccount: 'Delete account' },
} as const;
