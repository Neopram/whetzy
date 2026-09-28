/**
 * 23.1: `ForgotPasswordPage.tsx` and `ResetPasswordPage.tsx` never called
 * `useTranslation` — every string was hardcoded Spanish, so an English-mode
 * user hit a page in the wrong language with no fallback at all (worse than
 * a silent fallback: it never even tried the other language).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { ForgotPasswordPage } from '../pages/ForgotPasswordPage';
import { auth } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, auth: { ...actual.auth, requestPasswordReset: vi.fn() } };
});

const requestPasswordReset = auth.requestPasswordReset as unknown as ReturnType<typeof vi.fn>;

beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);

describe('ForgotPasswordPage — ES y EN nativos (23.1)', () => {
  it('ES: título y botón en español', async () => {
    await i18n.changeLanguage('es');
    render(<ForgotPasswordPage onBack={() => {}} />);
    expect(screen.getByText('¿Olvidaste tu contraseña?')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Enviar' })).toBeInTheDocument();
  });

  it('EN: same page in English, not a leftover Spanish string', async () => {
    await i18n.changeLanguage('en');
    render(<ForgotPasswordPage onBack={() => {}} />);
    expect(screen.getByText('Forgot your password?')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send' })).toBeInTheDocument();
    expect(screen.queryByText('¿Olvidaste tu contraseña?')).not.toBeInTheDocument();
  });

  it('EN: the "check your email" screen is English too, including the interpolated address', async () => {
    await i18n.changeLanguage('en');
    requestPasswordReset.mockResolvedValue({ message: 'ok' });
    render(<ForgotPasswordPage onBack={() => {}} />);

    fireEvent.change(screen.getByPlaceholderText('you@email.com'), {
      target: { value: 'shots@example.com' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Send' }));

    expect(await screen.findByText('Check your email')).toBeInTheDocument();
    expect(screen.getByText(/If shots@example\.com has an account/)).toBeInTheDocument();
  });
});
