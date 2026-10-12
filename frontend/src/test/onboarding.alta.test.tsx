/**
 * D-20 y D-23 (dueño, 2026-10-12): el onboarding guarda la ruta elegida en el
 * servidor, manda el origen del alta (primer contacto, sin terceros) y lleva a
 * quien empieza de cero a la primera lección de su ruta.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import OnboardingScreen from '../pages/OnboardingScreen';
import { useAppStore } from '../stores/useAppStore';
import { auth, progress } from '../services/api';
import { captureAttribution, readAttribution } from '../lib/attribution';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: { ...actual.auth, updateMe: vi.fn() },
    progress: { ...actual.progress, skills: vi.fn() },
  };
});

const updateMe = auth.updateMe as unknown as ReturnType<typeof vi.fn>;
const skills = progress.skills as unknown as ReturnType<typeof vi.fn>;

beforeEach(async () => {
  vi.clearAllMocks();
  localStorage.clear();
  await i18n.changeLanguage('es');
  updateMe.mockResolvedValue({});
  skills.mockResolvedValue([{ skill_id: 'sk_first' }, { skill_id: 'sk_second' }]);
});
afterEach(cleanup);

async function answer(label: string) {
  fireEvent.click(await screen.findByRole('button', { name: label }));
}

describe('atribución del alta (D-23)', () => {
  it('guarda el primer contacto y no lo pisa uno posterior', () => {
    captureAttribution('?utm_source=reddit&utm_campaign=aif-beta');
    captureAttribution('?utm_source=google&utm_medium=cpc');
    expect(readAttribution()).toEqual({ utm_source: 'reddit', utm_campaign: 'aif-beta', referred: false });
  });

  it('marca el referido si llegó por /r/<código>', () => {
    localStorage.setItem('whetzy_ref', 'abc');
    expect(readAttribution()).toEqual({ referred: true });
  });
});

describe('onboarding (D-20)', () => {
  it('principiante con certificación: guarda la ruta y abre su primera lección', async () => {
    const startLesson = vi.fn();
    useAppStore.setState({ startLesson });
    captureAttribution('?utm_source=reddit&utm_campaign=aif-beta');
    render(<OnboardingScreen onDone={() => {}} />);

    await answer('Soy principiante');
    await answer('Preparar una certificación');
    await answer('3-10 horas');
    fireEvent.click(await screen.findByTestId('cert-track11'));
    fireEvent.click(await screen.findByRole('button', { name: /Español/ }));

    await waitFor(() => expect(updateMe).toHaveBeenCalled());
    expect(updateMe.mock.calls[0][0]).toMatchObject({
      target_track_id: 'track11',
      signup_attribution: { utm_source: 'reddit', utm_campaign: 'aif-beta', referred: false },
    });
    expect(useAppStore.getState().selectedTrackId).toBe('track11');
    await waitFor(() => expect(skills).toHaveBeenCalledWith('track11'));
    await waitFor(() => expect(startLesson).toHaveBeenCalledWith('sk_first'));
  });

  it('con experiencia va a la prueba de nivel de su ruta, no a la lección', async () => {
    const startLesson = vi.fn();
    const startPlacement = vi.fn();
    useAppStore.setState({ startLesson, startPlacement });
    render(<OnboardingScreen onDone={() => {}} />);

    await answer('Soy profesional');
    await answer('Conseguir trabajo');
    await answer('>10 horas');
    fireEvent.click(await screen.findByRole('button', { name: /Español/ }));

    await waitFor(() => expect(startPlacement).toHaveBeenCalledWith('track04'));
    expect(startLesson).not.toHaveBeenCalled();
  });
});
