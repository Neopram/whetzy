/**
 * 24.8: el perfil público es privado por defecto. El interruptor de Perfil solo
 * existe si el servidor permite perfiles públicos, guarda en el servidor y se
 * deshace si falla.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { ProfileScreen } from '../pages/ProfileScreen';
import { useAppStore } from '../stores/useAppStore';
import { auth } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    gamification: { ...actual.gamification, badges: vi.fn().mockResolvedValue([]) },
    auth: { ...actual.auth, updateMe: vi.fn() },
    billing: {
      ...actual.billing,
      subscription: vi.fn().mockResolvedValue(null),
      paddleConfig: vi.fn().mockResolvedValue({ enabled: false, environment: 'production', client_token: '', prices: {} }),
    },
  };
});

const updateMe = auth.updateMe as unknown as ReturnType<typeof vi.fn>;

beforeEach(async () => {
  await i18n.changeLanguage('es');
  updateMe.mockReset();
});
afterEach(() => {
  cleanup();
  useAppStore.getState().updateUser({ publicProfileOptIn: false, publicProfilesEnabled: false });
});

describe('Perfil — perfil público', () => {
  it('no se ofrece si el servidor no publica perfiles', () => {
    useAppStore.getState().updateUser({ publicProfilesEnabled: false });
    render(<ProfileScreen />);
    expect(screen.queryByRole('switch', { name: 'Perfil público' })).toBeNull();
  });

  it('empieza apagado y explica qué se enseña y que se quita cuando quieras', () => {
    useAppStore.getState().updateUser({ publicProfilesEnabled: true, username: 'ada' });
    render(<ProfileScreen />);
    const sw = screen.getByRole('switch', { name: 'Perfil público' });
    expect(sw).toHaveAttribute('aria-checked', 'false');
    expect(screen.getByText(/whetzy\.com\/u\/ada/)).toBeInTheDocument();
    expect(screen.getByText(/Puedes quitarlo en cualquier momento/)).toBeInTheDocument();
  });

  it('activarlo lo guarda en el servidor y, si falla, vuelve atrás', async () => {
    useAppStore.getState().updateUser({ publicProfilesEnabled: true });
    render(<ProfileScreen />);
    const sw = screen.getByRole('switch', { name: 'Perfil público' });

    updateMe.mockResolvedValueOnce({});
    fireEvent.click(sw);
    await waitFor(() => expect(updateMe).toHaveBeenCalledWith({ public_profile_opt_in: true }));
    expect(sw).toHaveAttribute('aria-checked', 'true');

    updateMe.mockRejectedValueOnce(new Error('offline'));
    fireEvent.click(sw);
    await waitFor(() => expect(updateMe).toHaveBeenLastCalledWith({ public_profile_opt_in: false }));
    await waitFor(() => expect(sw).toHaveAttribute('aria-checked', 'true'));
  });

  it('en inglés el texto también es nativo', async () => {
    await i18n.changeLanguage('en');
    useAppStore.getState().updateUser({ publicProfilesEnabled: true });
    render(<ProfileScreen />);
    expect(screen.getByRole('switch', { name: 'Public profile' })).toBeInTheDocument();
    expect(screen.getByText(/You can turn it off at any time/)).toBeInTheDocument();
  });
});
