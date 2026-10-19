/**
 * 45.4 (ADR-66 E5): la página del enlace del correo sale en el idioma del
 * enlace (`&lang=`) y lleva a donde toca: con sesión, «Continuar» a `/` (que
 * vuelve a pedir `/auth/me` y la franja de 45.3 desaparece); sin sesión,
 * «Iniciar sesión» a `/login?lang=`.
 *
 * Antes salía en el idioma que tuviera el navegador y siempre mandaba a
 * `/login`, que con sesión devuelve a la app (`useRedirectIfSignedIn`).
 */
import { StrictMode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { VerifyEmailPage } from '../pages/VerifyEmailPage';
import { auth } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: { ...actual.auth, verifyEmail: vi.fn(), resendVerification: vi.fn(), me: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;

beforeEach(async () => {
  vi.clearAllMocks();
  m(auth.verifyEmail).mockResolvedValue({ message: 'ok' });
  await i18n.changeLanguage('es');
});
afterEach(cleanup);

describe('VerifyEmailPage: idioma y destino (45.4)', () => {
  it('con lang=en sale en inglés aunque la app estuviera en español', async () => {
    m(auth.me).mockRejectedValue(new Error('401'));
    render(<VerifyEmailPage token="t" lang="en" />);
    expect(await screen.findByText(i18n.t('verifyEmail.success', { lng: 'en' }))).toBeInTheDocument();
    expect(i18n.language).toBe('en');
  });

  it('con sesión, «Continuar» lleva a /', async () => {
    m(auth.me).mockResolvedValue({ id: 'u1' });
    render(<VerifyEmailPage token="t" lang="es" />);
    const link = await screen.findByRole('link', { name: 'Continuar' });
    expect(link.getAttribute('href')).toBe('/');
    expect(screen.queryByRole('link', { name: 'Iniciar sesión' })).toBeNull();
  });

  it('sin sesión, «Iniciar sesión» lleva a /login con el idioma', async () => {
    m(auth.me).mockRejectedValue(new Error('401'));
    render(<VerifyEmailPage token="t" lang="es" />);
    const link = await screen.findByRole('link', { name: 'Iniciar sesión' });
    expect(link.getAttribute('href')).toBe('/login?lang=es');
    expect(screen.queryByRole('link', { name: 'Continuar' })).toBeNull();
  });

  it('en inglés y sin sesión: «Sign in» a /login?lang=en', async () => {
    m(auth.me).mockRejectedValue(new Error('401'));
    render(<VerifyEmailPage token="t" lang="en" />);
    const link = await screen.findByRole('link', { name: 'Sign in' });
    expect(link.getAttribute('href')).toBe('/login?lang=en');
  });

  it('un lang no válido se ignora: sigue el idioma de la app', async () => {
    m(auth.me).mockRejectedValue(new Error('401'));
    render(<VerifyEmailPage token="t" lang="fr" />);
    const link = await screen.findByRole('link', { name: 'Iniciar sesión' });
    expect(link.getAttribute('href')).toBe('/login?lang=es');
    expect(i18n.language).toBe('es');
  });

  it('no pregunta por la sesión si el enlace no vale', async () => {
    m(auth.verifyEmail).mockRejectedValue(new Error('400'));
    render(<VerifyEmailPage token="t" lang="es" />);
    expect(await screen.findByText(/no es válido o ha caducado/)).toBeInTheDocument();
    expect(auth.me).not.toHaveBeenCalled();
  });

  it('el mismo enlace se canjea una sola vez aunque el efecto corra dos veces (StrictMode)', async () => {
    // El backend ya solo acepta el primer canje (45.4): el segundo daría 400 y la
    // página diría «enlace no válido» a quien acaba de verificar.
    let calls = 0;
    m(auth.verifyEmail).mockImplementation(async () => {
      calls += 1;
      if (calls > 1) throw new Error('Invalid or expired verification link');
      return { message: 'ok' };
    });
    m(auth.me).mockResolvedValue({ id: 'u1' });
    render(
      <StrictMode>
        <VerifyEmailPage token="una-vez" lang="es" />
      </StrictMode>,
    );
    expect(await screen.findByRole('link', { name: 'Continuar' })).toBeInTheDocument();
    expect(auth.verifyEmail).toHaveBeenCalledTimes(1);
  });
});
