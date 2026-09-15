import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useSpring, useMotionValue, useTransform, motion } from 'framer-motion';
import { useAppStore } from '../../stores/useAppStore';
import { useOfflineSync } from '../../hooks/useOfflineSync';
import styles from './TopBar.module.css';

function useCountUp(value: number) {
  const mv = useMotionValue(value);
  const spring = useSpring(mv, { stiffness: 80, damping: 20 });
  const display = useTransform(spring, (v) => Math.round(v).toLocaleString());
  const prevRef = useRef(value);
  useEffect(() => {
    if (value !== prevRef.current) { mv.set(value); prevRef.current = value; }
  }, [value, mv]);
  return display;
}

export function TopBar() {
  const { t } = useTranslation('common');
  const user = useAppStore((s) => s.user);
  const { isOnline, isSyncing, pendingAnswers } = useOfflineSync();
  const xpDisplay = useCountUp(user.totalXp);

  return (
    <header className={styles.topbar}>
      <div className={styles.left}>
        <div className={styles.logo}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" width="26" height="26">
            <path d="M12 12.5 12 4M12 12.5 5.5 19M12 12.5 18.5 19M12 4 5.5 19M5.5 19 18.5 19M18.5 19 12 4" opacity="0.55" />
            <circle cx="12" cy="12.5" r="2.6" fill="currentColor" stroke="none" />
            <circle cx="12" cy="4" r="1.9" fill="currentColor" stroke="none" />
            <circle cx="5.5" cy="19" r="1.9" fill="currentColor" stroke="none" />
            <circle cx="18.5" cy="19" r="1.9" fill="currentColor" stroke="none" />
          </svg>
          <span>Whetzy</span>
        </div>
      </div>
      <div className={styles.right}>
        {!isOnline && (
          <div style={{
            fontSize: 11, fontWeight: 700, color: '#fff',
            background: isSyncing ? 'var(--le-brand)' : 'var(--le-orange)',
            borderRadius: 8, padding: '3px 8px', lineHeight: 1.4,
          }}>
            {isSyncing ? t('offline.syncing') : pendingAnswers > 0 ? t('offline.noConnectionWithCount', { count: pendingAnswers }) : t('offline.noConnection')}
          </div>
        )}
        <div className={`${styles.stat} ${styles.streak}`} title="Racha">
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
            <path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14 0-1.62 1.05-2.76 2.81-3.12 1.77-.36 3.6-1.21 4.62-2.58.39 1.29.59 2.65.59 4.04 0 2.65-2.15 4.8-4.8 4.8z" />
          </svg>
          <span>{user.currentStreak}</span>
        </div>
        <div className={`${styles.stat} ${styles.gems}`} title="XP total">
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
            <path d="M13 2L3 14h6l-1 8 10-12h-6l1-8z" />
          </svg>
          <motion.span>{xpDisplay}</motion.span>
        </div>
        <div className={`${styles.stat} ${styles.level}`} title="Nivel">
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
            <path d="M12 2l2.4 7.4H22l-6 4.6 2.3 7.4L12 17l-6.3 4.4L8 14 2 9.4h7.6z" />
          </svg>
          <span>{user.level}</span>
        </div>
      </div>
    </header>
  );
}
