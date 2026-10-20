import type { ReactNode } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { DUR } from '../../lib/motion';

/**
 * Entrada de las páginas sueltas (46.15 A; plan §7.4): Auth, Verificar y
 * Restablecer entran como las pantallas internas, en vez de cambiar de golpe.
 * La landing no: está prerenderizada y entrar desde opacidad 0 retrasaría su
 * primer pintado (LCP).
 */
export function PageEnter({ children }: { children: ReactNode }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      data-fx={reduce ? undefined : 'enter'}
      initial={reduce ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: DUR.response / 2 }}
    >
      {children}
    </motion.div>
  );
}
