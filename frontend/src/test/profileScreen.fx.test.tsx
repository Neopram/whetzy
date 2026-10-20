/**
 * 46.2: los interruptores de sonido y vibración de Perfil cambian la
 * preferencia que lee `lib/feedbackFx.ts`. Textos en `producto` (ES/EN).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { ProfileScreen } from '../pages/ProfileScreen';
import { useAppStore } from '../stores/useAppStore';
import * as fx from '../lib/feedbackFx';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    gamification: { ...actual.gamification, badges: vi.fn().mockResolvedValue([]) },
    billing: {
      ...actual.billing,
      subscription: vi.fn().mockResolvedValue({ is_premium: false }),
      paddleConfig: vi.fn().mockResolvedValue({ enabled: false, prices: {} }),
    },
  };
});

beforeEach(() => {
  useAppStore.setState({ soundEnabled: false, hapticEnabled: true });
});
afterEach(cleanup);

describe('Perfil — sonido y vibración (46.2)', () => {
  it('ES: «Sonidos» arranca apagado y se enciende; «Vibración» se apaga', async () => {
    await i18n.changeLanguage('es');
    render(<ProfileScreen />);
    const sound = screen.getByRole('switch', { name: 'Sonidos' });
    const haptics = screen.getByRole('switch', { name: 'Vibración' });
    expect(sound).toHaveAttribute('aria-checked', 'false');
    expect(haptics).toHaveAttribute('aria-checked', 'true');

    fireEvent.click(sound);
    fireEvent.click(haptics);
    expect(useAppStore.getState()).toMatchObject({ soundEnabled: true, hapticEnabled: false });
    expect(screen.getByRole('switch', { name: 'Sonidos' })).toHaveAttribute('aria-checked', 'true');
  });

  it('46.2c: encender un interruptor da una muestra en ese toque; apagarlo, no', async () => {
    await i18n.changeLanguage('es');
    const preview = vi.spyOn(fx, 'preview');
    render(<ProfileScreen />);
    fireEvent.click(screen.getByRole('switch', { name: 'Sonidos' })); // apagado → encendido
    // Que suene lo prueban los tests de feedbackFx (jsdom no tiene AudioContext).
    expect(preview).toHaveBeenLastCalledWith('sound');
    fireEvent.click(screen.getByRole('switch', { name: 'Vibración' })); // encendido → apagado
    expect(preview).toHaveBeenLastCalledWith('haptic');
    expect(preview).toHaveLastReturnedWith(false);
    preview.mockRestore();
  });

  it('EN: los mismos interruptores con su texto en inglés', async () => {
    await i18n.changeLanguage('en');
    render(<ProfileScreen />);
    expect(screen.getByRole('switch', { name: 'Sounds' })).toBeInTheDocument();
    expect(screen.getByRole('switch', { name: 'Vibration' })).toBeInTheDocument();
    await i18n.changeLanguage('es');
  });
});
