import { forwardRef } from 'react';
import { motion } from 'framer-motion';
import { tapScale } from '../../lib/motion';
import styles from './Button.module.css';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'success' | 'text';
type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  full?: boolean;
  loading?: boolean;
  iconOnly?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      full = false,
      loading = false,
      iconOnly = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      className = '',
      ...rest
    },
    ref
  ) => {
    const cls = [
      styles.btn,
      styles[variant],
      styles[size],
      full ? styles.full : '',
      iconOnly ? styles.icon : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <motion.button
        ref={ref}
        className={cls}
        disabled={disabled || loading}
        whileTap={disabled || loading ? undefined : tapScale}
        {...(rest as object)}
      >
        {loading ? (
          <span className={styles.spinner} aria-hidden="true" />
        ) : (
          <>
            {leftIcon}
            {children}
            {rightIcon}
          </>
        )}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';
