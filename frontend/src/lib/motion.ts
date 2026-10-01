import type { Variants, Transition } from 'framer-motion';

// ── Spring presets ──────────────────────────────────────────────────────────
export const springs = {
  snappy:  { type: 'spring', stiffness: 420, damping: 30 } as Transition,
  bouncy:  { type: 'spring', stiffness: 300, damping: 18 } as Transition,
  gentle:  { type: 'spring', stiffness: 120, damping: 20 } as Transition,
  slow:    { type: 'spring', stiffness:  80, damping: 25 } as Transition,
  instant: { type: 'spring', stiffness: 600, damping: 35 } as Transition,
} as const;

// ── Page transitions ────────────────────────────────────────────────────────
export const pageVariants: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.22, ease: [0.4, 0, 0.2, 1] } },
  exit:    { opacity: 0, y: -6, transition: { duration: 0.15, ease: [0.4, 0, 1, 1] } },
};

// ── Slide-up (for quiz, lesson, modal-like screens) ────────────────────────
export const slideUpVariants: Variants = {
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0, transition: springs.gentle },
  exit:    { opacity: 0, y: 20, transition: { duration: 0.18 } },
};

// ── Card / item entrance ────────────────────────────────────────────────────
export const cardVariants: Variants = {
  initial: { opacity: 0, y: 16, scale: 0.97 },
  animate: { opacity: 1, y: 0,  scale: 1,    transition: springs.snappy },
  exit:    { opacity: 0, y:  8, scale: 0.97, transition: { duration: 0.12 } },
};

// ── Staggered list ──────────────────────────────────────────────────────────
export const listVariants: Variants = {
  animate: { transition: { staggerChildren: 0.055, delayChildren: 0.04 } },
};

export const listItemVariants: Variants = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0, transition: springs.snappy },
};

// ── Quiz feedback ───────────────────────────────────────────────────────────
export const correctVariants: Variants = {
  initial: { scale: 1 },
  animate: { scale: [1, 1.05, 0.97, 1.03, 1], transition: { duration: 0.44, ease: 'easeInOut' } },
};

export const wrongVariants: Variants = {
  initial: { x: 0 },
  animate: { x: [-7, 7, -5, 5, -3, 3, 0], transition: { duration: 0.38, ease: 'easeInOut' } },
};

// ── Button tap ──────────────────────────────────────────────────────────────
export const tapScale = { scale: 0.94 } as const;

// ── Modal ───────────────────────────────────────────────────────────────────
export const backdropVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.18 } },
  exit:    { opacity: 0, transition: { duration: 0.14 } },
};

export const modalVariants: Variants = {
  initial: { opacity: 0, scale: 0.87, y: 24 },
  animate: { opacity: 1, scale: 1,    y: 0,  transition: springs.bouncy },
  exit:    { opacity: 0, scale: 0.90, y: 12, transition: { duration: 0.16 } },
};

// ── Bottom sheet ────────────────────────────────────────────────────────────
export const sheetVariants: Variants = {
  initial: { y: '100%' },
  animate: { y: 0,      transition: springs.gentle },
  exit:    { y: '100%', transition: { duration: 0.2, ease: [0.4, 0, 1, 1] } },
};

// ── Pulsing glow (current node on learning path) ────────────────────────────
export const pulseVariants: Variants = {
  animate: {
    scale: [1, 1.06, 1],
    boxShadow: [
      '0 0 0 0px rgba(28,176,246,0.4)',
      '0 0 0 8px rgba(28,176,246,0)',
    ],
    transition: { duration: 1.8, repeat: Infinity, ease: 'easeInOut' },
  },
};

// ── Confetti burst (XP award) ───────────────────────────────────────────────
export const xpBurstVariants: Variants = {
  initial: { opacity: 0, scale: 0.3, y: 0 },
  animate: { opacity: [0, 1, 1, 0], scale: [0.3, 1.4, 1.2, 0.8], y: -40,
    transition: { duration: 0.65, ease: 'easeOut' } },
};
