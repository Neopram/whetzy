import { useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { createPortal } from 'react-dom';
import { backdropVariants, sheetVariants } from '../../lib/motion';
import styles from './Sheet.module.css';

interface SheetProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}

export function Sheet({ open, onClose, title, children }: SheetProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', onKey); document.body.style.overflow = ''; };
  }, [open, onClose]);

  return createPortal(
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            className={styles.backdrop}
            variants={backdropVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            onClick={onClose}
          />
          <motion.div
            className={styles.sheet}
            variants={sheetVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            role="dialog"
            aria-modal="true"
          >
            <div className={styles.handle} aria-hidden="true" />
            {title && <h2 className={styles.title}>{title}</h2>}
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>,
    document.body
  );
}
