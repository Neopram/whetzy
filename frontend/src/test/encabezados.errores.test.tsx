/**
 * axe por ruta (34.8, tras el verificador adversario de 34.9, 2026-10-24): quien
 * llega con un enlace roto (correo caducado, perfil que no existe) veía un texto
 * suelto sin encabezado; un lector de pantalla no sabía en qué página estaba.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { VerifyEmailPage } from '../pages/VerifyEmailPage';
import PublicProfileScreen from '../pages/PublicProfileScreen';
import { ApiError, auth, profiles } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: { ...actual.auth, verifyEmail: vi.fn(), resendVerification: vi.fn() },
    profiles: { get: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
});
afterEach(cleanup);

describe('páginas de error con encabezado', () => {
  it('verificar correo, enlace caducado: el aviso es el h1', async () => {
    m(auth.verifyEmail).mockRejectedValueOnce(new ApiError('expired', 400));
    render(<VerifyEmailPage token="malo" />);
    expect(await screen.findByRole('heading', { level: 1, name: i18n.t('verifyEmail.invalidOrExpired') })).toBeInTheDocument();
  });

  it('verificar correo, confirmado: el aviso es el h1', async () => {
    m(auth.verifyEmail).mockResolvedValueOnce({ message: 'ok' });
    render(<VerifyEmailPage token="bueno" />);
    expect(await screen.findByRole('heading', { level: 1, name: i18n.t('verifyEmail.success') })).toBeInTheDocument();
  });

  it('perfil público que no existe: el aviso es el h1', async () => {
    m(profiles.get).mockRejectedValueOnce(new ApiError('Profile not found', 404));
    render(<PublicProfileScreen handle="nadie" />);
    expect(await screen.findByRole('heading', { level: 1, name: i18n.t('profile.notFound') })).toBeInTheDocument();
  });
});
