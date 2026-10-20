import { motion, useReducedMotion } from 'framer-motion';
import { DUR } from '../../lib/motion';
import styles from './ProgressBar.module.css';

interface Props {
  value: number;
  max: number;
  /**
   * Accessible name. Required, not optional: a bare role="progressbar" has no
   * name of its own and fails WCAG 2.2 AA 1.1.1 (axe rule aria-progressbar-name),
   * so every call site has to say what it is measuring — in ES and EN.
   */
  label: string;
  color?: string;
  height?: number;
  showLabel?: boolean;
  /** 46.15 D: la barra crece desde 0 al aparecer (Estadísticas). */
  grow?: boolean;
}

export function ProgressBar({ value, max, label, color = 'var(--le-green)', height = 12, showLabel = false, grow = false }: Props) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const reduce = useReducedMotion();
  const animate = grow && !reduce;

  return (
    <div
      className={styles.track}
      style={{ height }}
      role="progressbar"
      aria-label={label}
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
    >
      {animate ? (
        <motion.div
          className={styles.fill}
          data-fx="grow"
          style={{ background: color }}
          initial={{ width: '0%' }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: DUR.response, ease: 'easeOut' }}
        />
      ) : (
        <div className={styles.fill} style={{ width: `${pct}%`, background: color }} />
      )}
      {showLabel && <span className={styles.label}>{Math.round(pct)}%</span>}
    </div>
  );
}
