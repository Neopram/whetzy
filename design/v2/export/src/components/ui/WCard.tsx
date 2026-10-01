import type { HTMLAttributes } from 'react';
import styles from './whetzy.module.css';
export interface WCardProps extends HTMLAttributes<HTMLElement> { variant?: 'default' | 'interactive' | 'highlighted' }
export function WCard({ variant = 'default', className = '', children, ...props }: WCardProps) { return <article className={`${styles.card} ${styles[variant]} ${className}`} {...props}>{children}</article>; }
