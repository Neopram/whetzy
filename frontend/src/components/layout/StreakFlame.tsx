import { useEffect, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../../stores/useAppStore';
import styles from './StreakFlame.module.css';

/**
 * Llama de la racha en la TopBar (46.11, docs/PLAN_UI_AVANZADA.md §7.3).
 *
 * Crece por tramos (1–6, 7–29, ≥ 30 días) y brilla más en cada uno. El día que
 * el servidor gasta un comodín (`streak_freeze_used` en `events[]`), un escudo
 * la cubre 600 ms y se anuncia en texto: la racha siguió gracias a él.
 */
export type FlameTier = 1 | 2 | 3;

export function flameTier(days: number): FlameTier {
  return days >= 30 ? 3 : days >= 7 ? 2 : 1;
}

const SIZE: Record<FlameTier, number> = { 1: 16, 2: 20, 3: 24 };
export const SHIELD_MS = 600;

export function StreakFlame({ days }: { days: number }) {
  const { t } = useTranslation();
  const reduce = useReducedMotion();
  const shieldAt = useAppStore((s) => s.streakShieldAt);
  const [shield, setShield] = useState(false);
  const tier = flameTier(days);
  const size = SIZE[tier];

  useEffect(() => {
    if (shieldAt === null) return;
    setShield(true);
    const id = window.setTimeout(() => setShield(false), SHIELD_MS);
    return () => window.clearTimeout(id);
  }, [shieldAt]);

  return (
    <span className={styles.wrap} style={{ width: size, height: size }}>
      <svg
        data-testid="streak-flame"
        data-tier={tier}
        className={`${styles.flame} ${styles[`t${tier}`]}`}
        viewBox="0 0 24 24"
        fill="currentColor"
        width={size}
        height={size}
        aria-hidden="true"
      >
        <path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14 0-1.62 1.05-2.76 2.81-3.12 1.77-.36 3.6-1.21 4.62-2.58.39 1.29.59 2.65.59 4.04 0 2.65-2.15 4.8-4.8 4.8z" />
      </svg>
      <AnimatePresence>
        {shield && (
          <motion.svg
            key={shieldAt}
            data-testid="streak-shield"
            className={styles.shield}
            viewBox="0 0 24 24"
            width={size}
            height={size}
            aria-hidden="true"
            initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.6 }}
            animate={reduce ? { opacity: 1 } : { opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
          >
            <path d="M12 2 4 5v6c0 5 3.4 9.7 8 11 4.6-1.3 8-6 8-11V5l-8-3Z" />
          </motion.svg>
        )}
      </AnimatePresence>
      {shield && <span className="visually-hidden" role="status">{t('topbar.streakShield')}</span>}
    </span>
  );
}
