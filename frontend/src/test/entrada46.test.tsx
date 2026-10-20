/**
 * 46.15 bloque A (docs/PLAN_UI_AVANZADA.md §7.5): las pantallas de entrada.
 * - Un error de formulario tiembla (nivel 0, sin sonido) y vuelve a temblar
 *   si cambia; el lector de pantalla lo oye por `role="alert"`.
 * - Verificar el correo y «te enviamos el enlace» dibujan un check cuando el
 *   servidor lo confirma.
 * - El alta cambia de paso con un desplazamiento lateral.
 * - La prueba de nivel marca un punto por pregunta respondida y el nivel
 *   estimado (en palabras, ADR-60) aparece al terminar.
 * Con movimiento reducido no tiembla, no se dibuja y no se desplaza nada.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { AuthScreen } from '../pages/AuthScreen';
import { ForgotPasswordPage } from '../pages/ForgotPasswordPage';
import { VerifyEmailPage } from '../pages/VerifyEmailPage';
import OnboardingScreen from '../pages/OnboardingScreen';
import { PlacementScreen } from '../pages/PlacementScreen';
import { ApiError, auth, content, placement } from '../services/api';

let reduce = false;
vi.mock('framer-motion', async (importOriginal) => {
  const actual = await importOriginal<typeof import('framer-motion')>();
  return { ...actual, useReducedMotion: () => reduce };
});
vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: { ...actual.auth, oauthProviders: vi.fn(), login: vi.fn(), register: vi.fn(), requestPasswordReset: vi.fn(), verifyEmail: vi.fn(), resendVerification: vi.fn() },
    content: { ...actual.content, tracks: vi.fn() },
    placement: { start: vi.fn(), answer: vi.fn(), result: vi.fn() },
  };
});

beforeEach(async () => {
  vi.clearAllMocks();
  reduce = false;
  await i18n.changeLanguage('es');
  (auth.oauthProviders as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ providers: [] });
  (content.tracks as unknown as ReturnType<typeof vi.fn>).mockResolvedValue([]);
  window.history.replaceState(null, '', '/auth');
});
afterEach(cleanup);

async function registerTaken() {
  render(<AuthScreen />);
  (auth.register as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(new ApiError('email_taken', 409, 'email_taken'));
  fireEvent.change(screen.getByLabelText(i18n.t('auth.nameLabel')), { target: { value: 'María' } });
  fireEvent.change(screen.getByLabelText(i18n.t('auth.usernameLabel')), { target: { value: 'maria_46' } });
  fireEvent.change(screen.getByLabelText(i18n.t('auth.emailLabel')), { target: { value: 'maria@example.com' } });
  fireEvent.change(screen.getByLabelText(i18n.t('auth.passwordLabel')), { target: { value: 'Str0ng!Pass' } });
  fireEvent.click(screen.getByRole('checkbox'));
  fireEvent.click(screen.getByRole('button', { name: i18n.t('auth.registerCta') }));
  return screen.findByRole('alert');
}

describe('Entrada (46.15 A)', () => {
  it('el error del formulario tiembla y se anuncia', async () => {
    const alert = await registerTaken();
    expect(alert).toHaveAttribute('data-fx', 'shake');
  });

  it('con movimiento reducido el error no tiembla', async () => {
    reduce = true;
    const alert = await registerTaken();
    expect(alert).not.toHaveAttribute('data-fx');
  });

  it('verificar el correo: check dibujado cuando el servidor lo confirma', async () => {
    (auth.verifyEmail as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ message: 'ok' });
    render(<VerifyEmailPage token="tok" />);
    await waitFor(() => expect(screen.getByTestId('drawn-check')).toBeInTheDocument());
    expect(screen.getByTestId('drawn-check')).toHaveAttribute('data-fx', 'draw');
  });

  it('enlace enviado: check dibujado; con movimiento reducido, estático', async () => {
    (auth.requestPasswordReset as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({});
    reduce = true;
    render(<ForgotPasswordPage onBack={() => {}} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'a@b.co' } });
    fireEvent.submit(screen.getByRole('textbox').closest('form')!);
    expect(await screen.findByTestId('drawn-check')).not.toHaveAttribute('data-fx');
  });

  it('el alta cambia de paso con desplazamiento', async () => {
    render(<OnboardingScreen onDone={() => {}} />);
    expect(await screen.findByTestId('onboarding-step')).toHaveAttribute('data-fx', 'slide');
  });
});

const pq = (id: string) => ({
  id, skill_id: 'sk010101', type: 'mcq' as const, difficulty_tier: 'easy' as const,
  question_es: `Enunciado ${id}`, question_en: `Stem ${id}`,
  options_es: ['uno', 'dos'], options_en: ['one', 'two'],
  correct_answer_es: null, correct_answer_en: null, expected_time_ms: 30000,
});

async function placementAnswered(finished: boolean) {
  const mock = (f: unknown) => f as ReturnType<typeof vi.fn>;
  mock(placement.start).mockResolvedValue({ session_id: 's1', track_id: 'track01', question: pq('q1'), questions_answered: 0 });
  mock(placement.answer).mockResolvedValue({
    correct: true, ability_estimate: 0.4, ability_se: 0.5, questions_answered: 1,
    finished, next_question: finished ? null : pq('q2'),
  });
  mock(placement.result).mockResolvedValue({
    session_id: 's1', track_id: 'track01', ability_estimate: 0.4, ability_se: 0.3, reliability: 0.9,
    total_questions: 20, correct: 14, accuracy: 0.7, module_recommendations: [],
  });
  render(<PlacementScreen trackId="track01" />);
  fireEvent.click(screen.getByRole('button', { name: /comenzar|empezar/i }));
  fireEvent.click(await screen.findByRole('button', { name: /dos/ }));
}

describe('Prueba de nivel (46.15 A)', () => {
  it('un punto por pregunta respondida; el último se llena con efecto', async () => {
    await placementAnswered(false);
    const dots = await screen.findByTestId('placement-dots');
    await waitFor(() => expect(dots.querySelectorAll('[data-done]')).toHaveLength(1));
    expect(dots.children).toHaveLength(20);
    expect(dots).toHaveAttribute('aria-hidden', 'true'); // «Pregunta n de 20» ya lo dice en texto
    expect(dots.querySelector('[data-done]')).toHaveAttribute('data-fx', 'fill');
  });

  it('al terminar, el nivel en palabras aparece con efecto', async () => {
    await placementAnswered(true);
    const level = await screen.findByTestId('placement-level', {}, { timeout: 2000 });
    expect(level).toHaveAttribute('data-fx', 'reveal');
    expect(level.textContent).not.toMatch(/%/);
  });

  it('con movimiento reducido, puntos y nivel sin efecto', async () => {
    reduce = true;
    await placementAnswered(true);
    await waitFor(() => expect(screen.getByTestId('placement-dots').querySelectorAll('[data-done]')).toHaveLength(1));
    expect(screen.getByTestId('placement-dots').querySelector('[data-done]')).not.toHaveAttribute('data-fx');
    expect(await screen.findByTestId('placement-level', {}, { timeout: 2000 })).not.toHaveAttribute('data-fx');
  });
});
