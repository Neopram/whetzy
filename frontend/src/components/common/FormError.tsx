import type { ReactNode } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { DUR } from '../../lib/motion';

/**
 * Error de formulario (46.15 A, docs/PLAN_UI_AVANZADA.md §7.5): tiembla una
 * vez, sin sonido, y vuelve a temblar si el mensaje cambia (`key`). El lector
 * de pantalla lo oye por `role="alert"`. Con movimiento reducido, quieto.
 */
export function FormError({ message, className, children }: { message: string; className?: string; children?: ReactNode }) {
  const reduce = useReducedMotion();
  return (
    <motion.p
      key={message}
      className={className}
      role="alert"
      data-fx={reduce ? undefined : 'shake'}
      animate={reduce ? undefined : { x: [0, -6, 6, -4, 4, 0] }}
      transition={{ duration: DUR.response * 0.75 }}
    >
      {children ?? message}
    </motion.p>
  );
}
