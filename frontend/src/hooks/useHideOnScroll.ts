import { useEffect, useRef, useState } from 'react';

/**
 * Esconde una barra fija al bajar por la página y la devuelve al subir.
 *
 * La barra inferior (5 pestañas, 64 px + zona segura) tapaba siempre el pie de
 * cada pantalla; en móvil y en ventanas bajas se veía mucha menos página de la
 * que había. Patrón de las apps nativas: bajar = leer, la barra se aparta;
 * subir, volver arriba o llegar al final = navegar, la barra vuelve.
 *
 * `resetKey` (la pantalla actual) la devuelve al cambiar de pantalla, para que
 * nunca se llegue a una pantalla nueva sin navegación visible.
 */
export function useHideOnScroll(resetKey: unknown, threshold = 8): boolean {
  const [hidden, setHidden] = useState(false);
  const lastY = useRef(0);

  useEffect(() => {
    setHidden(false);
    lastY.current = window.scrollY;
  }, [resetKey]);

  useEffect(() => {
    let frame = 0;
    const onScroll = () => {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        const y = window.scrollY;
        const delta = y - lastY.current;
        const atBottom = window.innerHeight + y >= document.documentElement.scrollHeight - 4;
        if (y < 64 || atBottom) setHidden(false);
        else if (delta > threshold) setHidden(true);
        else if (delta < -threshold) setHidden(false);
        if (Math.abs(delta) > threshold) lastY.current = y;
      });
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [threshold]);

  return hidden;
}
