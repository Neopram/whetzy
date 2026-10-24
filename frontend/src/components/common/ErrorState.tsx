import React from 'react';
import { useTranslation } from 'react-i18next';
import styles from './ErrorState.module.css';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  message,
  onRetry,
  retryLabel,
}) => {
  // Revisión de UI del 2026-10-23: el texto por defecto era «Reintentar» fijo,
  // también en inglés; y el lector de pantalla leía el emoji antes del mensaje.
  const { t } = useTranslation();
  return (
    <div className={styles.container} role="alert">
      <div className={styles.iconWrap}>
        <span className={styles.icon} aria-hidden="true">⚠️</span>
      </div>
      <p className={styles.message}>{message}</p>
      {onRetry && (
        <button type="button" className={styles.retryBtn} onClick={onRetry}>
          {retryLabel ?? t('common.retry')}
        </button>
      )}
    </div>
  );
};
