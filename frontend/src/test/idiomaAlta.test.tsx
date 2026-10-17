/**
 * 45.1 (ADR-66 E1, E6): el idioma de la cuenta es el que ve el alumno al
 * registrarse: `?lang=`, si no `whetzy_lang` (lo que eligió en la portada), y
 * si no el navegador (eso lo resuelve `i18n.ts` al arrancar).
 *
 * Antes /auth miraba `?lang` y luego `navigator.language`, sin mirar lo elegido
 * en la portada: un iPhone en inglés con la portada en «ES» se registraba en
 * inglés y recibía los correos en inglés (prueba del dueño, 2026-10-17). La
 * portada tampoco leía `whetzy_lang` y su botón iba a /auth sin `?lang`. Los
 * errores de OAuth estaban escritos en español.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n, { detectLanguage } from '../i18n';
import { AuthScreen } from '../pages/AuthScreen';
import LandingScreen from '../pages/LandingScreen';
import { auth } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, auth: { ...actual.auth, oauthProviders: vi.fn(), register: vi.fn(), startOAuth: vi.fn() } };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;

function browser(lang: string) {
  Object.defineProperty(window.navigator, 'language', { value: lang, configurable: true });
}

function fillAndRegister() {
  fireEvent.change(screen.getByLabelText(i18n.t('auth.nameLabel')), { target: { value: 'Fede' } });
  fireEvent.change(screen.getByLabelText(i18n.t('auth.usernameLabel')), { target: { value: 'fede_45' } });
  fireEvent.change(screen.getByLabelText(i18n.t('auth.emailLabel')), { target: { value: 'fede@example.com' } });
  fireEvent.change(screen.getByLabelText(i18n.t('auth.passwordLabel')), { target: { value: 'Str0ng!Pass' } });
  fireEvent.click(screen.getByRole('checkbox'));
  fireEvent.click(screen.getByRole('button', { name: i18n.t('auth.registerCta') }));
}

beforeEach(async () => {
  vi.clearAllMocks();
  m(auth.oauthProviders).mockResolvedValue({ providers: [] });
  m(auth.register).mockResolvedValue({ access_token: 'a', refresh_token: 'r' });
  window.history.replaceState(null, '', '/auth');
});
afterEach(cleanup);

describe('Registro: idioma de la cuenta (45.1)', () => {
  it('portada en español con el navegador en inglés → la cuenta se crea en español', async () => {
    await i18n.changeLanguage('es'); // lo que guardó la portada en whetzy_lang
    browser('en-US');
    render(<AuthScreen onAuthed={vi.fn()} />);
    await screen.findByText('El motor que te aprende mientras aprendes');
    fillAndRegister();
    await vi.waitFor(() => expect(auth.register).toHaveBeenCalled());
    expect(m(auth.register).mock.calls[0][0].language).toBe('es');
  });

  it('?lang=en manda sobre lo guardado', async () => {
    await i18n.changeLanguage('es');
    window.history.replaceState(null, '', '/auth?lang=en');
    render(<AuthScreen onAuthed={vi.fn()} />);
    await screen.findByText('The engine that learns you while you learn');
    fillAndRegister();
    await vi.waitFor(() => expect(auth.register).toHaveBeenCalled());
    expect(m(auth.register).mock.calls[0][0].language).toBe('en');
  });

  it('cambiar el idioma en el formulario es lo que se guarda', async () => {
    await i18n.changeLanguage('es');
    render(<AuthScreen onAuthed={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: 'English' }));
    fillAndRegister();
    await vi.waitFor(() => expect(auth.register).toHaveBeenCalled());
    expect(m(auth.register).mock.calls[0][0].language).toBe('en');
  });

  it('OAuth sale con el idioma de la pantalla', async () => {
    await i18n.changeLanguage('en');
    m(auth.oauthProviders).mockResolvedValue({ providers: ['github'] });
    render(<AuthScreen onAuthed={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /GitHub/ }));
    expect(auth.startOAuth).toHaveBeenCalledWith('github', 'en');
  });
});

describe('Detección inicial (i18n.ts)', () => {
  it('lo guardado gana al navegador; sin nada guardado, el navegador; otro idioma → español', () => {
    browser('en-US');
    localStorage.setItem('whetzy_lang', 'es');
    expect(detectLanguage()).toBe('es');
    localStorage.removeItem('whetzy_lang');
    expect(detectLanguage()).toBe('en');
    browser('fr-FR');
    expect(detectLanguage()).toBe('es');
  });
});

describe('Portada (45.1)', () => {
  it('con «ES» guardado y el navegador en inglés sale en español y el botón lleva ?lang=es', async () => {
    await i18n.changeLanguage('es');
    browser('en-US');
    window.history.replaceState(null, '', '/landing');
    render(<LandingScreen />);
    const ctas = await screen.findAllByRole('link', { name: i18n.t('landing.heroCta') });
    for (const cta of ctas) expect(cta.getAttribute('href')).toBe('/auth?lang=es');
    expect(screen.getByRole('link', { name: i18n.t('landing.nav.login') }).getAttribute('href')).toBe('/login?lang=es');
    expect(i18n.language).toBe('es');
  });
});

describe('Errores de OAuth traducidos (45.1, E6)', () => {
  it.each([
    ['email_required', 'auth.oauthErrors.emailRequired'],
    ['provider_error', 'auth.oauthErrors.providerError'],
    ['account_inactive', 'auth.oauthErrors.accountInactive'],
    ['email_unverified', 'auth.oauthErrors.emailUnverified'],
  ])('%s en inglés', async (code, key) => {
    await i18n.changeLanguage('en');
    window.history.replaceState(null, '', `/auth?oauth_error=${code}`);
    render(<AuthScreen onAuthed={vi.fn()} />);
    const alert = await screen.findByRole('alert');
    expect(i18n.t(key)).not.toBe(key);
    expect(alert.textContent).toContain(i18n.t(key));
  });

  it('sigue al idioma si se cambia y no tapa un error del formulario', async () => {
    await i18n.changeLanguage('es');
    window.history.replaceState(null, '', '/auth?oauth_error=email_required');
    render(<AuthScreen onAuthed={vi.fn()} />);
    expect((await screen.findByRole('alert')).textContent).toContain(i18n.t('auth.oauthErrors.emailRequired', { lng: 'es' }));
    fireEvent.click(screen.getByRole('button', { name: 'English' }));
    expect((await screen.findByRole('alert')).textContent).toContain(i18n.t('auth.oauthErrors.emailRequired', { lng: 'en' }));
    // Enviar el formulario vacío: el error de validación sustituye al de OAuth y se queda.
    fireEvent.click(screen.getByRole('button', { name: i18n.t('auth.registerCta') }));
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).not.toContain(i18n.t('auth.oauthErrors.emailRequired'));
    fireEvent.click(screen.getByRole('button', { name: 'Español' }));
    expect(screen.getByRole('alert').textContent).not.toContain(i18n.t('auth.oauthErrors.emailRequired', { lng: 'es' }));
  });
});
