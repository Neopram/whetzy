/**
 * El perfil público mostraba datos 100% inventados ("Carlos Pérez", Elo y
 * certificados de ejemplo) para cualquier handle -- nunca llamaba al backend
 * (0.3). Ahora es real o 404.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import PublicProfileScreen from '../pages/PublicProfileScreen';
import { ApiError, profiles as profilesApi } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    profiles: { get: vi.fn() },
  };
});

const getMock = profilesApi.get as unknown as ReturnType<typeof vi.fn>;

afterEach(() => {
  cleanup();
  getMock.mockReset();
});

const PROFILE = {
  username: 'ada',
  display_name: 'Ada Lovelace',
  avatar_emoji: '🦉',
  joined_at: '2026-01-15T00:00:00Z',
  current_streak: 12,
  mastery_avg: 78,
  skills_mastered: 24,
  certificates: [
    { code: 'cert-1', track_name_es: 'Python básico', track_name_en: 'Python basics', issued_at: '2026-09-01T00:00:00Z' },
  ],
  projects_completed: [
    { slug: 'rest-api-fastapi', name_es: 'API REST con FastAPI', name_en: 'REST API with FastAPI', completed_at: '2026-08-01T00:00:00Z' },
  ],
};

describe('PublicProfileScreen — real o 404 (0.3)', () => {
  it('shows the real data returned by the backend, not a hardcoded mock', async () => {
    await i18n.changeLanguage('es');
    getMock.mockResolvedValueOnce(PROFILE);
    render(<PublicProfileScreen handle="ada" />);

    await waitFor(() => expect(screen.getByText('Ada Lovelace')).toBeInTheDocument());
    expect(screen.getByText('@ada')).toBeInTheDocument();
    expect(screen.getByText('Python básico')).toBeInTheDocument();
    expect(screen.getByText('API REST con FastAPI')).toBeInTheDocument();
    expect(getMock).toHaveBeenCalledWith('ada');
  });

  it('a completed project is a card, not a link to the non-existent /project route', async () => {
    await i18n.changeLanguage('es');
    getMock.mockResolvedValueOnce(PROFILE);
    render(<PublicProfileScreen handle="ada" />);

    const title = await screen.findByText('API REST con FastAPI');
    expect(title.closest('a')).toBeNull();
    expect(document.querySelector('a[href^="/project/"]')).toBeNull();
  });

  it('shows a not-found message for an unknown handle, not fabricated data', async () => {
    await i18n.changeLanguage('es');
    getMock.mockRejectedValueOnce(new ApiError('Profile not found', 404));
    render(<PublicProfileScreen handle="no-such-user" />);

    await waitFor(() =>
      expect(screen.getByText('No existe ningún perfil con ese nombre de usuario')).toBeInTheDocument()
    );
    expect(screen.queryByText('Ada Lovelace')).not.toBeInTheDocument();
  });

  it('empty certificates and projects show the honest empty state', async () => {
    await i18n.changeLanguage('es');
    getMock.mockResolvedValueOnce({ ...PROFILE, certificates: [], projects_completed: [] });
    render(<PublicProfileScreen handle="ada" />);

    await waitFor(() => expect(screen.getByText('Todavía sin certificaciones')).toBeInTheDocument());
    expect(screen.getByText('Todavía sin proyectos')).toBeInTheDocument();
  });
});

describe('PublicProfileScreen — noindex mientras no haya perfil público (24.8)', () => {
  const robots = () => document.head.querySelector('meta[name="robots"]')?.getAttribute('content') ?? null;

  it('lleva noindex si el perfil no existe o no es público (404)', async () => {
    await i18n.changeLanguage('es');
    getMock.mockRejectedValueOnce(new ApiError('Profile not found', 404));
    render(<PublicProfileScreen handle="privado" />);
    await waitFor(() => expect(screen.getByText(/No existe ningún perfil/)).toBeInTheDocument());
    expect(robots()).toBe('noindex');
  });

  it('lleva noindex mientras carga y lo quita cuando hay un perfil público cargado', async () => {
    await i18n.changeLanguage('es');
    let resolve!: (p: typeof PROFILE) => void;
    getMock.mockReturnValueOnce(new Promise((r) => { resolve = r; }));
    render(<PublicProfileScreen handle="ada" />);
    expect(robots()).toBe('noindex');
    resolve(PROFILE);
    await waitFor(() => expect(screen.getByText('Ada Lovelace')).toBeInTheDocument());
    expect(robots()).toBeNull();
  });
});
