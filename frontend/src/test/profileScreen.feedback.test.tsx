/**
 * Paso 2 del lanzamiento piloto (2026-10-01): el alumno no tenía ninguna vía
 * para decir qué le frena. «Enviar comentario» en Perfil abre su correo hacia la
 * dirección de `VITE_FEEDBACK_EMAIL`, que decide el dueño; sin ella no se pinta.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { ProfileScreen } from '../pages/ProfileScreen';
import { useAppStore } from '../stores/useAppStore';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, gamification: { ...actual.gamification, badges: vi.fn().mockResolvedValue([]) } };
});

beforeEach(async () => {
  await i18n.changeLanguage('es');
  useAppStore.getState().updateUser({ username: 'ana_piloto' });
});
afterEach(async () => {
  cleanup();
  vi.unstubAllEnvs();
  await i18n.changeLanguage('es');
});

describe('Perfil — enviar comentario', () => {
  it('con VITE_FEEDBACK_EMAIL, abre un correo con asunto y cuerpo', () => {
    vi.stubEnv('VITE_FEEDBACK_EMAIL', 'pilotos@example.org');

    render(<ProfileScreen />);

    const link = screen.getByRole('link', { name: /Enviar comentario/ });
    const href = link.getAttribute('href') ?? '';
    expect(href.startsWith('mailto:pilotos@example.org?')).toBe(true);
    const params = new URLSearchParams(href.split('?')[1]);
    expect(params.get('subject')).toBe('Whetzy — comentario');
    expect(params.get('body')).toContain('@ana_piloto');
  });

  it('en inglés el texto también está en inglés', async () => {
    vi.stubEnv('VITE_FEEDBACK_EMAIL', 'pilotos@example.org');
    await i18n.changeLanguage('en');

    render(<ProfileScreen />);

    const href = screen.getByRole('link', { name: /Send feedback/ }).getAttribute('href') ?? '';
    expect(new URLSearchParams(href.split('?')[1]).get('subject')).toBe('Whetzy — feedback');
  });

  it('sin dirección configurada no promete un canal que no existe', () => {
    vi.stubEnv('VITE_FEEDBACK_EMAIL', '');

    render(<ProfileScreen />);

    expect(screen.queryByRole('link', { name: /Enviar comentario/ })).not.toBeInTheDocument();
  });
});
