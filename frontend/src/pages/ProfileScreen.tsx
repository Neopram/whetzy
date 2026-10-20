import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { Button } from '../components/common/Button';
import btn from '../components/common/Button.module.css';
import { Card } from '../components/common/Card';
import { TwoFactorSettings } from '../components/profile/TwoFactorSettings';
import { ProgressBar } from '../components/common/ProgressBar';
import { useApi } from '../hooks/useApi';
import { usePushNotifications } from '../hooks/usePushNotifications';
import { API_BASE_URL, auth, billing, content, gamification } from '../services/api';
import { getStoredTheme, toggleTheme, type Theme } from '../theme';
import { checkoutHref } from '../lib/paddle';
import { preview } from '../lib/feedbackFx';
import styles from './ProfileScreen.module.css';
import { Loading } from '../components/common/Loading';

// Los enlaces de compra llevan el aspecto del Button común (serie 34).
const LINK_PRIMARY = `${btn.btn} ${btn.primary} ${btn.md} ${btn.full}`;
const LINK_SECONDARY = `${btn.btn} ${btn.secondary} ${btn.md} ${btn.full}`;

export function ProfileScreen() {
  const user = useAppStore((s) => s.user);
  const language = useAppStore((s) => s.user.language);
  const setScreen = useAppStore((s) => s.setScreen);
  const setLanguage = useAppStore((s) => s.setLanguage);
  const updateUser = useAppStore((s) => s.updateUser);
  const aiExplanations = useAppStore((s) => s.aiExplanations);
  const toggleAiExplanations = useAppStore((s) => s.toggleAiExplanations);
  const soundEnabled = useAppStore((s) => s.soundEnabled);
  const toggleSound = useAppStore((s) => s.toggleSound);
  const hapticEnabled = useAppStore((s) => s.hapticEnabled);
  const toggleHaptic = useAppStore((s) => s.toggleHaptic);
  const signOut = useAppStore((s) => s.signOut);
  const [theme, setTheme] = useState<Theme>(getStoredTheme());
  const { t, i18n: i18nInst } = useTranslation();

  const badges = useApi(() => gamification.badges(), []);
  // 43.4 (D5): la ruta activa también se cambia desde Yo.
  const activeTrackId = useAppStore((s) => s.activeTrackId);
  const browseTracks = useAppStore((s) => s.browseTracks);
  const tracksList = useApi(() => content.tracks(), []);
  const activeTrack = tracksList.data?.find((tr) => tr.id === activeTrackId);
  // Solo quien paga por la web (Paddle) cancela aquí; App Store y Google Play
  // se cancelan desde la tienda.
  const subscription = useApi(
    () => (user.isPremium ? billing.subscription() : Promise.resolve(null)),
    [user.isPremium],
  );
  // 40.9: el plan anual solo se ofrece si el dueño encendió `ANNUAL_PLAN_ENABLED`
  // y puso el id de precio — `prices.plus_annual`/`pro_annual` vienen null si no.
  const paddleCfg = useApi(
    () => (user.isPremium ? Promise.resolve(null) : billing.paddleConfig()),
    [user.isPremium],
  );
  const [exportState, setExportState] = useState<'idle' | 'busy' | 'error'>('idle');
  const exportData = async () => {
    setExportState('busy');
    try {
      const data = await auth.exportData();
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }),
      );
      const a = document.createElement('a');
      a.href = url;
      a.download = `whetzy-${user.username}-datos.json`;
      a.click();
      URL.revokeObjectURL(url);
      setExportState('idle');
    } catch {
      setExportState('error');
    }
  };
  const [cancelState, setCancelState] = useState<'idle' | 'confirm' | 'busy' | 'done' | 'error'>('idle');

  // Se aplica al momento y se deshace si el servidor falla: un interruptor
  // que miente sobre la baja es peor que uno lento.
  async function handleMarketingToggle() {
    const next = !user.marketingEmails;
    updateUser({ marketingEmails: next });
    try {
      await auth.setMarketingEmails(next);
    } catch {
      updateUser({ marketingEmails: !next });
    }
  }

  async function handleCancel() {
    setCancelState('busy');
    try {
      await billing.cancelPaddle();
      setCancelState('done');
    } catch {
      setCancelState('error');
    }
  }
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
      await fetch(`${API_BASE_URL}/push/preferences`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ streak_enabled: next }),
      });
    } catch { /* ignore */ }
  }

  function handleLangChange(lang: 'es' | 'en') {
    setLanguage(lang);
    updateUser({ language: lang });
    void auth.updateMe({ language: lang }).catch(() => { /* sin red: se reintenta al volver a cambiarlo */ });
    void i18nInst.changeLanguage(lang);
  }
  // 43.3 (D2): las horas por semana salieron del onboarding y viven aquí.
  function handleWeeklyTime(value: number) {
    updateUser({ weeklyTime: value });
    void auth.updateMe({ onboarding_weekly_time: value }).catch(() => { /* sin red: se reintenta al volver a cambiarlo */ });
  }


  const allBadges = badges.data ?? [];

  // La dirección la decide el dueño (frontend/.env.production); sin ella no hay botón.
  const feedbackEmail = import.meta.env.VITE_FEEDBACK_EMAIL as string | undefined;
  const feedbackHref = feedbackEmail
    ? `mailto:${feedbackEmail}?${new URLSearchParams({
        subject: t('profile.feedbackSubject'),
        body: t('profile.feedbackBody', { username: user.username }),
      }).toString().replace(/\+/g, '%20')}`
    : null;

  return (
    <div className={styles.screen}>
      <div className={styles.profileHeader}>
        <div className={styles.avatar}>{user.avatarEmoji}</div>
        <h1 className={styles.name}>{user.displayName}</h1>
        <p className={styles.username}>@{user.username}</p>
        <div className={styles.levelWrap}>
          <span className={styles.levelBadge}>{t('profile.level')} {user.level}</span>
          <div className={styles.xpBar}>
            <ProgressBar value={user.totalXp % 500} max={500} label={t('a11y.progressXp')} color="var(--le-blue)" height={4} />
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
          <h2 className={styles.proTitle}>Whetzy Pro</h2>
          <p className={styles.proDesc}>{t('profile.proDesc')}</p>
          <div className={styles.proActions}>
            <a className={LINK_PRIMARY} href={checkoutHref('plus')}>{t('profile.proBuy')}</a>
            <a className={LINK_SECONDARY} href={checkoutHref('pro')}>{t('profile.proMaxBuy')}</a>
          </div>
          {paddleCfg.data?.prices.plus_annual && (
            <div className={styles.proActions}>
              <a className={LINK_PRIMARY} href={checkoutHref('plus_annual')}>{t('profile.proBuyAnnual')}</a>
              {paddleCfg.data.prices.pro_annual && (
                <a className={LINK_SECONDARY} href={checkoutHref('pro_annual')}>{t('profile.proMaxBuyAnnual')}</a>
              )}
            </div>
          )}
        </Card>
      )}

      {user.grantedTier && user.grantedUntil && (
        <Card className={styles.proCard}>
          <p className={styles.proDesc}>
            {t('profile.grantedPlan', {
              plan: user.grantedTier === 'pro' ? 'Pro Max' : 'Pro',
              date: new Date(user.grantedUntil).toLocaleDateString(i18nInst.language, { day: 'numeric', month: 'long', year: 'numeric' }),
            })}
          </p>
        </Card>
      )}

      {user.isPremium && subscription.data?.subscription_provider === 'paddle' && (
        <Card>
          <h2 className={styles.cardTitle}>{t('profile.subscriptionTitle')}</h2>
          {subscription.data.subscription_status === 'canceled' || cancelState === 'done' ? (
            <p className={styles.muted}>{t('profile.cancelDone')}</p>
          ) : cancelState === 'confirm' || cancelState === 'busy' ? (
            <>
              <p className={styles.muted}>{t('profile.cancelConfirm')}</p>
              <div className={styles.proActions}>
                <Button type="button" variant="danger" full disabled={cancelState === 'busy'} onClick={() => void handleCancel()}>
                  {t('profile.cancelYes')}
                </Button>
                <Button type="button" variant="ghost" full disabled={cancelState === 'busy'} onClick={() => setCancelState('idle')}>
                  {t('profile.cancelNo')}
                </Button>
              </div>
            </>
          ) : (
            <>
              {cancelState === 'error' && <p className={styles.muted} role="alert">{t('profile.cancelError')}</p>}
              <Button type="button" variant="ghost" full onClick={() => setCancelState('confirm')}>
                {t('profile.cancel')}
              </Button>
            </>
          )}
        </Card>
      )}

      <Card>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>{t('profile.badges')}</h2>
          <span className={styles.badgeCount}>{earnedIds.size}</span>
        </div>
        {badges.loading && <Loading label={t('profile.loading')} shape="line" />}
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
        <h2 className={styles.cardTitle}>{t('profile.explore')}</h2>
        <div className={styles.settings}>
          {feedbackHref && (
            <a className={styles.setting} href={feedbackHref}>
              <span className={styles.settingLabel}>{t('profile.feedback')}</span>
              <span aria-hidden="true">→</span>
            </a>
          )}
          <button
            type="button"
            className={styles.setting}
            onClick={() => setScreen('stats')}
          >
            <span className={styles.settingLabel}>{t('nav.stats')}</span>
            <span aria-hidden="true">→</span>
          </button>
          <button
            type="button"
            className={styles.setting}
            onClick={() => setScreen('wallet')}
          >
            <span className={styles.settingLabel}>{t('wallet.title')}</span>
            <span aria-hidden="true">→</span>
          </button>
          <button
            type="button"
            className={styles.setting}
            onClick={() => setScreen('marketplace')}
          >
            <span className={styles.settingLabel}>{t('profile.goCatalog')}</span>
            <span aria-hidden="true">→</span>
          </button>
          {/* «Instructor» es para creadores, no para suscripciones regulares
              (dueño, 2026-10-16); «Admin», solo para el dueño (#202). */}
          {user.canCreateCourses && (
            <button
              type="button"
              className={styles.setting}
              onClick={() => setScreen('instructor')}
            >
              <span className={styles.settingLabel}>{t('profile.goInstructor')}</span>
              <span aria-hidden="true">→</span>
            </button>
          )}
          {user.isOwner && (
            <button
              type="button"
              className={styles.setting}
              onClick={() => setScreen('admin')}
            >
              <span className={styles.settingLabel}>{t('profile.goAdmin')}</span>
              <span aria-hidden="true">→</span>
            </button>
          )}
        </div>
      </Card>

      <Card>
        <h2 className={styles.cardTitle}>{t('profile.settings')}</h2>
        <div className={styles.settings}>
          <div className={styles.setting}>
            <span className={styles.settingLabel}>{t('profile.langLabel')}</span>
            <div className={styles.langToggle}>
              <button type="button" aria-pressed={language === 'es'} className={`${styles.langBtn} ${language === 'es' ? styles.langActive : ''}`} onClick={() => handleLangChange('es')}>ES</button>
              <button type="button" aria-pressed={language === 'en'} className={`${styles.langBtn} ${language === 'en' ? styles.langActive : ''}`} onClick={() => handleLangChange('en')}>EN</button>
            </div>
          </div>
          <div className={styles.setting}>
            <span className={styles.settingLabel}>
              {t('profile.activeTrack')}
              {': '}
              <strong data-testid="profile-active-track">
                {activeTrack ? (language === 'es' ? activeTrack.name_es : activeTrack.name_en) : (activeTrackId ?? t('profile.noActiveTrack'))}
              </strong>
            </span>
            <button
              type="button"
              className={styles.langBtn}
              onClick={browseTracks}
            >
              {activeTrackId ? t('profile.changeTrack') : t('profile.chooseTrack')}
            </button>
          </div>
          <div className={styles.setting}>
            <span className={styles.settingLabel} id="weekly-time-label">{t('profile.weeklyTime')}</span>
            <div className={styles.langToggle} role="group" aria-labelledby="weekly-time-label">
              {[0, 1, 2].map((v) => (
                <button key={v} type="button" aria-pressed={user.weeklyTime === v} className={`${styles.langBtn} ${user.weeklyTime === v ? styles.langActive : ''}`} onClick={() => handleWeeklyTime(v)}>
                  {t(`profile.weeklyTimeOptions.${v}`)}
                </button>
              ))}
            </div>
          </div>
          <div className={styles.setting}>
            <span className={styles.settingLabel}>{t('profile.darkMode')}</span>
            <button type="button" className={`${styles.toggle} ${theme === 'dark' ? styles.toggleOn : ''}`} onClick={() => setTheme(toggleTheme())} role="switch" aria-checked={theme === 'dark'} aria-label={t('profile.darkMode')}>
              <span className={styles.track}><span className={styles.toggleThumb} /></span>
            </button>
          </div>
          <div className={styles.setting}>
            <span className={styles.settingLabel}>{t('profile.aiExplanations')}</span>
            <button
              className={`${styles.toggle} ${aiExplanations ? styles.toggleOn : ''}`}
              type="button"
              onClick={toggleAiExplanations}
              role="switch"
              aria-checked={aiExplanations}
              aria-label={t('profile.aiExplanations')}
            >
              <span className={styles.track}><span className={styles.toggleThumb} /></span>
            </button>
          </div>
          <div className={styles.setting}>
            <span className={styles.settingLabel}>{t('producto:fx.sound')}</span>
            <button
              className={`${styles.toggle} ${soundEnabled ? styles.toggleOn : ''}`}
              type="button"
              onClick={() => { toggleSound(); preview('sound'); }}
              role="switch"
              aria-checked={soundEnabled}
              aria-label={t('producto:fx.sound')}
            >
              <span className={styles.track}><span className={styles.toggleThumb} /></span>
            </button>
          </div>
          <div className={styles.setting}>
            <span className={styles.settingLabel}>{t('producto:fx.haptics')}</span>
            <button
              className={`${styles.toggle} ${hapticEnabled ? styles.toggleOn : ''}`}
              type="button"
              onClick={() => { toggleHaptic(); preview('haptic'); }}
              role="switch"
              aria-checked={hapticEnabled}
              aria-label={t('producto:fx.haptics')}
            >
              <span className={styles.track}><span className={styles.toggleThumb} /></span>
            </button>
          </div>
          <div className={styles.setting}>
            <span className={styles.settingLabel}>{t('profile.marketingEmails')}</span>
            <button
              className={`${styles.toggle} ${user.marketingEmails ? styles.toggleOn : ''}`}
              type="button"
              onClick={() => void handleMarketingToggle()}
              role="switch"
              aria-checked={user.marketingEmails}
              aria-label={t('profile.marketingEmails')}
            >
              <span className={styles.track}><span className={styles.toggleThumb} /></span>
            </button>
          </div>
          {push.supported && (
            <div className={styles.setting}>
              <span className={styles.settingLabel}>{t('profile.streakReminders')}</span>
              <button
                className={`${styles.toggle} ${streakPushOn ? styles.toggleOn : ''}`}
                type="button"
                onClick={handleStreakPushToggle}
                role="switch"
                aria-checked={streakPushOn}
                aria-label={t('profile.streakReminders')}
              >
                <span className={styles.track}><span className={styles.toggleThumb} /></span>
              </button>
            </div>
          )}
          <TwoFactorSettings />
        </div>
      </Card>

      <Button type="button" variant="ghost" full onClick={signOut}>{t('profile.signOut')}</Button>

      <div className={styles.legalLinks}>
        <a href="/privacy" className={styles.legalLink}>{t('profile.privacy')}</a>
        <span className={styles.legalSep}>·</span>
        <a href="/terms" className={styles.legalLink}>{t('profile.terms')}</a>
        <span className={styles.legalSep}>·</span>
        <button
          type="button"
          className={styles.legalLink}
          onClick={exportData}
          disabled={exportState === 'busy'}
        >
          {exportState === 'busy' ? t('profile.exporting') : t('profile.exportData')}
        </button>
        <span className={styles.legalSep}>·</span>
        <a href="/delete-account" className={styles.deleteLink}>{t('profile.deleteAccount')}</a>
      </div>
      {exportState === 'error' && <p role="alert" className={styles.exportError}>{t('profile.exportError')}</p>}
    </div>
  );
}
