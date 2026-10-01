/**
 * 39.34: el quiz muestra el 429 `free_daily_quota` con la hora de reinicio,
 * en vez del genérico "HTTP 429" que dejaba `request()` al descartar el
 * `detail` estructurado (ver services/api.ts, isQuotaError).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import '../i18n';
import { QuizScreen } from '../pages/QuizScreen';
import { useAppStore } from '../stores/useAppStore';
import { ApiError, quiz as quizApi } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, quiz: { ...actual.quiz, start: vi.fn() } };
});

// jsdom has no real <canvas> 2D context, and lottie-web reaches for one as
// soon as it mounts (the loading-state animation QuizScreen renders while
// quiz.start() is pending) — same gap test/setup.ts documents for Worker.
vi.mock('@lottiefiles/react-lottie-player', () => ({ Player: () => null }));

const start = quizApi.start as unknown as ReturnType<typeof vi.fn>;

beforeEach(() => {
  vi.clearAllMocks();
  useAppStore.getState().startQuiz('study', 10);
});
afterEach(cleanup);

describe('QuizScreen — cupo diario Free (39.34)', () => {
  it('muestra el mensaje de cupo con la hora de reinicio, no "HTTP 429"', async () => {
    start.mockRejectedValue(
      new ApiError('free_daily_quota', 429, {
        code: 'free_daily_quota',
        kind: 'questions',
        limit: 30,
        resets_at: '2026-09-28T00:00:00+00:00',
      }),
    );

    render(<QuizScreen />);

    expect(await screen.findByText(/30/)).toBeInTheDocument();
    expect(screen.queryByText(/^HTTP 429$/)).not.toBeInTheDocument();
  });

  it('sigue mostrando el mensaje genérico para un fallo que no es de cupo', async () => {
    start.mockRejectedValue(new Error('network down'));

    render(<QuizScreen />);

    expect(await screen.findByText(/network down/i)).toBeInTheDocument();
  });
});
