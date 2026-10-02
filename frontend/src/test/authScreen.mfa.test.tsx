/**
 * Login con 2FA (O1.3). Hasta el 2026-10-02 la contraseña sola abría sesión
 * aunque la cuenta tuviera 2FA. Ahora `/auth/login` devuelve un reto y la
 * pantalla pide el código; solo un código bueno llama a `onAuthed`.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { AuthScreen } from '../pages/AuthScreen';
import { ApiError, auth } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: { ...actual.auth, oauthProviders: vi.fn(), login: vi.fn(), login2fa: vi.fn() },
  };
});

const login = auth.login as unknown as ReturnType<typeof vi.fn>;
const login2fa = auth.login2fa as unknown as ReturnType<typeof vi.fn>;

beforeEach(async () => {
  vi.clearAllMocks();
  (auth.oauthProviders as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ providers: [] });
  Object.defineProperty(window.navigator, 'language', { value: 'es-ES', configurable: true });
  await i18n.changeLanguage('es');
  window.history.replaceState(null, '', '/auth');
});
afterEach(cleanup);

function openLogin() {
  fireEvent.click(screen.getByRole('button', { name: i18n.t('auth.login') }));
}

async function submitPassword() {
  openLogin();
  fireEvent.change(screen.getByLabelText(/correo/i), { target: { value: 'ana@example.com' } });
  fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'Passw0rd!long' } });
  fireEvent.click(screen.getByRole('button', { name: 'ENTRAR' }));
  return screen.findByRole('heading', { name: 'Verificación en dos pasos' });
}

function submitCode(code: string) {
  fireEvent.change(screen.getByLabelText('Código'), { target: { value: code } });
  fireEvent.click(screen.getByRole('button', { name: 'Verificar y entrar' }));
}

describe('AuthScreen — segundo paso de la 2FA', () => {
  it('con reto, la contraseña sola no entra: pide el código y entra con él', async () => {
    const onAuthed = vi.fn();
    login.mockResolvedValue({ mfa_required: true, mfa_token: 'mfa.jwt' });
    login2fa.mockResolvedValue({ access_token: 'a', refresh_token: 'r' });
    render(<AuthScreen onAuthed={onAuthed} />);
    await submitPassword();
    expect(onAuthed).not.toHaveBeenCalled();

    submitCode('123 456');
    await vi.waitFor(() => expect(onAuthed).toHaveBeenCalledTimes(1));
    expect(login2fa).toHaveBeenCalledWith('123456', 'mfa.jwt');
  });

  it('código malo: se queda en el paso y lo dice', async () => {
    const onAuthed = vi.fn();
    login.mockResolvedValue({ mfa_required: true, mfa_token: 'mfa.jwt' });
    login2fa.mockRejectedValue(new ApiError('invalid_code', 400));
    render(<AuthScreen onAuthed={onAuthed} />);
    await submitPassword();
    submitCode('000000');
    expect(await screen.findByRole('alert')).toHaveTextContent('El código no es válido');
    expect(screen.getByRole('heading', { name: 'Verificación en dos pasos' })).toBeInTheDocument();
    expect(onAuthed).not.toHaveBeenCalled();
  });

  it('demasiados intentos (429) y reto caducado (401) tienen su mensaje', async () => {
    login.mockResolvedValue({ mfa_required: true, mfa_token: 'mfa.jwt' });
    login2fa.mockRejectedValueOnce(new ApiError('locked', 429));
    render(<AuthScreen onAuthed={() => {}} />);
    await submitPassword();
    submitCode('111111');
    expect(await screen.findByRole('alert')).toHaveTextContent('Demasiados intentos');

    login2fa.mockRejectedValueOnce(new ApiError('Unauthorized', 401));
    submitCode('222222');
    expect(await screen.findByRole('alert')).toHaveTextContent('más de 5 minutos');
    expect(screen.queryByRole('heading', { name: 'Verificación en dos pasos' })).toBeNull();
  });

  it('sin 2FA el login entra directo, como siempre', async () => {
    const onAuthed = vi.fn();
    login.mockResolvedValue({ access_token: 'a', refresh_token: 'r' });
    render(<AuthScreen onAuthed={onAuthed} />);
    openLogin();
    fireEvent.change(screen.getByLabelText(/correo/i), { target: { value: 'ana@example.com' } });
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'Passw0rd!long' } });
    fireEvent.click(screen.getByRole('button', { name: 'ENTRAR' }));
    await vi.waitFor(() => expect(onAuthed).toHaveBeenCalledTimes(1));
    expect(login2fa).not.toHaveBeenCalled();
  });

  it('tras OAuth (?mfa=1) pide el código y no deja el parámetro en la URL', async () => {
    window.history.replaceState(null, '', '/auth?mfa=1');
    const onAuthed = vi.fn();
    login2fa.mockResolvedValue({ access_token: 'a', refresh_token: 'r' });
    render(<AuthScreen onAuthed={onAuthed} />);
    expect(screen.getByRole('heading', { name: 'Verificación en dos pasos' })).toBeInTheDocument();
    expect(window.location.search).toBe('');
    submitCode('123456');
    await vi.waitFor(() => expect(onAuthed).toHaveBeenCalledTimes(1));
    // Sin token en el cuerpo: el backend lo lee de la cookie HttpOnly.
    expect(login2fa).toHaveBeenCalledWith('123456', undefined);
  });
});
