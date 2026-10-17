/**
 * 34.11 (b): /auth elegía el idioma inicial por `?lang`, o si no está,
 * `navigator.language` (AuthScreen.tsx:64) — antes salía siempre en español
 * porque `i18n.ts` arranca con `lng: 'es'` y nadie miraba el navegador. El
 * criterio de aceptación de esa fila pide explícitamente "con test"; el
 * verificador adversario de esta fila lo encontró sin cubrir. Este archivo
 * lo cubre: navegador en inglés → UI en inglés sin `?lang`; navegador en
 * español (o cualquier otro idioma) → se queda en español, el arranque por
 * defecto de `i18n.ts`.
 *
 * 45.1 (ADR-66 E1) cambia el orden: `?lang`, luego lo guardado en
 * `whetzy_lang` (lo elegido en la portada) y solo sin nada guardado el
 * navegador. Ese último paso lo hace `detectLanguage` al arrancar i18n
 * (`idiomaAlta.test.tsx`); /auth ya no mira el navegador por su cuenta.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { AuthScreen } from '../pages/AuthScreen';
import { auth } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, auth: { ...actual.auth, oauthProviders: vi.fn() } };
});

const oauthProviders = auth.oauthProviders as unknown as ReturnType<typeof vi.fn>;

function stubNavigatorLanguage(lang: string) {
  Object.defineProperty(window.navigator, 'language', { value: lang, configurable: true });
}

beforeEach(async () => {
  vi.clearAllMocks();
  oauthProviders.mockResolvedValue({ providers: [] });
  await i18n.changeLanguage('es');
  window.history.replaceState(null, '', '/auth');
});
afterEach(cleanup);

describe('AuthScreen — idioma inicial por navigator.language (34.11 b)', () => {
  it('navegador en inglés con «es» guardado, sin ?lang → se queda en español (45.1)', async () => {
    stubNavigatorLanguage('en-US');
    render(<AuthScreen onAuthed={() => {}} />);
    await screen.findByText('El motor que te aprende mientras aprendes');
    expect(i18n.language).toBe('es');
  });

  it('i18n arrancó en inglés (nada guardado y navegador en inglés) → /auth en inglés', async () => {
    await i18n.changeLanguage('en');
    render(<AuthScreen onAuthed={() => {}} />);
    await screen.findByText('The engine that learns you while you learn');
    expect(i18n.language).toBe('en');
  });

  it('navegador en español, sin ?lang → la UI se queda en español', async () => {
    stubNavigatorLanguage('es-AR');
    render(<AuthScreen onAuthed={() => {}} />);
    await screen.findByText('El motor que te aprende mientras aprendes');
    expect(i18n.language).toBe('es');
  });

  it('navegador en un tercer idioma, sin ?lang → cae a español, no a inglés', async () => {
    stubNavigatorLanguage('fr-FR');
    render(<AuthScreen onAuthed={() => {}} />);
    await screen.findByText('El motor que te aprende mientras aprendes');
    expect(i18n.language).toBe('es');
  });

  it('?lang=en en la URL gana al navegador en español', async () => {
    window.history.replaceState(null, '', '/auth?lang=en');
    stubNavigatorLanguage('es-ES');
    render(<AuthScreen onAuthed={() => {}} />);
    await screen.findByText('The engine that learns you while you learn');
    expect(i18n.language).toBe('en');
  });
});
