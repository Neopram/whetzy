import { useEffect, useId, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';
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

const FOCUSABLE =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function Modal({ open, onClose, title, children, footer, closeOnBackdrop = true }: ModalProps) {
  const { t } = useTranslation();
  const firstFocusRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  // Revisión de UI del 2026-10-23: el efecto dependía de `onClose`, y quien pasa
  // una función nueva en cada render (UsersPanel) lo repetía a cada tecla: el
  // foco saltaba al ✕. Se lee la última `onClose` desde una ref.
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    firstFocusRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCloseRef.current();
        return;
      }
      // El Tab no sale del modal: del último control vuelve al primero y al revés.
      if (e.key !== 'Tab' || !panelRef.current) return;
      const focusables = Array.from(panelRef.current.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      } else if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      }
    };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
      prev?.focus();
    };
  }, [open]);

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
          aria-labelledby={title ? titleId : undefined}
        >
          <motion.div
            ref={panelRef}
            className={styles.modal}
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            onClick={(e) => e.stopPropagation()}
          >
            {/* The header always renders: it carries the close button, which is
                the focus target and the only way out for a keyboard user when
                the modal has no title. */}
            <div className={styles.header}>
              {title && <h2 id={titleId} className={styles.title}>{title}</h2>}
              <button
                ref={firstFocusRef}
                className={styles.closeBtn}
                onClick={onClose}
                aria-label={t('quiz.close')}
              >
                <span aria-hidden="true">✕</span>
              </button>
            </div>
            <div className={styles.body}>{children}</div>
            {footer && <div className={styles.footer}>{footer}</div>}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  );
}
