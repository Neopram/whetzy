/**
 * «Atrás» dentro de la app (PR B, 2026-10-16). Sobre `master` 9e32059 las
 * pantallas no tenían URL: «atrás» salía de la app desde cualquiera, y
 * recargar en Ranking volvía a Hoy.
 */
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { BACK_EVENT, screenForPath, useScreenHistory } from '../lib/screenHistory';
import { useAppStore } from '../stores/useAppStore';

const store = () => useAppStore.getState();
const back = () => act(async () => { window.history.back(); await new Promise((r) => setTimeout(r, 30)); });

beforeEach(() => {
  window.history.replaceState(null, '', '/');
  act(() => useAppStore.setState({ currentScreen: 'home', previousScreen: 'home' }));
});
afterEach(cleanup);

describe('cada pantalla principal tiene su URL', () => {
  it('rutas conocidas y desconocidas', () => {
    expect(screenForPath('/')).toBe('home');
    expect(screenForPath('/tracks')).toBe('tracks');
    expect(screenForPath('/ranking/')).toBe('league');
    expect(screenForPath('/profile')).toBe('profile');
    expect(screenForPath('/nada')).toBeNull();
  });

  it('cambiar de pantalla apila una entrada y «atrás» vuelve a la anterior', async () => {
    renderHook(() => useScreenHistory(true));
    act(() => store().setScreen('tracks'));
    expect(window.location.pathname).toBe('/tracks');
    act(() => store().setScreen('league'));
    expect(window.location.pathname).toBe('/ranking');

    await back();
    await waitFor(() => expect(store().currentScreen).toBe('tracks'));
    expect(window.location.pathname).toBe('/tracks');
    await back();
    await waitFor(() => expect(store().currentScreen).toBe('home'));
  });

  it('al cargar en /ranking se abre Ranking', () => {
    window.history.replaceState(null, '', '/ranking');
    renderHook(() => useScreenHistory(true));
    expect(store().currentScreen).toBe('league');
  });

  it('en / se queda la pantalla que la app ya eligió (43.3: onboarding → prueba de nivel)', () => {
    // El onboarding llama a startPlacement justo antes de que el historial
    // arranque; la URL sigue en «/» y antes eso devolvía al alumno a Hoy.
    act(() => store().startPlacement('track01'));
    renderHook(() => useScreenHistory(true));
    expect(store().currentScreen).toBe('placement');
  });

  it('sin sesión no toca el historial', () => {
    renderHook(() => useScreenHistory(false));
    const before = window.history.length;
    act(() => store().setScreen('tracks'));
    expect(window.history.length).toBe(before);
    expect(window.location.pathname).toBe('/');
  });
});

describe('quiz y exámenes: «atrás» no sale sin preguntar', () => {
  it('en el quiz «atrás» avisa a la pantalla y se queda en el quiz', async () => {
    renderHook(() => useScreenHistory(true));
    act(() => store().setScreen('tracks'));
    act(() => store().setScreen('quiz'));
    // Recargar en mitad de una pantalla inmersiva lleva a Hoy.
    expect(window.location.pathname).toBe('/');

    let warned = 0;
    const onBack = () => { warned += 1; };
    window.addEventListener(BACK_EVENT, onBack);
    await back();
    window.removeEventListener(BACK_EVENT, onBack);

    expect(warned).toBe(1);
    expect(store().currentScreen).toBe('quiz');
  });

  it('salir del quiz por su botón no deja el quiz en el historial', async () => {
    renderHook(() => useScreenHistory(true));
    act(() => store().setScreen('tracks'));
    act(() => store().setScreen('quiz'));
    act(() => store().setScreen('tracks'));
    await new Promise((r) => setTimeout(r, 30));
    expect(window.location.pathname).toBe('/tracks');

    await back();
    await waitFor(() => expect(store().currentScreen).toBe('home'));
  });

  it('una lección (inmersiva sin diálogo) sí vuelve atrás', async () => {
    renderHook(() => useScreenHistory(true));
    act(() => store().setScreen('tracks'));
    act(() => store().setScreen('lesson'));
    await back();
    await waitFor(() => expect(store().currentScreen).toBe('tracks'));
  });
});
