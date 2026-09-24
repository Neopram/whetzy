import React from 'react';
import styles from './ErrorState.module.css';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  message,
  onRetry,
  retryLabel = 'Reintentar',
}) => {
  return (
    <div className={styles.container} role="alert">
      <div className={styles.iconWrap}>
        <span className={styles.icon}>⚠️</span>
      </div>
      <p className={styles.message}>{message}</p>
      {onRetry && (
        <button type="button" className={styles.retryBtn} onClick={onRetry}>
          {retryLabel}
        </button>
      )}
    </div>
  );
};
