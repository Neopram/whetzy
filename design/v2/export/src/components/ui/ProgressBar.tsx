import styles from './whetzy.module.css';
export interface ProgressBarProps { value: number; label: string; tone?: 'steel' | 'ember' | 'success' }
export function ProgressBar({ value, label, tone = 'steel' }: ProgressBarProps) { return <div className={`${styles.progress} ${styles[tone]}`} role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(value * 100)}><span style={{ width: `${Math.max(0, Math.min(100, value * 100))}%` }}/></div>; }
