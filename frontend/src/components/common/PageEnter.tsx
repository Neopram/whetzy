import type { ReactNode } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { DUR } from '../../lib/motion';

/**
 * Entrada de las páginas sueltas (46.15 A y 46.14; plan §7.4): Auth, Verificar,
 * Restablecer, Estado y la landing entran como las pantallas internas, en vez
 * de cambiar de golpe.
 *
 * La landing (decisión del dueño, 2026-10-21) entra también, pero con
 * `fade={false}`: su hero está prerenderizado y es el elemento del LCP
 * (`data-lcp="hero"`, scripts/prerender-landing.mjs). Entrar desde opacidad 0
 * lo ocultaría hasta que arranque el JS y retrasaría el LCP. Solo con
 * `transform` (8 px hacia arriba) el hero sigue visible y pintado desde el
 * primer fotograma, y el movimiento no cuenta para el LCP ni para el CLS.
 */
export function PageEnter({ children, fade = true }: { children: ReactNode; fade?: boolean }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      data-fx={reduce ? undefined : 'enter'}
      initial={reduce ? false : fade ? { opacity: 0, y: 8 } : { y: 8 }}
      animate={fade ? { opacity: 1, y: 0 } : { y: 0 }}
      transition={{ duration: DUR.response / 2 }}
    >
      {children}
    </motion.div>
  );
}
