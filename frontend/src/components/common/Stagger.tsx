import { Children, type ReactNode } from 'react';
import { motion, useReducedMotion, type HTMLMotionProps, type Variants } from 'framer-motion';
import { DUR } from '../../lib/motion';

/**
 * Listas que entran escalonadas (46.15 D; plan §7.5). Un solo patrón para
 * Perfil, Estadísticas, Cartera, el informe y el perfil público, en vez de
 * repetir las variantes en cada pantalla. Con movimiento reducido, la lista
 * aparece entera y sin `data-enter`.
 */
/**
 * Retraso entre elementos: 0,04 s, salvo en listas largas, donde el total se
 * recorta a `DUR.response`. Con las 35 rutas del catálogo, 0,04 s fijos eran
 * 1,4 s esperando a la última tarjeta (y axe medía tarjetas a medio aparecer).
 */
export function staggerFor(count: number): number {
  return Math.min(0.04, DUR.response / Math.max(count, 1));
}
const ITEM: Variants = {
  hidden: { opacity: 0, y: 6 },
  shown: { opacity: 1, y: 0, transition: { duration: DUR.response / 2 } },
};

type ListTag = 'ul' | 'ol' | 'div';
type ItemTag = 'li' | 'div';

export function StaggerList({
  as = 'ul', children, ...rest
}: { as?: ListTag; children: ReactNode } & Omit<HTMLMotionProps<'ul'>, 'variants' | 'initial' | 'animate' | 'children'>) {
  const reduce = useReducedMotion();
  const Tag = motion[as] as typeof motion.ul;
  return (
    <Tag
      {...rest}
      data-enter={reduce ? undefined : 'stagger'}
      variants={{ hidden: {}, shown: { transition: { staggerChildren: staggerFor(Children.count(children)) } } }}
      initial={reduce ? false : 'hidden'}
      animate="shown"
    >
      {children}
    </Tag>
  );
}

export function StaggerItem({
  as = 'li', children, ...rest
}: { as?: ItemTag; children: ReactNode } & Omit<HTMLMotionProps<'li'>, 'variants' | 'children'>) {
  const Tag = motion[as] as typeof motion.li;
  return <Tag {...rest} variants={ITEM}>{children}</Tag>;
}
