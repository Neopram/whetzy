/**
 * Preparación (design/v2, brief-msg2 §E): dominios ordenados por peso, la
 * «mayor palanca» es el dominio no listo con más peso × lo que le falta al
 * 75 %, y el simulacro sale con el formato de la ruta (antes caía en 65
 * preguntas / 90 min también en PCEP, que son 30 / 40).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import i18n from '../i18n';
import { ReadinessScreen } from '../pages/ReadinessScreen';
import { useAppStore } from '../stores/useAppStore';
import { exams, content } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    exams: { ...actual.exams, certificationReadiness: vi.fn() },
    content: { ...actual.content, tracks: vi.fn() },
  };
});

const readiness = exams.certificationReadiness as unknown as ReturnType<typeof vi.fn>;
const tracks = content.tracks as unknown as ReturnType<typeof vi.fn>;

const dom = (id: string, name: string, weight: number, p: number, ready = false) => ({
  domain_id: id, name_es: name, name_en: name, weight_pct: weight, p_known_mean: p,
  skills_assessed: 1, skills_total: 3, ready,
});

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  readiness.mockResolvedValue({
    track_id: 'track09',
    overall_p_known: 0.42,
    domains: [
      dom('d1', 'Ligero a cero', 10, 0.0),       // 10 × 0.75 = 7.5
      dom('d2', 'Pesado casi listo', 40, 0.7),   // 40 × 0.05 = 2   (el más pesado, no la palanca)
      dom('d3', 'Medio y listo', 30, 0.9, true), // listo: no cuenta
      dom('d4', 'Medio a cero', 20, 0.0),        // 20 × 0.75 = 15  ← palanca
    ],
  });
  tracks.mockResolvedValue([{
    id: 'track09', name_es: 'PCEP', name_en: 'PCEP', order: 9, icon: '🐍', color: '#000', total_questions: 267,
    is_certification: true, cert_provider: 'Python Institute', exam_question_count: 30, exam_duration_minutes: 40,
  }]);
});
afterEach(cleanup);

describe('ReadinessScreen v2', () => {
  it('ordena por peso y elige como palanca el dominio con más peso × lo que falta', async () => {
    render(<ReadinessScreen trackId="track09" onExit={() => {}} />);
    const lever = await screen.findByRole('region', { name: 'Tu mayor palanca' });
    expect(within(lever).getByText(/Medio a cero: vale el 20 % del examen y su estado es «Evidencia insuficiente»/)).toBeInTheDocument();

    const names = screen.getAllByRole('listitem').map((li) => li.querySelector('span')?.textContent);
    expect(names).toEqual(['Pesado casi listo', 'Medio y listo', 'Medio a cero', 'Ligero a cero']);
  });

  it('ADR-60: sin nada practicado dice «Evidencia insuficiente», nunca un % del modelo', async () => {
    readiness.mockResolvedValue({
      track_id: 'track09', overall_p_known: 0.1,
      domains: [{ ...dom('d1', 'Uno', 60, 0.1), skills_assessed: 0 }, { ...dom('d2', 'Dos', 40, 0.1), skills_assessed: 0 }],
    });
    render(<ReadinessScreen trackId="track09" onExit={() => {}} />);
    expect(await screen.findByTestId('readiness-band')).toHaveTextContent('Evidencia insuficiente');
    expect(screen.getAllByText('sin practicar')).toHaveLength(2);
    expect(document.body.textContent).not.toMatch(/10 ?%/);
  });

  it('ADR-60: con evidencia en todos los dominios y todos listos dice «Fuerte», con sus cifras', async () => {
    readiness.mockResolvedValue({
      track_id: 'track09', overall_p_known: 0.84,
      domains: [
        { ...dom('d1', 'Uno', 60, 0.84, true), answers: 12, correct: 10 },
        { ...dom('d2', 'Dos', 40, 0.84, true), answers: 8, correct: 7 },
      ],
    });
    render(<ReadinessScreen trackId="track09" onExit={() => {}} />);
    expect(await screen.findByTestId('readiness-band')).toHaveTextContent('Fuerte');
    expect(screen.getByText(/20 respuestas · 17 aciertos/)).toBeInTheDocument();
    // «Knowledge 84 %» es justo lo que ADR-60 prohíbe.
    expect(document.body.textContent).not.toMatch(/84 ?%/);
  });

  it('ADR-60: un dominio con menos de 7 respuestas basta para pedir más evidencia', async () => {
    readiness.mockResolvedValue({
      track_id: 'track09', overall_p_known: 0.9,
      domains: [
        { ...dom('d1', 'Uno', 60, 0.9, true), answers: 30, correct: 28 },
        { ...dom('d2', 'Dos', 40, 0.9, true), answers: 6, correct: 6 },
      ],
    });
    render(<ReadinessScreen trackId="track09" onExit={() => {}} />);
    expect(await screen.findByTestId('readiness-band')).toHaveTextContent('Evidencia insuficiente');
  });

  it('el simulacro usa el formato de la ruta, no 65 / 90', async () => {
    const startMockExam = vi.fn();
    useAppStore.setState({ startMockExam });
    render(<ReadinessScreen trackId="track09" onExit={() => {}} />);
    const btn = await screen.findByRole('button', { name: /Hacer simulacro ahora/ });
    await within(btn).findByText('30 preguntas · 40 minutos');
    fireEvent.click(btn);
    expect(startMockExam).toHaveBeenCalledWith('track09', 30, 40);
  });
});
