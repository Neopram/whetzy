/**
 * 46.15 bloque A (docs/PLAN_UI_AVANZADA.md §7.5): las pantallas de entrada.
 * - Un error de formulario tiembla (nivel 0, sin sonido) y vuelve a temblar
 *   si cambia; el lector de pantalla lo oye por `role="alert"`.
 * - Verificar el correo y «te enviamos el enlace» dibujan un check cuando el
 *   servidor lo confirma.
 * - El alta cambia de paso con un desplazamiento lateral.
 * Con movimiento reducido no tiembla, no se dibuja y no se desplaza nada.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { AuthScreen } from '../pages/AuthScreen';
import { ForgotPasswordPage } from '../pages/ForgotPasswordPage';
import { VerifyEmailPage } from '../pages/VerifyEmailPage';
import OnboardingScreen from '../pages/OnboardingScreen';
import { ApiError, auth, content } from '../services/api';

let reduce = false;
vi.mock('framer-motion', async (importOriginal) => {
  const actual = await importOriginal<typeof import('framer-motion')>();
  return { ...actual, useReducedMotion: () => reduce };
});
vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: { ...actual.auth, oauthProviders: vi.fn(), login: vi.fn(), register: vi.fn(), requestPasswordReset: vi.fn(), verifyEmail: vi.fn(), resendVerification: vi.fn() },
    content: { ...actual.content, tracks: vi.fn() },
  };
});

beforeEach(async () => {
  vi.clearAllMocks();
  reduce = false;
  await i18n.changeLanguage('es');
  (auth.oauthProviders as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ providers: [] });
  (content.tracks as unknown as ReturnType<typeof vi.fn>).mockResolvedValue([]);
  window.history.replaceState(null, '', '/auth');
});
afterEach(cleanup);

async function registerTaken() {
  render(<AuthScreen />);
  (auth.register as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(new ApiError('email_taken', 409, 'email_taken'));
  fireEvent.change(screen.getByLabelText(i18n.t('auth.nameLabel')), { target: { value: 'María' } });
  fireEvent.change(screen.getByLabelText(i18n.t('auth.usernameLabel')), { target: { value: 'maria_46' } });
  fireEvent.change(screen.getByLabelText(i18n.t('auth.emailLabel')), { target: { value: 'maria@example.com' } });
  fireEvent.change(screen.getByLabelText(i18n.t('auth.passwordLabel')), { target: { value: 'Str0ng!Pass' } });
  fireEvent.click(screen.getByRole('checkbox'));
  fireEvent.click(screen.getByRole('button', { name: i18n.t('auth.registerCta') }));
  return screen.findByRole('alert');
}

describe('Entrada (46.15 A)', () => {
  it('el error del formulario tiembla y se anuncia', async () => {
    const alert = await registerTaken();
    expect(alert).toHaveAttribute('data-fx', 'shake');
  });

  it('con movimiento reducido el error no tiembla', async () => {
    reduce = true;
    const alert = await registerTaken();
    expect(alert).not.toHaveAttribute('data-fx');
  });

  it('verificar el correo: check dibujado cuando el servidor lo confirma', async () => {
    (auth.verifyEmail as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ message: 'ok' });
    render(<VerifyEmailPage token="tok" />);
    await waitFor(() => expect(screen.getByTestId('drawn-check')).toBeInTheDocument());
    expect(screen.getByTestId('drawn-check')).toHaveAttribute('data-fx', 'draw');
  });

  it('enlace enviado: check dibujado; con movimiento reducido, estático', async () => {
    (auth.requestPasswordReset as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({});
    reduce = true;
    render(<ForgotPasswordPage onBack={() => {}} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'a@b.co' } });
    fireEvent.submit(screen.getByRole('textbox').closest('form')!);
    expect(await screen.findByTestId('drawn-check')).not.toHaveAttribute('data-fx');
  });

  it('el alta cambia de paso con desplazamiento', async () => {
    render(<OnboardingScreen onDone={() => {}} />);
    expect(await screen.findByTestId('onboarding-step')).toHaveAttribute('data-fx', 'slide');
  });
});
