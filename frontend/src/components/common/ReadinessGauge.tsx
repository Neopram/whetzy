import type { ReactNode } from 'react';
import styles from './ReadinessGauge.module.css';

interface Props {
  /** 0–100. */
  value: number;
  /** Texto bajo la cifra, dentro del arco. */
  label: string;
  /** Lectura completa para lectores de pantalla. */
  ariaLabel: string;
  /** Umbral en %, marcado sobre el arco. */
  threshold?: number;
  children?: ReactNode;
}

// Semicírculo de radio 82 con centro (100,100), de izquierda a derecha
// (design/v2). El marcador del umbral se coloca por ángulo: al 75 % cae en
// (158, 42).
const R = 82;

export function ReadinessGauge({ value, label, ariaLabel, threshold = 75, children }: Props) {
  const v = Math.max(0, Math.min(100, Math.round(value)));
  const angle = Math.PI * (1 - threshold / 100);
  const mx = 100 + R * Math.cos(angle);
  const my = 100 - R * Math.sin(angle);
  return (
    <div className={styles.wrap}>
      <div className={styles.gauge}>
        <svg viewBox="0 0 200 120" role="img" aria-label={ariaLabel}>
          <path className={styles.track} d="M 18 100 A 82 82 0 0 1 182 100" />
          <path
            className={styles.fill}
            d="M 18 100 A 82 82 0 0 1 182 100"
            pathLength={100}
            strokeDasharray={`${v} 100`}
          />
          <circle className={styles.marker} cx={mx} cy={my} r="4" />
        </svg>
        <div className={styles.value} aria-hidden="true">
          <strong>{v}<small>%</small></strong>
          <span>{label}</span>
        </div>
      </div>
      {children}
    </div>
  );
}
