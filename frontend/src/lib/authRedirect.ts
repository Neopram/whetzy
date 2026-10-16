import { useEffect } from 'react';
import { auth } from '../services/api';

/**
 * «Atrás» y la entrada a la app (2026-10-16). Con la sesión abierta, `/auth`,
 * `/login` y `/register` enseñaban el formulario de acceso como si no la
 * hubiera, y era justo donde caía «atrás» desde el panel.
 *
 * Pregunta a `/auth/me` (la cookie `whetzy_logged_in` no se ve entre dominios
 * en producción, 30.9) y, si hay sesión, sustituye la entrada del historial
 * por `next`: con `replace` la pantalla de acceso no queda detrás.
 */
export function useRedirectIfSignedIn(next: string): void {
  useEffect(() => {
    let cancelled = false;
    auth
      .me()
      .then(() => {
        if (!cancelled) window.location.replace(next);
      })
      .catch(() => {
        // 401 o red caída: no hay sesión que reanudar, se queda el formulario.
      });
    return () => {
      cancelled = true;
    };
  }, [next]);
}

/** La pestaña con la que abre el acceso: `/login` es para quien ya tiene cuenta. */
export function initialAuthMode(pathname: string): 'login' | 'register' {
  return pathname.replace(/\/+$/, '') === '/login' ? 'login' : 'register';
}
