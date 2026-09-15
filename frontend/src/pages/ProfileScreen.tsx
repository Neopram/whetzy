import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { Card } from '../components/common/Card';
import { ProgressBar } from '../components/common/ProgressBar';
import { useApi } from '../hooks/useApi';
import { usePushNotifications } from '../hooks/usePushNotifications';
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
  const { t, i18n: i18nInst } = useTranslation();

  const badges = useApi(() => gamification.badges(), []);
  const earnedIds = new Set((badges.data ?? []).map((b) => b.badge.id));
  const push = usePushNotifications();
  const [streakPushOn, setStreakPushOn] = useState(true);

  async function handleStreakPushToggle() {
    const next = !streakPushOn;
    setStreakPushOn(next);
    if (next) {
      await push.subscribe();
    }
    try {
      await fetch('/api/v1/push/preferences', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('whetzy_access_token') ?? ''}` },
        body: JSON.stringify({ streak_enabled: next }),
      });
    } catch { /* ignore */ }
  }

  function handleLangChange(lang: 'es' | 'en') {
    setLanguage(lang);
    updateUser({ language: lang });
    void i18nInst.changeLanguage(lang);
  }

  const allBadges = badges.data ?? [];

  return (
    <div className={styles.screen}>
      <div className={styles.profileHeader}>
        <div className={styles.avatar}>{user.avatarEmoji}</div>
        <h1 className={styles.name}>{user.displayName}</h1>
        <p className={styles.username}>@{user.username}</p>
        <div className={styles.levelWrap}>
          <span className={styles.levelBadge}>{t('profile.level')} {user.level}</span>
          <div className={styles.xpBar}>
            <ProgressBar value={user.totalXp % 500} max={500} label={t('a11y.progressXp')} color="var(--le-brand)" height={8} />
            <span className={styles.xpText}>{user.totalXp.toLocaleString()} XP · {t('profile.nextLevel')} {500 - (user.totalXp % 500)} XP</span>
          </div>
        </div>
      </div>

      <div className={styles.statsRow}>
        <div className={styles.statBox}><span className={styles.statVal}>{user.currentStreak}</span><span className={styles.statLabel}>{t('profile.streak')}</span></div>
        <div className={styles.statBox}><span className={styles.statVal}>{user.maxStreak}</span><span className={styles.statLabel}>{t('profile.best')}</span></div>
        <div className={styles.statBox}><span className={styles.statVal}>{user.totalXp.toLocaleString()}</span><span className={styles.statLabel}>{t('profile.totalXp')}</span></div>
      </div>

      {!user.isPremium && (
        <Card className={styles.proCard}>
          <div className={styles.proContent}>
            <span className={styles.proIcon}>👑</span>
            <div>
              <h3 className={styles.proTitle}>Whetzy Pro</h3>
              <p className={styles.proDesc}>{t('profile.proDesc')}</p>
            </div>
          </div>
          <button className={styles.proBtn}>$9.99/{t('profile.month')}</button>
        </Card>
      )}

      <Card>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>{t('profile.badges')}</h2>
          <span className={styles.badgeCount}>{earnedIds.size}</span>
        </div>
        {badges.loading && <p className={styles.muted}>{t('profile.loading')}</p>}
        {!badges.loading && allBadges.length === 0 && <p className={styles.muted}>{t('profile.noBadges')}</p>}
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
        <h2 className={styles.cardTitle}>{t('profile.settings')}</h2>
        <div className={styles.settings}>
          <div className={styles.setting}>
            <span className={styles.settingLabel}>{t('profile.langLabel')}</span>
            <div className={styles.langToggle}>
              <button className={`${styles.langBtn} ${language === 'es' ? styles.langActive : ''}`} onClick={() => handleLangChange('es')}>ES</button>
              <button className={`${styles.langBtn} ${language === 'en' ? styles.langActive : ''}`} onClick={() => handleLangChange('en')}>EN</button>
            </div>
          </div>
          <div className={styles.setting}>
            <span className={styles.settingLabel}>{t('profile.darkMode')}</span>
            <button className={`${styles.toggle} ${theme === 'dark' ? styles.toggleOn : ''}`} onClick={() => setTheme(toggleTheme())} role="switch" aria-checked={theme === 'dark'}>
              <span className={styles.toggleThumb} />
            </button>
          </div>
          {push.supported && (
            <div className={styles.setting}>
              <span className={styles.settingLabel}>{t('profile.streakReminders')}</span>
              <button
                className={`${styles.toggle} ${streakPushOn ? styles.toggleOn : ''}`}
                onClick={handleStreakPushToggle}
                role="switch"
                aria-checked={streakPushOn}
              >
                <span className={styles.toggleThumb} />
              </button>
            </div>
          )}
        </div>
      </Card>

      <button className={styles.signOut} onClick={signOut}>{t('profile.signOut')}</button>

      <div className={styles.legalLinks}>
        <a href="/privacy" className={styles.legalLink}>{t('profile.privacy')}</a>
        <span className={styles.legalSep}>·</span>
        <a href="/terms" className={styles.legalLink}>{t('profile.terms')}</a>
        <span className={styles.legalSep}>·</span>
        <a href="/delete-account" className={styles.deleteLink}>{t('profile.deleteAccount')}</a>
      </div>
    </div>
  );
}
