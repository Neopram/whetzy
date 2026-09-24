import React from 'react';
import styles from './EmptyState.module.css';

interface EmptyStateProps {
  icon?: string | React.ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = '✨',
  title,
  description,
  actionLabel,
  onAction,
}) => {
  return (
    <div className={styles.container}>
      <div className={styles.iconWrap}>
        {typeof icon === 'string' ? <span className={styles.icon}>{icon}</span> : icon}
      </div>
      <h3 className={styles.title}>{title}</h3>
      {description && <p className={styles.description}>{description}</p>}
      {actionLabel && onAction && (
        <button type="button" className={styles.actionBtn} onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
};
