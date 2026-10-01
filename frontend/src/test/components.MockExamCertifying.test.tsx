/**
 * Examen certificador en MockExamScreen (38.7, ADR-49): precio visible, botón
 * cerrado mientras el cobro no esté abierto, y certificado al aprobar.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup, within } from '@testing-library/react';
import '../i18n';
import i18n from '../i18n';
import { MockExamScreen } from '../pages/MockExamScreen';
import { ApiError, exams } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    exams: {
      ...actual.exams,
      certificationAccess: vi.fn(),
      startCertifying: vi.fn(),
      startMock: vi.fn(),
      submitMock: vi.fn(),
    },
  };
});

const m = exams as unknown as Record<string, ReturnType<typeof vi.fn>>;

const question = {
  id: 'q1',
  type: 'mcq',
  question_es: '¿Pregunta?',
  question_en: 'Question?',
  options_es: ['a', 'b'],
  options_en: ['a', 'b'],
};

const started = {
  attempt_id: 'att1',
  track_id: 'track08',
  duration_minutes: 90,
  started_at: new Date().toISOString(),
  expires_at: new Date(Date.now() + 90 * 60_000).toISOString(),
  questions: [question],
};

function renderScreen() {
  return render(<MockExamScreen trackId="track08" questionCount={65} durationMinutes={90} />);
}

describe('MockExamScreen — examen certificador', () => {
  beforeEach(() => {
    Object.values(m).forEach((fn) => fn.mockReset?.());
    void i18n.changeLanguage('es');
  });
  afterEach(() => cleanup());

  it('sin compra: muestra el pago único, enlaza al checkout y cierra el botón', async () => {
    m.certificationAccess.mockResolvedValue({
      track_id: 'track08', price_usd: 39.99, paywall_enabled: true, purchased: false, can_start: false,
    });
    renderScreen();
    const section = await screen.findByTestId('certifying');
    expect(within(section).getByText(/Pago único de 39,99 \$/)).toBeInTheDocument();
    expect(within(section).getByRole('link', { name: /COMPRAR LA CERTIFICACIÓN/ })).toHaveAttribute(
      'href',
      '/checkout?plan=certification&track=track08',
    );
    expect(within(section).getByRole('button', { name: /PRESENTAR EXAMEN CERTIFICADOR/ })).toBeDisabled();
  });

  it('aprobado: veredicto, aviso de que no es el examen oficial y certificado de preparación', async () => {
    m.certificationAccess.mockResolvedValue({
      track_id: 'track08', price_usd: 39.99, paywall_enabled: false, purchased: false, can_start: true,
    });
    m.startCertifying.mockResolvedValue(started);
    m.submitMock.mockResolvedValue({
      attempt_id: 'att1',
      status: 'submitted',
      expired: false,
      report: {
        track_id: 'track08', questions: 1, answered: 1, unanswered: 0, correct: 1, raw_pct: 100,
        per_domain: [], elapsed_seconds: 60, duration_minutes: 90,
        scoring_note_es: 'nota', scoring_note_en: 'note',
        per_domain_caveat_es: 'c', per_domain_caveat_en: 'c',
        pass_pct: 70, passed: true,
        pass_note_es: 'Aprobado con el umbral de Whetzy (70 %). No sustituye al examen oficial del proveedor.',
        pass_note_en: 'x',
      },
      certificate: {
        code: 'abc', username: 'ana', track_id: 'track08', track_name_es: 'AWS CLF-C02',
        track_name_en: 'AWS CLF-C02', score_pct: 100, questions: 1,
        issued_at: '2026-09-25T00:00:00Z', revoked: false, is_certification: true,
      },
    });
    renderScreen();
    fireEvent.click(await screen.findByRole('button', { name: /PRESENTAR EXAMEN CERTIFICADOR/ }));
    fireEvent.click(await screen.findByRole('radio', { name: 'a' }));
    fireEvent.click(screen.getByRole('button', { name: /ENTREGAR/ }));

    expect(await screen.findByText('Resultado del examen certificador')).toBeInTheDocument();
    expect(m.startCertifying).toHaveBeenCalledWith('track08');
    expect(m.startMock).not.toHaveBeenCalled();
    expect(screen.getByText('Aprobado')).toBeInTheDocument();
    expect(screen.getAllByText(/Certificado Whetzy de preparación/).length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /VOLVER A PRESENTARLO/ })).toBeInTheDocument();
  });

  it('402 al empezar: explica que falta el pago y vuelve a la portada', async () => {
    m.certificationAccess.mockResolvedValue({
      track_id: 'track08', price_usd: 39.99, paywall_enabled: true, purchased: false, can_start: true,
    });
    m.startCertifying.mockRejectedValue(new ApiError('certification_purchase_required', 402));
    renderScreen();
    fireEvent.click(await screen.findByRole('button', { name: /PRESENTAR EXAMEN CERTIFICADOR/ }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/requiere el pago único/);
  });
});
