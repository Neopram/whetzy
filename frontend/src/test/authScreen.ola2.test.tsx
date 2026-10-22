/**
 * /auth, ola 2 (2026-10-21):
 * - Apple y Google van antes del formulario (el camino corto primero) y el
 *   separador dice qué viene después: «o con tu correo»;
 * - cada botón lleva su variante de marca (colores de sus guías, como tokens);
 * - «Términos» y «Política de privacidad» son enlaces de verdad;
 * - en español se tutea también en «¿Olvidaste tu contraseña?».
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
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
  providers.mockResolvedValue({ providers: ['apple', 'google'] });
});
afterEach(cleanup);

describe('/auth (ola 2)', () => {
  it('Apple y Google antes del primer campo del formulario', async () => {
    render(<AuthScreen onAuthed={vi.fn()} />);
    const google = await screen.findByRole('button', { name: 'Continuar con Google' });
    const firstField = screen.getByLabelText('Correo electrónico');
    expect(google.compareDocumentPosition(firstField) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByText('o con tu correo')).toBeInTheDocument();
  });

  it('cada botón con su variante de marca', async () => {
    render(<AuthScreen onAuthed={vi.fn()} />);
    const google = await screen.findByRole('button', { name: 'Continuar con Google' });
    const apple = screen.getByRole('button', { name: 'Continuar con Apple' });
    expect(google.className).toMatch(/socialGoogle/);
    expect(apple.className).toMatch(/socialApple/);
  });

  it('los colores de marca existen como tokens en los dos temas', () => {
    const css = readFileSync(join(process.cwd(), 'src/styles/design-tokens.css'), 'utf8');
    const [dark, light] = css.split(':root[data-theme="light"] {');
    for (const token of ['--le-oauth-google-bg', '--le-oauth-google-border', '--le-oauth-google-text', '--le-oauth-apple-bg', '--le-oauth-apple-text']) {
      expect(dark).toContain(`${token}:`);
      expect(light).toContain(`${token}:`);
    }
  });

  it.each([
    ['es', 'Términos', 'Política de privacidad'],
    ['en', 'Terms', 'Privacy Policy'],
  ] as const)('Términos y Privacidad son enlaces (%s)', async (lang, terms, privacy) => {
    await i18n.changeLanguage(lang);
    render(<AuthScreen onAuthed={vi.fn()} />);
    await screen.findAllByRole('button');
    expect(screen.getByRole('link', { name: terms })).toHaveAttribute('href', '/terms');
    expect(screen.getByRole('link', { name: privacy })).toHaveAttribute('href', '/privacy');
  });

  it('tutea: «¿Olvidaste tu contraseña?»', async () => {
    window.history.replaceState(null, '', '/login');
    render(<AuthScreen onAuthed={vi.fn()} />);
    expect(await screen.findByRole('button', { name: '¿Olvidaste tu contraseña?' })).toBeInTheDocument();
    expect(screen.queryByText('¿Olvidó su contraseña?')).toBeNull();
  });
});
