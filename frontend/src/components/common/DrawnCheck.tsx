import { motion, useReducedMotion } from 'framer-motion';
import { DUR } from '../../lib/motion';
import styles from './DrawnCheck.module.css';

/**
 * Check que se dibuja (46.15 A, docs/PLAN_UI_AVANZADA.md §7.5): solo cuando el
 * servidor ha confirmado algo (correo verificado, enlace enviado). Decorativo:
 * el texto de al lado dice lo mismo. Con movimiento reducido, estático.
 */
export function DrawnCheck() {
  const reduce = useReducedMotion();
  const draw = reduce ? {} : { initial: { pathLength: 0 }, animate: { pathLength: 1 } };
  return (
    <svg
      className={styles.check}
      viewBox="0 0 48 48"
      width="56"
      height="56"
      aria-hidden="true"
      data-testid="drawn-check"
      data-fx={reduce ? undefined : 'draw'}
    >
      <motion.circle cx="24" cy="24" r="21" {...draw} transition={{ duration: DUR.milestone * 0.6 }} />
      <motion.path d="M14 25 l7 7 l13 -15" {...draw} transition={{ duration: DUR.milestone * 0.4, delay: DUR.milestone * 0.5 }} />
    </svg>
  );
}
