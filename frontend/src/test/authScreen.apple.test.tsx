/**
 * 19.2 (ADR-13): «Continuar con Apple» solo aparece si el servidor lo ofrece
 * (`/auth/oauth/providers`), que hoy no lo hace: faltan las credenciales del
 * Apple Developer Program (H.2). Y cancelar en la pantalla de Apple vuelve con
 * `oauth_error=cancelled`, que se explica en el idioma de la pantalla.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { AuthScreen } from '../pages/AuthScreen';
import { auth } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, auth: { ...actual.auth, oauthProviders: vi.fn(), startOAuth: vi.fn() } };
});

const providers = auth.oauthProviders as unknown as ReturnType<typeof vi.fn>;

beforeEach(async () => {
  vi.clearAllMocks();
  window.history.replaceState(null, '', '/auth');
  await i18n.changeLanguage('es');
});
afterEach(cleanup);

describe('AuthScreen — Sign in with Apple', () => {
  it('sin Apple en /providers no hay botón', async () => {
    providers.mockResolvedValue({ providers: ['google'] });
    render(<AuthScreen onAuthed={vi.fn()} />);
    await screen.findByRole('button', { name: 'Continuar con Google' });
    expect(screen.queryByRole('button', { name: 'Continuar con Apple' })).toBeNull();
  });

  it('con Apple, el botón sale primero y arranca el flujo de Apple', async () => {
    providers.mockResolvedValue({ providers: ['google', 'apple'] });
    render(<AuthScreen onAuthed={vi.fn()} />);
    const apple = await screen.findByRole('button', { name: 'Continuar con Apple' });
    const google = screen.getByRole('button', { name: 'Continuar con Google' });
    expect(apple.compareDocumentPosition(google) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    fireEvent.click(apple);
    expect(auth.startOAuth).toHaveBeenCalledWith('apple', 'es');
  });

  it('cancelar en Apple se explica, en inglés también', async () => {
    providers.mockResolvedValue({ providers: [] });
    await i18n.changeLanguage('en');
    window.history.replaceState(null, '', '/auth?oauth_error=cancelled&lang=en');
    render(<AuthScreen onAuthed={vi.fn()} />);
    expect((await screen.findByRole('alert')).textContent).toContain('You cancelled the sign-in');
  });
});
