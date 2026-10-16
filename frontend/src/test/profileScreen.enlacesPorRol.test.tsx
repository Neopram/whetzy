/**
 * Auditoría de pantallas, 2026-10-16. «Instructor» es para creadores, no para
 * suscripciones regulares (decisión del dueño): plan Creador, o el dueño y los
 * admins. «Admin» es solo del dueño (#202). Antes «Instructor» salía a todos y
 * «Admin» a nadie: `/auth/me` no mandaba `is_admin` y el store lo dejaba en false.
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

const as = (canCreateCourses: boolean, isOwner: boolean) =>
  useAppStore.getState().updateUser({ canCreateCourses, isOwner });

beforeEach(async () => {
  await i18n.changeLanguage('es');
});
afterEach(() => {
  cleanup();
  as(false, false);
});

describe('Perfil — enlaces según plan y rol', () => {
  it('un alumno con suscripción normal no ve Instructor ni Admin', () => {
    as(false, false);
    render(<ProfileScreen />);
    expect(screen.getByRole('button', { name: i18n.t('profile.goCatalog') })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: i18n.t('profile.goInstructor') })).toBeNull();
    expect(screen.queryByRole('button', { name: i18n.t('profile.goAdmin') })).toBeNull();
  });

  it('un creador ve Instructor pero no Admin', () => {
    as(true, false);
    render(<ProfileScreen />);
    expect(screen.getByRole('button', { name: i18n.t('profile.goInstructor') })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: i18n.t('profile.goAdmin') })).toBeNull();
  });

  it('el dueño ve los dos', () => {
    as(true, true);
    render(<ProfileScreen />);
    expect(screen.getByRole('button', { name: i18n.t('profile.goInstructor') })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: i18n.t('profile.goAdmin') })).toBeInTheDocument();
  });
});
