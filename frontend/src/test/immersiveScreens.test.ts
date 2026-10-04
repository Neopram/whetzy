/**
 * `IMMERSIVE_SCREENS` (0.9) es lo que protege a quiz/examen/lección de
 * perderse por un toque o un gesto de sobra: oculta la barra inferior y, con
 * el fix de App.tsx, también desactiva el swipe global de ir a casa/mercado.
 * 'duels' faltaba del conjunto — un duelo en vivo se podía abandonar con un
 * solo toque en la barra inferior, sin confirmación ni aviso de ningún tipo
 * (DuelScreen no tiene ni diálogo de salida propio).
 */
import { describe, expect, it } from 'vitest';
import { IMMERSIVE_SCREENS, isImmersiveScreen, navigationTargetForSwipe } from '../lib/immersiveScreens';

describe('IMMERSIVE_SCREENS (0.9)', () => {
  it('incluye duels: un duelo en vivo es "una tarea, una salida" igual que un examen', () => {
    expect(IMMERSIVE_SCREENS.has('duels')).toBe(true);
    expect(isImmersiveScreen('duels')).toBe(true);
  });

  it('sigue cubriendo los exámenes y lecciones ya protegidos', () => {
    for (const screen of ['quiz', 'placement', 'mockexam', 'trackexam', 'lesson', 'readiness']) {
      expect(isImmersiveScreen(screen)).toBe(true);
    }
  });

  it('home y las pantallas de navegación libre no son inmersivas', () => {
    for (const screen of ['home', 'tracks', 'stats', 'league', 'profile', 'marketplace']) {
      expect(isImmersiveScreen(screen)).toBe(false);
    }
  });
});

describe('navigationTargetForSwipe (0.9 — el swipe global no debe saltar fuera de un examen/duelo)', () => {
  it('un swipe a la derecha desde una pantalla normal va a casa', () => {
    expect(navigationTargetForSwipe('right', 'tracks')).toBe('home');
  });

  it('un swipe a la izquierda desde una pantalla normal va al mercado', () => {
    expect(navigationTargetForSwipe('left', 'tracks')).toBe('marketplace');
  });

  it('no navega si ya está en el destino', () => {
    expect(navigationTargetForSwipe('right', 'home')).toBeNull();
    expect(navigationTargetForSwipe('left', 'marketplace')).toBeNull();
  });

  it('no navega desde una pantalla inmersiva — ni a casa ni al mercado', () => {
    for (const screen of ['quiz', 'mockexam', 'duels', 'lesson']) {
      expect(navigationTargetForSwipe('right', screen)).toBeNull();
      expect(navigationTargetForSwipe('left', screen)).toBeNull();
    }
  });
});
