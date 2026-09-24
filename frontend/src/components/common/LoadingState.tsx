import React from 'react';
import styles from './LoadingState.module.css';

interface LoadingStateProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  fullScreen?: boolean;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Cargando contenido...',
  size = 'md',
  fullScreen = false,
}) => {
  return (
    <div className={`${styles.container} ${fullScreen ? styles.fullScreen : ''} ${styles[size]}`}>
      <div className={styles.spinner} role="status" aria-label="Cargando">
        <div className={styles.glowRing} />
        <div className={styles.innerCore} />
      </div>
      {message && <p className={styles.message}>{message}</p>}
    </div>
  );
};
