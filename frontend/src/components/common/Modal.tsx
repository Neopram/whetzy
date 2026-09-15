import { useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { createPortal } from 'react-dom';
import { backdropVariants, modalVariants } from '../../lib/motion';
import styles from './Modal.module.css';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  closeOnBackdrop?: boolean;
}

export function Modal({ open, onClose, title, children, footer, closeOnBackdrop = true }: ModalProps) {
  const firstFocusRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    firstFocusRef.current?.focus();
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
      prev?.focus();
    };
  }, [open, onClose]);

  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div
          className={styles.backdrop}
          variants={backdropVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          onClick={closeOnBackdrop ? onClose : undefined}
          aria-modal="true"
          role="dialog"
        >
          <motion.div
            className={styles.modal}
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            onClick={(e) => e.stopPropagation()}
          >
            {(title != null || true) && (
              <div className={styles.header}>
                {title && <h2 className={styles.title}>{title}</h2>}
                <button
                  ref={firstFocusRef}
                  className={styles.closeBtn}
                  onClick={onClose}
                  aria-label="Cerrar"
                >
                  ✕
                </button>
              </div>
            )}
            <div className={styles.body}>{children}</div>
            {footer && <div className={styles.footer}>{footer}</div>}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  );
}
