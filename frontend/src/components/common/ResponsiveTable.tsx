import React from 'react';
import styles from './ResponsiveTable.module.css';

interface ResponsiveTableProps {
  children: React.ReactNode;
  ariaLabel?: string;
  minWidth?: number | string;
}

export const ResponsiveTable: React.FC<ResponsiveTableProps> = ({
  children,
  ariaLabel = 'Tabla de datos',
  minWidth = '600px',
}) => {
  return (
    <div className={styles.tableWrapper} role="region" aria-label={ariaLabel} tabIndex={0}>
      <div className={styles.scrollHint}>↔ Desliza horizontalmente</div>
      <div className={styles.innerContainer} style={{ minWidth }}>
        {children}
      </div>
    </div>
  );
};
