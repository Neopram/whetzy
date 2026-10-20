/**
 * Páginas sueltas (certificado e informe públicos, legales): el idioma de un
 * visitante sin cuenta. Antes se aplicaba `user.language` del store, que para
 * quien no ha entrado nunca vale 'es' por defecto: un reclutador con el
 * navegador en inglés veía la verificación del certificado en español.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { standaloneLanguage } from '../lib/standaloneLanguage';
import { DEFAULT_USER_ID } from '../stores/useAppStore';

const visitor = { id: DEFAULT_USER_ID, language: 'es' as const };
const account = { id: 'u-123', language: 'es' as const };

function browser(lang: string, stored: string | null = null, search = '') {
  vi.spyOn(navigator, 'language', 'get').mockReturnValue(lang);
  localStorage.clear();
  if (stored) localStorage.setItem('whetzy_lang', stored);
  window.history.replaceState(null, '', `/certificate/abc${search}`);
}

afterEach(() => { vi.restoreAllMocks(); localStorage.clear(); });

describe('standaloneLanguage', () => {
  it('visitante sin cuenta con el navegador en inglés: inglés', () => {
    browser('en-US');
    expect(standaloneLanguage(visitor)).toBe('en');
  });

  it('visitante sin cuenta con el navegador en español: español', () => {
    browser('es-AR');
    expect(standaloneLanguage(visitor)).toBe('es');
  });

  it('visitante que eligió idioma en la portada: lo elegido manda sobre el navegador', () => {
    browser('es-ES', 'en');
    expect(standaloneLanguage(visitor)).toBe('en');
  });

  it('con cuenta: el idioma de la cuenta, no el del navegador', () => {
    browser('en-US');
    expect(standaloneLanguage(account)).toBe('es');
  });

  it('?lang= manda siempre (enlace compartido en un idioma)', () => {
    browser('es-ES', null, '?lang=en');
    expect(standaloneLanguage(account)).toBe('en');
  });
});
