/**
 * Combo del quiz con anillo de progreso (46.1, docs/PLAN_UI_AVANZADA.md §6.2).
 *
 * El anillo se llena hacia el próximo umbral de multiplicador del servidor
 * (`COMBO_MULTIPLIERS` en backend/app/services/quiz.py: 3 → ×2, 7 → ×3,
 * 15 → ×5). Al cruzarlo, la etiqueta «×N» salta; con movimiento reducido solo
 * cambia, sin salto. El texto dice lo mismo que el anillo, para quien no lo ve.
 */
import { motion, useReducedMotion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { springs } from '../../lib/motion';
import styles from './ComboRing.module.css';

export const COMBO_STEPS: readonly [number, number][] = [[3, 2], [7, 3], [15, 5]];

/** Multiplicador vigente con este combo (1 si aún no llega a 3). */
export function multiplierFor(combo: number): number {
  let m = 1;
  for (const [at, x] of COMBO_STEPS) if (combo >= at) m = x;
  return m;
}

/** Fracción del camino desde el umbral anterior hasta el siguiente (1 pasado el último). */
export function ringProgress(combo: number): number {
  let from = 0;
  for (const [at] of COMBO_STEPS) {
    if (combo < at) return (combo - from) / (at - from);
    from = at;
  }
  return 1;
}

const R = 9;
const C = 2 * Math.PI * R;

export function ComboRing({ combo }: { combo: number }) {
  const { t } = useTranslation();
  const reduce = useReducedMotion();
  const mult = multiplierFor(combo);
  const crossed = COMBO_STEPS.some(([at]) => at === combo);
  const dash = C * ringProgress(combo);

  return (
    <span className={styles.combo} data-testid="combo">
      <svg className={styles.ring} viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
        <circle className={styles.track} cx="12" cy="12" r={R} />
        <motion.circle
          className={styles.fill}
          cx="12" cy="12" r={R}
          strokeDasharray={C}
          initial={false}
          animate={{ strokeDashoffset: C - dash }}
          transition={reduce ? { duration: 0 } : springs.gentle}
        />
      </svg>
      <span>{t('quiz.comboLabel', { n: combo })}</span>
      {mult > 1 && (
        <motion.b
          key={mult}
          className={styles.mult}
          initial={crossed && !reduce ? { scale: 1.6 } : false}
          animate={{ scale: 1 }}
          transition={springs.bouncy}
        >
          ×{mult}
        </motion.b>
      )}
    </span>
  );
}
