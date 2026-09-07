import styles from './ProgressBar.module.css';

interface Props {
  value: number;
  max: number;
  color?: string;
  height?: number;
  showLabel?: boolean;
}

export function ProgressBar({ value, max, color = 'var(--le-green)', height = 12, showLabel = false }: Props) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={styles.track} style={{ height }} role="progressbar" aria-valuenow={value} aria-valuemax={max}>
      <div className={styles.fill} style={{ width: `${pct}%`, background: color }} />
      {showLabel && <span className={styles.label}>{Math.round(pct)}%</span>}
    </div>
  );
}
