import type { HTMLAttributes } from 'react';
import styles from './whetzy.module.css';
export interface ChipProps extends HTMLAttributes<HTMLSpanElement> { tone?: 'neutral' | 'success' | 'attention' | 'error' }
export function Chip({ tone = 'neutral', className = '', children, ...props }: ChipProps) { return <span className={`${styles.chip} ${styles[tone]} ${className}`} {...props}>{children}</span>; }
