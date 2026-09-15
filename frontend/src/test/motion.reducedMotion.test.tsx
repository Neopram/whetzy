/**
 * 17.6(b) — prefers-reduced-motion contra framer-motion.
 *
 * El bloque de `global.css` (`animation-duration: 0.01ms !important`) apaga las
 * animaciones CSS y no toca framer-motion: framer escribe `transform` en linea
 * desde JS, fuera del alcance de cualquier regla de hoja de estilo. Con
 * `lib/motion.ts` en el arbol hay animaciones `repeat: Infinity` (el pulso del
 * nodo actual del mapa, el parpadeo de la racha), asi que sin
 * `<MotionConfig reducedMotion="user">` la app se mueve, en bucle, para quien
 * pidio explicitamente que no lo hiciera.
 *
 * Este test comprueba lo unico que importa del contrato: bajo
 * `prefers-reduced-motion: reduce`, una animacion de transform no llega a
 * escribir un transform, y la misma animacion SIN el wrapper si lo escribe
 * (la segunda mitad es la que le da dientes: si `MotionConfig` dejara de hacer
 * efecto, el primer caso pasaria por accidente al pasar tambien el segundo).
 */
import { render, waitFor } from '@testing-library/react';
import { motion, MotionConfig } from 'framer-motion';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { pulseVariants } from '../lib/motion';

function mockPrefersReducedMotion(reduce: boolean) {
  vi.stubGlobal(
    'matchMedia',
    (query: string) =>
      ({
        matches: query.includes('prefers-reduced-motion') ? reduce : false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }) as unknown as MediaQueryList,
  );
}

/** El nodo "actual" del mapa de progreso: escala en bucle, para siempre. */
function PulsingNode() {
  return (
    <motion.div data-testid="node" variants={pulseVariants} animate="animate">
      nodo
    </motion.div>
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('prefers-reduced-motion', () => {
  it('no anima transform cuando el usuario pide movimiento reducido', async () => {
    mockPrefersReducedMotion(true);

    const { getByTestId } = render(
      <MotionConfig reducedMotion="user">
        <PulsingNode />
      </MotionConfig>,
    );

    // Le damos tiempo de sobra: la animacion dura 1,8 s y repite, asi que si
    // fuera a moverse ya habria escrito un transform mucho antes.
    await new Promise(r => setTimeout(r, 120));

    const node = getByTestId('node');
    expect(node.style.transform === '' || node.style.transform === 'none').toBe(true);
  });

  it('si anima transform cuando el usuario no pide nada (el test anterior tiene dientes)', async () => {
    mockPrefersReducedMotion(false);

    const { getByTestId } = render(
      <MotionConfig reducedMotion="never">
        <PulsingNode />
      </MotionConfig>,
    );

    const node = getByTestId('node');
    await waitFor(
      () => {
        expect(node.style.transform).not.toBe('');
      },
      { timeout: 1000 },
    );
  });
});
