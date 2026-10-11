/**
 * `email.py` manda el enlace de verificación a `/verify-email?token=...`,
 * pero no había ninguna página en ese camino -- quien lo pulsara no llegaba
 * a ningún sitio que llamara a `POST /auth/verify-email` (0.2).
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { VerifyEmailPage } from '../pages/VerifyEmailPage';
import { auth } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: { ...actual.auth, verifyEmail: vi.fn(), resendVerification: vi.fn() },
  };
});

const verifyEmail = auth.verifyEmail as unknown as ReturnType<typeof vi.fn>;
const resendVerification = auth.resendVerification as unknown as ReturnType<typeof vi.fn>;

afterEach(() => {
  cleanup();
  verifyEmail.mockReset();
  resendVerification.mockReset();
});

describe('VerifyEmailPage — consume el enlace del correo (0.2)', () => {
  it('calls verifyEmail with the token from the URL and shows success', async () => {
    await i18n.changeLanguage('es');
    verifyEmail.mockResolvedValueOnce({ message: 'ok' });
    render(<VerifyEmailPage token="tok-123" />);

    await waitFor(() => expect(screen.getByText(/Email verificado/)).toBeInTheDocument());
    expect(verifyEmail).toHaveBeenCalledWith('tok-123');
  });

  it('shows an invalid/expired message and a resend form on failure', async () => {
    await i18n.changeLanguage('es');
    verifyEmail.mockRejectedValueOnce(new Error('Invalid or expired verification link'));
    render(<VerifyEmailPage token="stale-token" />);

    await waitFor(() => expect(screen.getByText(/no es válido o ha caducado/)).toBeInTheDocument());
    expect(screen.getByPlaceholderText('Tu email')).toBeInTheDocument();
  });

  it('an empty token never calls the backend and goes straight to the resend form', async () => {
    await i18n.changeLanguage('es');
    render(<VerifyEmailPage token="" />);

    await waitFor(() => expect(screen.getByText(/no es válido o ha caducado/)).toBeInTheDocument());
    expect(verifyEmail).not.toHaveBeenCalled();
  });

  it('resending always shows the same honest message, win or lose (no email enumeration)', async () => {
    await i18n.changeLanguage('es');
    verifyEmail.mockRejectedValueOnce(new Error('Invalid or expired verification link'));
    resendVerification.mockResolvedValueOnce({ message: 'ok' });
    render(<VerifyEmailPage token="stale-token" />);

    await waitFor(() => screen.getByLabelText('Tu email'));
    fireEvent.change(screen.getByLabelText('Tu email'), { target: { value: 'a@b.test' } });
    fireEvent.click(screen.getByText('Enviar de nuevo'));

    await waitFor(() =>
      expect(screen.getByText(/te hemos enviado un nuevo enlace/)).toBeInTheDocument()
    );
    expect(resendVerification).toHaveBeenCalledWith('a@b.test');
  });
});
