/**
 * 43.3 (ADR-65 D2): objetivo → ruta de aprendizaje → certificación relacionada
 * (opcional) → experiencia → prueba de nivel o «empiezo de cero» → Hoy.
 * Se mantiene lo de D-20/D-23: la ruta y el origen del alta van al servidor.
 *
 * Antes: experiencia, objetivo y horas; la ruta salía del objetivo (no se
 * elegía), y al final se preguntaba el idioma, que ya venía del registro.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import OnboardingScreen, { GOAL } from '../pages/OnboardingScreen';
import { useAppStore } from '../stores/useAppStore';
import { auth, content, type TrackRead } from '../services/api';
import { captureAttribution, readAttribution } from '../lib/attribution';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: { ...actual.auth, updateMe: vi.fn() },
    content: { ...actual.content, tracks: vi.fn() },
  };
});

const updateMe = auth.updateMe as unknown as ReturnType<typeof vi.fn>;
const tracks = content.tracks as unknown as ReturnType<typeof vi.fn>;

function tr(id: string, name: string, cert = false): TrackRead {
  return {
    id, name_es: name, name_en: name, order: 0, icon: '·', color: '#000', total_questions: 1,
    is_certification: cert, cert_provider: null, exam_question_count: null, exam_duration_minutes: null,
  };
}

beforeEach(async () => {
  vi.clearAllMocks();
  localStorage.clear();
  await i18n.changeLanguage('es');
  updateMe.mockResolvedValue({});
  tracks.mockResolvedValue([
    tr('track01', 'Python Básico'),
    tr('track04', 'Ingeniería de Software'),
    tr('track09', 'PCEP', true),
    tr('track41', 'PCAP', true),
  ]);
});
afterEach(cleanup);

async function click(name: string | RegExp) {
  fireEvent.click(await screen.findByRole('button', { name }));
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

describe('onboarding (43.3, D2)', () => {
  it('las dos cosas: ruta, certificación relacionada, experiencia y prueba de nivel', async () => {
    const startPlacement = vi.fn();
    useAppStore.setState({ startPlacement });
    captureAttribution('?utm_source=reddit&utm_campaign=aif-beta');
    const onDone = vi.fn();
    render(<OnboardingScreen onDone={onDone} />);

    await click('Las dos cosas');
    expect(screen.getByText('Programación')).toBeTruthy(); // agrupadas por área
    fireEvent.click(await screen.findByTestId('track-track01'));
    fireEvent.click(await screen.findByTestId('cert-track09'));
    await click('Algo he visto');
    await click('Hacer la prueba');

    await waitFor(() => expect(updateMe).toHaveBeenCalled());
    expect(updateMe.mock.calls[0][0]).toMatchObject({
      onboarding_goal: GOAL.both,
      onboarding_experience: 1,
      target_track_id: 'track01',
      target_certification_id: 'track09',
      onboarding_completed: true,
      signup_attribution: { utm_source: 'reddit', utm_campaign: 'aif-beta', referred: false },
    });
    expect(updateMe.mock.calls[0][0]).not.toHaveProperty('language');
    expect(useAppStore.getState().selectedTrackId).toBe('track01');
    expect(useAppStore.getState().user.onboardingCompleted).toBe(true);
    expect(onDone).toHaveBeenCalled();
    expect(startPlacement).toHaveBeenCalledWith('track01');
  });

  it('aprender: sin paso de certificación; «empiezo de cero» va a Hoy sin prueba', async () => {
    const startPlacement = vi.fn();
    const setScreen = vi.fn();
    useAppStore.setState({ startPlacement, setScreen });
    render(<OnboardingScreen onDone={() => {}} />);

    await click('Aprender');
    fireEvent.click(await screen.findByTestId('track-track01'));
    expect(screen.queryByTestId('cert-track09')).toBeNull();
    await click('Empiezo de cero'); // experiencia
    await click('Empiezo de cero'); // prueba de nivel o no
    expect(startPlacement).not.toHaveBeenCalled();
    expect(setScreen).toHaveBeenCalledWith('home');
    expect(updateMe.mock.calls[0][0].target_certification_id).toBeUndefined();
  });

  it('certificarme en una ruta sin certificación relacionada se salta ese paso', async () => {
    render(<OnboardingScreen onDone={() => {}} />);
    await click('Certificarme');
    fireEvent.click(await screen.findByTestId('track-track04'));
    expect(await screen.findByText(/¿Cuánto sabes ya de Ingeniería de Software\?/)).toBeTruthy();
    expect(screen.getByText('Paso 3 de 4')).toBeTruthy();
  });

  it('ya no pregunta el idioma ni las horas por semana', async () => {
    render(<OnboardingScreen onDone={() => {}} />);
    expect(screen.queryByRole('button', { name: /Español/ })).toBeNull();
    expect(screen.queryByText(/por semana/)).toBeNull();
  });
});
