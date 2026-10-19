/**
 * 45.3 (ADR-66 E4): mientras el correo no esté verificado, la app lo dice con
 * una franja en el armazón: «Te enviamos un enlace a fe***@gmail.com ·
 * Reenviar · ×». Antes ningún fichero de `frontend/src` (sin contar tests)
 * leía `email_verified`, y `UserRead` no lo traía aunque `/auth/me` lo manda.
 */
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import i18n from '../i18n';
import { VerifyEmailBanner, maskEmail } from '../components/common/VerifyEmailBanner';
import { DEFAULT_USER_ID, useAppStore } from '../stores/useAppStore';
import { auth, type UserRead } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, auth: { ...actual.auth, me: vi.fn(), resendVerification: vi.fn() } };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;

const BASE: UserRead = {
  id: 'u1', email: 'federico@gmail.com', username: 'fede', display_name: 'Fede', language: 'es',
  avatar_emoji: '🙂', level: 1, total_xp: 0, current_streak: 0, max_streak: 0,
  streak_freeze_available: 1, last_active: null, created_at: '2026-10-17T00:00:00Z',
  is_premium: false,
};

async function signedIn(over: Partial<UserRead>) {
  m(auth.me).mockResolvedValue({ ...BASE, ...over });
  await useAppStore.getState().hydrateFromApi();
}

const banner = () => screen.queryByTestId('verify-email-banner');

beforeEach(async () => {
  vi.clearAllMocks();
  m(auth.resendVerification).mockResolvedValue({ message: 'ok' });
  sessionStorage.clear();
  await i18n.changeLanguage('es');
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  useAppStore.getState().signOut();
});

describe('maskEmail', () => {
  it('deja ver las dos primeras letras y el dominio', () => {
    expect(maskEmail('federico@gmail.com')).toBe('fe***@gmail.com');
    expect(maskEmail('a@b.co')).toBe('a***@b.co');
    expect(maskEmail('sin-arroba')).toBe('sin-arroba');
  });
});

describe('VerifyEmailBanner (45.3)', () => {
  it('el store lee email_verified de /auth/me', async () => {
    await signedIn({ email_verified: false });
    expect(useAppStore.getState().user.emailVerified).toBe(false);
    await signedIn({ email_verified: true });
    expect(useAppStore.getState().user.emailVerified).toBe(true);
  });

  it('aparece sin verificar, con el email enmascarado', async () => {
    await signedIn({ email_verified: false });
    render(<VerifyEmailBanner />);
    expect(banner()).not.toBeNull();
    expect(banner()!.textContent).toContain('fe***@gmail.com');
    expect(banner()!.textContent).not.toContain('federico@gmail.com');
  });

  it('no aparece verificado, ni sin sesión', async () => {
    await signedIn({ email_verified: true });
    render(<VerifyEmailBanner />);
    expect(banner()).toBeNull();
    cleanup();
    useAppStore.getState().signOut();
    render(<VerifyEmailBanner />);
    expect(banner()).toBeNull();
    // El perfil de muestra (antes de hidratar) nunca la enseña, diga lo que diga.
    cleanup();
    useAppStore.setState((st) => ({ user: { ...st.user, emailVerified: false, email: 'demo@example.com' } }));
    expect(useAppStore.getState().user.id).toBe(DEFAULT_USER_ID);
    render(<VerifyEmailBanner />);
    expect(banner()).toBeNull();
  });

  it('«Reenviar» llama al endpoint con el email de la cuenta y espera 60 s', async () => {
    await signedIn({ email_verified: false });
    vi.useFakeTimers();
    render(<VerifyEmailBanner />);
    const resend = screen.getByRole('button', { name: i18n.t('verifyBanner.resend') });
    await act(async () => {
      fireEvent.click(resend);
    });
    expect(auth.resendVerification).toHaveBeenCalledWith('federico@gmail.com');
    expect(banner()!.textContent).toContain(i18n.t('verifyBanner.sent'));
    const waiting = screen.getByRole('button', { name: /60/ });
    expect(waiting).toBeDisabled();
    fireEvent.click(waiting);
    expect(auth.resendVerification).toHaveBeenCalledTimes(1);
    await act(async () => {
      vi.advanceTimersByTime(59_000);
    });
    expect(screen.getByRole('button', { name: /1/ })).toBeDisabled();
    await act(async () => {
      vi.advanceTimersByTime(1_000);
    });
    expect(screen.getByRole('button', { name: i18n.t('verifyBanner.resend') })).toBeEnabled();
  });

  it('si el reenvío falla lo dice y deja volver a intentarlo', async () => {
    await signedIn({ email_verified: false });
    m(auth.resendVerification).mockRejectedValue(new Error('429'));
    render(<VerifyEmailBanner />);
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: i18n.t('verifyBanner.resend') }));
    });
    expect(banner()!.textContent).toContain(i18n.t('verifyBanner.error'));
    expect(screen.getByRole('button', { name: i18n.t('verifyBanner.resend') })).toBeEnabled();
  });

  it('la × la oculta durante la sesión del navegador', async () => {
    await signedIn({ email_verified: false });
    render(<VerifyEmailBanner />);
    fireEvent.click(screen.getByRole('button', { name: i18n.t('verifyBanner.dismiss') }));
    expect(banner()).toBeNull();
    cleanup();
    render(<VerifyEmailBanner />);
    expect(banner()).toBeNull();
  });

  it('sale en inglés con la app en inglés', async () => {
    await signedIn({ email_verified: false, language: 'en' });
    await i18n.changeLanguage('en');
    render(<VerifyEmailBanner />);
    expect(i18n.t('verifyBanner.text', { email: 'x' })).not.toBe(i18n.t('verifyBanner.text', { email: 'x', lng: 'es' }));
    expect(banner()!.textContent).toContain(i18n.t('verifyBanner.text', { email: 'fe***@gmail.com' }));
  });
});
