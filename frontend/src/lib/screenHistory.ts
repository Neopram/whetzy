/**
 * «Atrás» dentro de la app (PR B, 2026-10-16). Las pantallas viven en el store
 * (`setScreen`), sin URL: «atrás» salía de la app entera desde cualquier
 * pantalla, y recargar en Rutas o Ranking volvía siempre a Hoy.
 *
 * - Las pantallas principales tienen su ruta (`SCREEN_PATHS`); cambiar de
 *   pantalla apila una entrada en el historial y «atrás» vuelve a la anterior.
 * - Las inmersivas (quiz, examen, lección…) apilan una entrada con la URL `/`:
 *   recargar en mitad de una lleva a Hoy, porque su estado no se guarda.
 * - En quiz y exámenes (`BACK_GUARDED`) «atrás» no sale: se repone la entrada
 *   y se avisa a la pantalla con `BACK_EVENT`, que decide (el quiz abre su
 *   diálogo de salida).
 * - Salir de una inmersiva por su propia UI hacia la pantalla de la que vino
 *   retrocede el historial en vez de apilar: si no, «atrás» desde Hoy volvería
 *   a un quiz que ya no existe.
 */
import { useEffect, useRef } from 'react';
import { useAppStore, type Screen } from '../stores/useAppStore';
import { isImmersiveScreen } from './immersiveScreens';

export const SCREEN_PATHS: Partial<Record<Screen, string>> = {
  home: '/',
  tracks: '/tracks',
  league: '/ranking',
  profile: '/profile',
  stats: '/stats',
  wallet: '/wallet',
  marketplace: '/catalog',
};

export const BACK_GUARDED: ReadonlySet<Screen> = new Set<Screen>(['quiz', 'mockexam', 'trackexam']);

/** Evento de ventana que recibe la pantalla protegida cuando se pulsa «atrás». */
export const BACK_EVENT = 'whetzy:back';

interface Entry {
  whetzyScreen: Screen;
  prev?: Screen;
}

export function screenForPath(pathname: string): Screen | null {
  const p = pathname.length > 1 ? pathname.replace(/\/+$/, '') : pathname;
  const hit = (Object.entries(SCREEN_PATHS) as [Screen, string][]).find(([, path]) => path === p);
  return hit ? hit[0] : null;
}

export function pathForScreen(screen: Screen): string {
  return SCREEN_PATHS[screen] ?? '/';
}

function entryOf(state: unknown): Entry | null {
  return state && typeof state === 'object' && 'whetzyScreen' in state ? (state as Entry) : null;
}

/** Ata la pantalla del store al historial del navegador mientras `enabled`
 *  (sesión abierta y sin onboarding). */
export function useScreenHistory(enabled: boolean): void {
  const currentScreen = useAppStore((s) => s.currentScreen);
  const started = useRef(false);

  // Arranque: la URL elige la pantalla (recargar en /ranking abre Ranking).
  useEffect(() => {
    if (!enabled || started.current) return;
    started.current = true;
    // «/» no pide ninguna pantalla en concreto: manda la que la app ya eligió
    // (43.3: el onboarding abre la prueba de nivel justo antes de arrancar
    // esto, y antes se pisaba con Hoy). `currentScreen` no se persiste, así
    // que al cargar la página sigue siendo 'home'.
    const fromUrl = screenForPath(window.location.pathname);
    const screen = fromUrl && fromUrl !== 'home' ? fromUrl : useAppStore.getState().currentScreen;
    window.history.replaceState({ whetzyScreen: screen } satisfies Entry, '', pathForScreen(screen) + window.location.search);
    if (screen !== useAppStore.getState().currentScreen) useAppStore.getState().setScreen(screen);
  }, [enabled]);

  // Cada cambio de pantalla hecho por la app (no por «atrás») se apunta.
  useEffect(() => {
    if (!enabled || !started.current) return;
    const top = entryOf(window.history.state);
    if (top?.whetzyScreen === currentScreen) return;
    if (top && isImmersiveScreen(top.whetzyScreen)) {
      if (top.prev === currentScreen) {
        window.history.back();
        return;
      }
      window.history.replaceState({ whetzyScreen: currentScreen, prev: top.prev } satisfies Entry, '', pathForScreen(currentScreen));
      return;
    }
    window.history.pushState({ whetzyScreen: currentScreen, prev: top?.whetzyScreen } satisfies Entry, '', pathForScreen(currentScreen));
  }, [enabled, currentScreen]);

  // «Atrás» y «adelante» del navegador (y el botón atrás de Android).
  useEffect(() => {
    if (!enabled) return;
    const onPop = (e: PopStateEvent) => {
      const { currentScreen: here, setScreen } = useAppStore.getState();
      if (BACK_GUARDED.has(here)) {
        const prev = entryOf(e.state)?.whetzyScreen;
        window.history.pushState({ whetzyScreen: here, prev } satisfies Entry, '', '/');
        window.dispatchEvent(new Event(BACK_EVENT));
        return;
      }
      let target = entryOf(e.state)?.whetzyScreen ?? screenForPath(window.location.pathname) ?? 'home';
      if (isImmersiveScreen(target) && target !== here) {
        // Una inmersiva ya cerrada: su estado no existe. Se queda en la
        // pantalla de su URL.
        target = screenForPath(window.location.pathname) ?? 'home';
        window.history.replaceState({ whetzyScreen: target } satisfies Entry, '', pathForScreen(target));
      }
      if (target !== here) setScreen(target);
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, [enabled]);
}

/** La pantalla protegida decide qué hace «atrás» (abrir su diálogo, avisar…).
 *  El manejador se lee del último render: el listener se engancha una vez. */
export function useBackGuard(handler: () => void): void {
  const ref = useRef(handler);
  useEffect(() => {
    ref.current = handler;
  });
  useEffect(() => {
    const onBack = () => ref.current();
    window.addEventListener(BACK_EVENT, onBack);
    return () => window.removeEventListener(BACK_EVENT, onBack);
  }, []);
}
