/**
 * 43.2 (ADR-65 D10): los errores del registro y del login se enseñan
 * traducidos y diciendo qué campo falla. Antes, un 409 salía como
 * «email_taken» o «A user with that email…» en inglés, un 422 como «HTTP 422»
 * y un login fallido como «Incorrect email or password» también en la pantalla
 * en español.
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
    auth: { ...actual.auth, oauthProviders: vi.fn(), login: vi.fn(), register: vi.fn() },
  };
});

const register = auth.register as unknown as ReturnType<typeof vi.fn>;
const login = auth.login as unknown as ReturnType<typeof vi.fn>;

async function setLang(lang: 'es' | 'en') {
  Object.defineProperty(window.navigator, 'language', { value: lang === 'es' ? 'es-ES' : 'en-US', configurable: true });
  await i18n.changeLanguage(lang);
}

beforeEach(async () => {
  vi.clearAllMocks();
  (auth.oauthProviders as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ providers: [] });
  window.history.replaceState(null, '', '/auth');
  await setLang('es');
});
afterEach(cleanup);

function fillRegister(username = 'maria_43') {
  fireEvent.change(screen.getByLabelText(i18n.t('auth.nameLabel')), { target: { value: 'María' } });
  fireEvent.change(screen.getByLabelText(i18n.t('auth.usernameLabel')), { target: { value: username } });
  fireEvent.change(screen.getByLabelText(i18n.t('auth.emailLabel')), { target: { value: 'maria@example.com' } });
  fireEvent.change(screen.getByLabelText(i18n.t('auth.passwordLabel')), { target: { value: 'Str0ng!Pass' } });
  fireEvent.click(screen.getByRole('checkbox'));
  fireEvent.click(screen.getByRole('button', { name: i18n.t('auth.registerCta') }));
}

// El aviso lleva un «⚠️ » delante: se compara su contenido, no el texto exacto.
async function expectAlert(key: string) {
  const alert = await screen.findByRole('alert');
  expect(alert.textContent).toContain(i18n.t(key));
}

describe('AuthScreen — errores traducidos y por campo (43.2)', () => {
  it.each(['es', 'en'] as const)('409 email_taken en %s', async (lang) => {
    await setLang(lang);
    register.mockRejectedValue(new ApiError('email_taken', 409, { code: 'email_taken', field: 'email' }));
    render(<AuthScreen onAuthed={vi.fn()} />);
    fillRegister();
    await expectAlert('auth.errEmailTaken');
    expect(i18n.t('auth.errEmailTaken')).not.toBe('auth.errEmailTaken');
  });

  it('409 username_taken', async () => {
    register.mockRejectedValue(new ApiError('username_taken', 409, { code: 'username_taken', field: 'username' }));
    render(<AuthScreen onAuthed={vi.fn()} />);
    fillRegister();
    await expectAlert('auth.errUsernameTaken');
  });

  it('422 por palabra no permitida en el usuario', async () => {
    register.mockRejectedValue(
      new ApiError('HTTP 422', 422, [{ loc: ['body', 'username'], msg: "Value error, That name isn't allowed" }]),
    );
    render(<AuthScreen onAuthed={vi.fn()} />);
    fillRegister();
    await expectAlert('auth.errNameNotAllowed');
  });

  it('422 de email', async () => {
    register.mockRejectedValue(new ApiError('HTTP 422', 422, [{ loc: ['body', 'email'], msg: 'value is not a valid email' }]));
    render(<AuthScreen onAuthed={vi.fn()} />);
    fillRegister();
    await expectAlert('auth.errEmail');
  });

  it('el usuario con espacios alrededor pasa la validación del cliente', async () => {
    register.mockResolvedValue({ access_token: 'a', refresh_token: 'r' });
    const onAuthed = vi.fn();
    render(<AuthScreen onAuthed={onAuthed} />);
    fillRegister('  maria_43  ');
    await vi.waitFor(() => expect(onAuthed).toHaveBeenCalled());
    expect(register.mock.calls[0][0].username).toBe('maria_43');
  });

  // Verificador §7 (2026-10-17): «la regex mira el email sin recortar». No
  // pasa: el campo es `type="email"` y su saneado de valor (HTML) ya quita los
  // espacios de los bordes. Este caso vigila que siga así si el campo cambia.
  it('el email con un espacio detrás (autocompletado del móvil) pasa y viaja recortado', async () => {
    register.mockResolvedValue({ access_token: 'a', refresh_token: 'r' });
    const onAuthed = vi.fn();
    render(<AuthScreen onAuthed={onAuthed} />);
    fireEvent.change(screen.getByLabelText(i18n.t('auth.nameLabel')), { target: { value: 'María' } });
    fireEvent.change(screen.getByLabelText(i18n.t('auth.usernameLabel')), { target: { value: 'maria_43' } });
    fireEvent.change(screen.getByLabelText(i18n.t('auth.emailLabel')), { target: { value: 'maria@example.com ' } });
    fireEvent.change(screen.getByLabelText(i18n.t('auth.passwordLabel')), { target: { value: 'Str0ng!Pass' } });
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: i18n.t('auth.registerCta') }));
    await vi.waitFor(() => expect(onAuthed).toHaveBeenCalled());
    expect(register.mock.calls[0][0].email).toBe('maria@example.com');
  });

  it.each(['es', 'en'] as const)('login con credenciales malas en %s', async (lang) => {
    await setLang(lang);
    login.mockRejectedValue(new ApiError('Incorrect email or password', 401, 'Incorrect email or password'));
    render(<AuthScreen onAuthed={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: i18n.t('auth.login') }));
    fireEvent.change(screen.getByLabelText(i18n.t('auth.emailLabel')), { target: { value: 'ana@example.com' } });
    fireEvent.change(screen.getByLabelText(i18n.t('auth.passwordLabel')), { target: { value: 'Passw0rd!long' } });
    fireEvent.click(screen.getByRole('button', { name: i18n.t('auth.loginCta') }));
    await expectAlert('auth.errCredentials');
  });
});
