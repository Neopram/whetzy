import type { ReactNode } from 'react';
import styles from './Card.module.css';

interface Props {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

export function Card({ children, className = '', onClick }: Props) {
  const Tag = onClick ? 'button' : 'div';
  return (
    <Tag className={`${styles.card} ${className}`} onClick={onClick}>
      {children}
    </Tag>
  );
}
