/**
 * Tests for src/components/quiz/WhyButton.tsx — the visible "¿Por qué? / Why?"
 * tutor entry point (TASK 11.2 / GAP-5).
 *
 * Covers:
 *  - Free users see an honest upsell with NO network call (red line 7).
 *  - Plus users get a real explanation with a source badge that reflects
 *    `grounded` honestly, including the not-grounded case (red line 2).
 *  - The panel resets when the question changes and closes in one tap.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import '../i18n';
import i18n from '../i18n';
import { WhyButton } from '../components/quiz/WhyButton';
import { ApiError, tutor as tutorApi } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    tutor: { explain: vi.fn() },
  };
});

const explainMock = tutorApi.explain as unknown as ReturnType<typeof vi.fn>;

describe('WhyButton', () => {
  beforeEach(() => {
    explainMock.mockReset();
    void i18n.changeLanguage('es');
  });

  afterEach(() => {
    cleanup();
  });

  it('renders the "¿Por qué?" toggle button for every question, collapsed by default', () => {
    render(<WhyButton questionId="q1" isPremium={false} onUpgrade={vi.fn()} />);
    const btn = screen.getByRole('button', { name: /¿Por qué\?/i });
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveAttribute('aria-expanded', 'false');
  });

  it('free user: shows an honest upsell and never calls the tutor API', async () => {
    const onUpgrade = vi.fn();
    render(<WhyButton questionId="q1" isPremium={false} onUpgrade={onUpgrade} />);

    fireEvent.click(screen.getByRole('button', { name: /¿Por qué\?/i }));

    expect(await screen.findByText(/Explicaciones del tutor AI/i)).toBeInTheDocument();
    expect(explainMock).not.toHaveBeenCalled();

    // Upsell CTA navigates to the upgrade screen — no fake purchase flow.
    fireEvent.click(screen.getByRole('button', { name: /Ver Whetzy Plus/i }));
    expect(onUpgrade).toHaveBeenCalledTimes(1);
  });

  it('free user: closes in one tap via the close button', async () => {
    render(<WhyButton questionId="q1" isPremium={false} onUpgrade={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /¿Por qué\?/i }));
    await screen.findByText(/Explicaciones del tutor AI/i);

    fireEvent.click(screen.getByRole('button', { name: /Cerrar/i }));
    await waitFor(() => expect(screen.queryByText(/Explicaciones del tutor AI/i)).not.toBeInTheDocument());
    expect(screen.getByRole('button', { name: /¿Por qué\?/i })).toHaveAttribute('aria-expanded', 'false');
  });

  it('plus user: fetches and shows a grounded explanation with the source badge', async () => {
    explainMock.mockResolvedValue({
      explanation: 'Porque el bucle recorre cada elemento una vez.',
      provider: 'groq',
      grounded: true,
      times_missed: 1,
    });

    render(<WhyButton questionId="q1" isPremium={true} onUpgrade={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /¿Por qué\?/i }));

    expect(await screen.findByText(/Porque el bucle recorre cada elemento una vez\./)).toBeInTheDocument();
    expect(screen.getByText(/Basado en el contenido del curso/i)).toBeInTheDocument();
    expect(explainMock).toHaveBeenCalledWith('q1');
  });

  it('plus user: honestly labels a non-grounded explanation instead of hiding it', async () => {
    explainMock.mockResolvedValue({
      explanation: 'Respuesta genérica del modelo.',
      provider: 'groq',
      grounded: false,
      times_missed: 0,
    });

    render(<WhyButton questionId="q1" isPremium={true} onUpgrade={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /¿Por qué\?/i }));

    await screen.findByText(/Respuesta genérica del modelo\./);
    expect(screen.getByText(/no verificado contra el curso/i)).toBeInTheDocument();
    expect(screen.queryByText(/Basado en el contenido del curso/i)).not.toBeInTheDocument();
  });

  it('plus user: shows a retry affordance when the tutor call fails', async () => {
    explainMock.mockRejectedValue(new Error('network error'));

    render(<WhyButton questionId="q1" isPremium={true} onUpgrade={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /¿Por qué\?/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/no está disponible/i);
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeInTheDocument();
  });

  it('resets to idle when the question id changes', async () => {
    explainMock.mockResolvedValue({
      explanation: 'Explicación 1',
      provider: 'groq',
      grounded: true,
      times_missed: 0,
    });

    const { rerender } = render(<WhyButton questionId="q1" isPremium={true} onUpgrade={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /¿Por qué\?/i }));
    await screen.findByText('Explicación 1');

    rerender(<WhyButton questionId="q2" isPremium={true} onUpgrade={vi.fn()} />);
    expect(screen.queryByText('Explicación 1')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /¿Por qué\?/i })).toHaveAttribute('aria-expanded', 'false');
  });

  it('renders the English label when the language is switched (bilingual parity)', async () => {
    await i18n.changeLanguage('en');
    render(<WhyButton questionId="q1" isPremium={false} onUpgrade={vi.fn()} />);
    expect(screen.getByRole('button', { name: /^Why\?$/i })).toBeInTheDocument();
  });
  it('Pro al llegar al cupo diario: explica el límite y ofrece Pro Max, sin «Reintentar» (38.6)', async () => {
    explainMock.mockRejectedValueOnce(new ApiError('tutor_daily_limit', 429));
    const onUpgrade = vi.fn();
    render(<WhyButton questionId="q1" isPremium onUpgrade={onUpgrade} />);

    fireEvent.click(screen.getByRole('button', { name: /¿Por qué\?/i }));

    expect(await screen.findByText(/Has usado tus explicaciones de hoy/i)).toBeInTheDocument();
    expect(screen.getByText(/Pro incluye 20 explicaciones/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Ver Pro Max/i }));
    expect(onUpgrade).toHaveBeenCalledTimes(1);
  });

  it('otro 429 (freno por minuto) sigue siendo un error con «Reintentar»', async () => {
    explainMock.mockRejectedValueOnce(new ApiError('Too many requests', 429));
    render(<WhyButton questionId="q1" isPremium onUpgrade={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /¿Por qué\?/i }));
    expect(await screen.findByRole('button', { name: /Reintentar/i })).toBeInTheDocument();
  });
});
