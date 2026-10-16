/**
 * «Atrás» y la entrada a la app (2026-10-16, reproducido con Playwright sobre
 * `master` 56e7001):
 * - tras entrar, «atrás» desde el panel volvía al formulario de acceso;
 * - `/auth` con la sesión abierta enseñaba el formulario;
 * - `/login` abría «Crear cuenta»;
 * - `/r/<código>` atrapaba «atrás» (volvía a /r/ y este redirigía otra vez);
 * - quien ya tenía cuenta no tenía puerta propia en la landing.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, renderHook, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { initialAuthMode, useRedirectIfSignedIn } from '../lib/authRedirect';
import { AuthScreen } from '../pages/AuthScreen';
import { ApiError, auth } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, auth: { ...actual.auth, me: vi.fn(), oauthProviders: vi.fn() } };
});

const me = auth.me as unknown as ReturnType<typeof vi.fn>;
const SRC = join(__dirname, '..');

let replace: ReturnType<typeof vi.fn>;
beforeEach(async () => {
  vi.clearAllMocks();
  (auth.oauthProviders as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ providers: [] });
  Object.defineProperty(window.navigator, 'language', { value: 'es-ES', configurable: true });
  await i18n.changeLanguage('es');
  replace = vi.fn();
  vi.spyOn(window, 'location', 'get').mockReturnValue({ ...window.location, replace } as Location);
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('la pestaña de inicio depende de la ruta', () => {
  it('/login abre «Iniciar sesión»; /auth y /register, «Crear cuenta»', () => {
    expect(initialAuthMode('/login')).toBe('login');
    expect(initialAuthMode('/login/')).toBe('login');
    expect(initialAuthMode('/auth')).toBe('register');
    expect(initialAuthMode('/register')).toBe('register');
  });

  it('AuthScreen en /login enseña el formulario de entrar, sin los campos de registro', () => {
    vi.restoreAllMocks();
    window.history.replaceState(null, '', '/login');
    render(<AuthScreen onAuthed={() => {}} />);
    expect(screen.queryByLabelText('Nombre')).toBeNull();
    expect(screen.getByLabelText(/contraseña/i)).toHaveAttribute('autocomplete', 'current-password');
  });
});

describe('con la sesión abierta, el acceso lleva a la app', () => {
  it('si /auth/me responde, sustituye la entrada del historial por `next`', async () => {
    me.mockResolvedValue({ id: 'u1' });
    renderHook(() => useRedirectIfSignedIn('/'));
    await waitFor(() => expect(replace).toHaveBeenCalledWith('/'));
  });

  it('sin sesión (401) se queda el formulario', async () => {
    me.mockRejectedValue(new ApiError('Not authenticated', 401));
    renderHook(() => useRedirectIfSignedIn('/'));
    await new Promise((r) => setTimeout(r, 20));
    expect(replace).not.toHaveBeenCalled();
  });
});

describe('ninguna navegación interna apila la entrada anterior', () => {
  it('App y Checkout usan location.replace, nunca assign', () => {
    for (const f of ['App.tsx', 'pages/CheckoutScreen.tsx']) {
      expect(readFileSync(join(SRC, f), 'utf8'), f).not.toMatch(/location\.assign\(/);
    }
  });

  it('la landing tiene un «Entrar» que lleva a /login', () => {
    const landing = readFileSync(join(SRC, 'pages', 'LandingScreen.tsx'), 'utf8');
    expect(landing).toMatch(/href="\/login"[^>]*>\{t\('landing\.nav\.login'\)\}/);
  });
});
