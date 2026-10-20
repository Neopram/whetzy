/**
 * 2026-10-20 (hallado al capturar 46.15 D): las páginas públicas que se abren
 * sin cuenta — `/certificate/<code>`, `/verify/<code>`, `/report/<code>` y las
 * de `STANDALONE_DOC` (legal, borrado de cuenta, evidencia) — llamaban a
 * `i18n.changeLanguage(user.language)`. Sin sesión, `user` es el perfil de
 * muestra del store con `language: 'es'`, así que pisaban el idioma que
 * `detectLanguage` había sacado del navegador: con Playwright `locale: 'en-US'`
 * el certificado seguía en español.
 *
 * Criterio: `?lang=` si viene; si hay sesión, el idioma del usuario; si no, el
 * de `detectLanguage` (lo guardado en `whetzy_lang` y, sin nada, el navegador).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import App from '../App';
import i18n from '../i18n';
import { certificates, masteryReports } from '../services/api';
import { DEFAULT_USER_ID, useAppStore } from '../stores/useAppStore';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    certificates: { ...actual.certificates, verify: vi.fn() },
    masteryReports: { ...actual.masteryReports, get: vi.fn() },
  };
});

const verify = certificates.verify as unknown as ReturnType<typeof vi.fn>;
const getReport = masteryReports.get as unknown as ReturnType<typeof vi.fn>;

function stubNavigatorLanguage(lang: string) {
  Object.defineProperty(window.navigator, 'language', { value: lang, configurable: true });
}

const initialUser = useAppStore.getState().user;

beforeEach(async () => {
  vi.clearAllMocks();
  verify.mockRejectedValue(new Error('404'));
  getReport.mockRejectedValue(new Error('404'));
  // El arranque de i18n en un navegador nuevo: nada elegido aún.
  await i18n.changeLanguage('es');
  localStorage.clear();
  useAppStore.setState({ user: { ...initialUser, id: DEFAULT_USER_ID, language: 'es' } });
});
afterEach(() => {
  cleanup();
  window.history.replaceState(null, '', '/');
});

describe('páginas públicas sin sesión — idioma del navegador', () => {
  it('/certificate/<code> con navegador en inglés y sin sesión → en inglés', async () => {
    stubNavigatorLanguage('en-US');
    window.history.replaceState(null, '', '/certificate/ABC123');
    render(<App />);
    expect(await screen.findByRole('heading', { name: 'Certificate check' })).toBeInTheDocument();
    expect(document.documentElement.lang).toBe('en');
  });

  it('/verify/<code> (alias) con navegador en inglés → en inglés', async () => {
    stubNavigatorLanguage('en-GB');
    window.history.replaceState(null, '', '/verify/ABC123');
    render(<App />);
    expect(await screen.findByRole('heading', { name: 'Certificate check' })).toBeInTheDocument();
  });

  it('/certificate/<code> con navegador en español → en español', async () => {
    stubNavigatorLanguage('es-AR');
    window.history.replaceState(null, '', '/certificate/ABC123');
    render(<App />);
    expect(await screen.findByRole('heading', { name: 'Comprobación de certificado' })).toBeInTheDocument();
    expect(document.documentElement.lang).toBe('es');
  });

  it('con sesión manda el idioma del usuario, no el del navegador', async () => {
    stubNavigatorLanguage('en-US');
    useAppStore.setState({ user: { ...initialUser, id: 'user-1', language: 'es' } });
    window.history.replaceState(null, '', '/certificate/ABC123');
    render(<App />);
    expect(await screen.findByRole('heading', { name: 'Comprobación de certificado' })).toBeInTheDocument();
    expect(document.documentElement.lang).toBe('es');
  });

  it('?lang=en gana al navegador en español y a la sesión', async () => {
    stubNavigatorLanguage('es-ES');
    useAppStore.setState({ user: { ...initialUser, id: 'user-1', language: 'es' } });
    window.history.replaceState(null, '', '/certificate/ABC123?lang=en');
    render(<App />);
    expect(await screen.findByRole('heading', { name: 'Certificate check' })).toBeInTheDocument();
  });

  it('/report/<code> con navegador en inglés y sin sesión → en inglés', async () => {
    stubNavigatorLanguage('en-US');
    window.history.replaceState(null, '', '/report/abc123');
    render(<App />);
    await vi.waitFor(() => expect(getReport).toHaveBeenCalled());
    await vi.waitFor(() => expect(document.documentElement.lang).toBe('en'));
    expect(i18n.language).toBe('en');
  });

  it('/privacy con navegador en inglés y sin sesión → en inglés', async () => {
    stubNavigatorLanguage('en-US');
    window.history.replaceState(null, '', '/privacy');
    render(<App />);
    await vi.waitFor(() => expect(document.documentElement.lang).toBe('en'));
    expect(i18n.language).toBe('en');
    expect(document.title).toBe(i18n.t('docTitle.privacy', { lng: 'en' }));
  });
});
