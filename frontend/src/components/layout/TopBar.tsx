import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useSpring, useMotionValue, useTransform, motion } from 'framer-motion';
import { useAppStore } from '../../stores/useAppStore';
import { useOfflineSync } from '../../hooks/useOfflineSync';
import { BrandMark } from '../common/BrandMark';
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
          <BrandMark height={24} />
          <span>Whet<span className={styles.logoAccent}>zy</span></span>
        </div>
      </div>
      <div className={styles.right}>
        {!isOnline && (
          <div style={{
            fontSize: 11, fontWeight: 700, color: 'var(--le-text-inverse)',
            background: isSyncing ? 'var(--le-brand)' : 'var(--le-orange)',
            borderRadius: 8, padding: '3px 8px', lineHeight: 1.4,
          }}>
            {isSyncing ? t('offline.syncing') : pendingAnswers > 0 ? t('offline.noConnectionWithCount', { count: pendingAnswers }) : t('offline.noConnection')}
          </div>
        )}
        {/* Cada cifra lleva su etiqueta (design/v2): antes eran tres números
            sueltos (racha, XP, nivel) sin decir qué medía cada uno. El nivel
            vive en Yo. */}
        <div className={`${styles.stat} ${styles.streak}`} title={t('topbar.streakLabel')}>
          <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16" aria-hidden="true">
            <path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14 0-1.62 1.05-2.76 2.81-3.12 1.77-.36 3.6-1.21 4.62-2.58.39 1.29.59 2.65.59 4.04 0 2.65-2.15 4.8-4.8 4.8z" />
          </svg>
          <span className={styles.value}>{user.currentStreak}</span>
          <span className={styles.unit}>{t('topbar.days', { count: user.currentStreak })}</span>
        </div>
        <div className={`${styles.stat} ${styles.gems}`} title={t('topbar.xpLabel')}>
          <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16" aria-hidden="true">
            <path d="M13 2L3 14h6l-1 8 10-12h-6l1-8z" />
          </svg>
          <motion.span className={styles.value}>{xpDisplay}</motion.span>
          <span className={styles.unit}>{t('topbar.xp')}</span>
        </div>
      </div>
    </header>
  );
}
