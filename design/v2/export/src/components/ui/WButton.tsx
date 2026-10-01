import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { LoaderCircle } from 'lucide-react';
import styles from './whetzy.module.css';
export interface WButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> { variant?: 'primary' | 'secondary' | 'ghost' | 'danger'; loading?: boolean; icon?: ReactNode }
export function WButton({ variant = 'secondary', loading = false, icon, children, className = '', disabled, ...props }: WButtonProps) {
 return <button className={`${styles.button} ${styles[variant]} ${className}`} disabled={disabled || loading} aria-busy={loading} {...props}>{loading ? <LoaderCircle size={18} className={styles.spin} /> : icon}{children}</button>;
}
