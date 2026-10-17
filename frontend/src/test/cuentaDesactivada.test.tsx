/**
 * 2026-10-17, iPhone del dueño: borró su cuenta desde `/delete-account` y, al
 * pulsar «atrás», volvía a Hoy como si nada. El servidor ya la había
 * desactivado (`DELETE /auth/me/account` 200 y después todo 403 «Inactive
 * user» en los logs de Railway), pero la app solo cerraba sesión con un 401 y
 * la pantalla de borrar no tocaba el estado local.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { progress, setOnSessionExpired } from '../services/api';
import { DEFAULT_USER_ID, useAppStore } from '../stores/useAppStore';
import { DeleteAccountScreen } from '../pages/DeleteAccountScreen';

function responder(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

afterEach(() => {
  setOnSessionExpired(null);
  vi.unstubAllGlobals();
  cleanup();
});

describe('403 «Inactive user»: la sesión se da por cerrada', () => {
  it('avisa a la app, igual que un 401 definitivo', async () => {
    const expirada = vi.fn();
    setOnSessionExpired(expirada);
    vi.stubGlobal('fetch', vi.fn(async () => responder(403, { detail: 'Inactive user' })));
    await expect(progress.dashboard()).rejects.toMatchObject({ status: 403 });
    expect(expirada).toHaveBeenCalledTimes(1);
  });

  it('un 403 por otra causa no cierra la sesión', async () => {
    const expirada = vi.fn();
    setOnSessionExpired(expirada);
    vi.stubGlobal('fetch', vi.fn(async () => responder(403, { detail: 'Admin access required' })));
    await expect(progress.dashboard()).rejects.toMatchObject({ status: 403 });
    expect(expirada).not.toHaveBeenCalled();
  });

  it('el propio /auth/logout no vuelve a disparar el aviso (sin bucle)', async () => {
    const expirada = vi.fn();
    setOnSessionExpired(expirada);
    vi.stubGlobal('fetch', vi.fn(async () => responder(403, { detail: 'Inactive user' })));
    const { logout } = await import('../services/api');
    await logout();
    expect(expirada).not.toHaveBeenCalled();
  });
});

describe('Borrar cuenta: al terminar, la sesión local se cierra', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('es');
    useAppStore.setState({ user: { ...useAppStore.getState().user, id: 'u-1', name: 'Dueño' } });
  });

  it('tras el DELETE con 200 el usuario guardado vuelve al anónimo', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string, init?: RequestInit) => {
        if (String(url).endsWith('/auth/login')) return responder(200, { access_token: 'a', refresh_token: 'r' });
        if (String(url).endsWith('/auth/me/account') && init?.method === 'DELETE') {
          return responder(200, { message: 'ok', purge_after: '2026-11-16T00:00:00Z' });
        }
        return responder(403, { detail: 'Inactive user' });
      }),
    );
    render(<DeleteAccountScreen />);
    fireEvent.change(screen.getByLabelText(i18n.t('deleteAccount.email')), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText(i18n.t('deleteAccount.password')), { target: { value: 'secreto-123' } });
    fireEvent.click(screen.getByRole('button', { name: i18n.t('deleteAccount.continue') }));
    const confirmar = await screen.findByLabelText(
      i18n.t('deleteAccount.confirmLabel', { word: i18n.t('deleteAccount.confirmWord') }),
    );
    fireEvent.change(confirmar, { target: { value: i18n.t('deleteAccount.confirmWord') } });
    fireEvent.click(screen.getByRole('button', { name: i18n.t('deleteAccount.deleteCta') }));
    await screen.findByText(i18n.t('deleteAccount.doneTitle'));
    await waitFor(() => expect(useAppStore.getState().user.id).toBe(DEFAULT_USER_ID));
  });
});
