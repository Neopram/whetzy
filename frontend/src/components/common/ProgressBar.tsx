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
}

export function ProgressBar({ value, max, label, color = 'var(--le-green)', height = 12, showLabel = false }: Props) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

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
      <div className={styles.fill} style={{ width: `${pct}%`, background: color }} />
      {showLabel && <span className={styles.label}>{Math.round(pct)}%</span>}
    </div>
  );
}
