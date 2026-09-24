import React from 'react';
import styles from './TabsNav.module.css';

export interface TabItem<T extends string = string> {
  id: T;
  label: string;
  badge?: string | number;
  icon?: string | React.ReactNode;
}

interface TabsNavProps<T extends string = string> {
  tabs: TabItem<T>[];
  activeTab: T;
  onChange: (id: T) => void;
  ariaLabel?: string;
}

export function TabsNav<T extends string = string>({
  tabs,
  activeTab,
  onChange,
  ariaLabel = 'Pestañas de navegación',
}: TabsNavProps<T>) {
  return (
    <nav className={styles.wrapper} aria-label={ariaLabel}>
      <div className={styles.scrollContainer} role="tablist">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              role="tab"
              type="button"
              aria-selected={isActive}
              className={`${styles.tabBtn} ${isActive ? styles.active : ''}`}
              onClick={() => onChange(tab.id)}
            >
              {tab.icon && <span className={styles.icon}>{tab.icon}</span>}
              <span className={styles.label}>{tab.label}</span>
              {tab.badge !== undefined && (
                <span className={`${styles.badge} ${isActive ? styles.badgeActive : ''}`}>
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
