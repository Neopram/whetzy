/**
 * Informe de dominio (ECONOMIA §2.3): la página pública pinta la instantánea, y
 * la Cartera lo compra con un request_id que se reutiliza al reintentar.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { MasteryReportScreen } from '../pages/MasteryReportScreen';
import WalletScreen from '../pages/WalletScreen';
import { ApiError, economy, masteryReports } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    economy: { ...actual.economy, balance: vi.fn(), prices: vi.fn(), referralCode: vi.fn() },
    masteryReports: { buy: vi.fn(), mine: vi.fn(), get: vi.fn() },
  };
});

const get = masteryReports.get as unknown as ReturnType<typeof vi.fn>;
const buy = masteryReports.buy as unknown as ReturnType<typeof vi.fn>;
const balance = economy.balance as unknown as ReturnType<typeof vi.fn>;

const REPORT = {
  code: 'abc123',
  created_at: '2026-10-02T10:00:00Z',
  snapshot: {
    generated_at: '2026-10-02T10:00:00Z', display_name: 'Ana', username: 'ana',
    total_questions_answered: 240, overall_accuracy: 0.81, max_streak: 12,
    tracks: [{
      track_id: 'track01', name_es: 'Python básico', name_en: 'Python basics', icon: '🐍',
      average_mastery: 0.62, skills_mastered: 3, total_skills: 10,
      mastered_skills: [{ name_es: 'Bucles', name_en: 'Loops', p_known: 0.97 }],
    }],
  },
};

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  balance.mockResolvedValue({ balance: 450, currency: 'credits', expires_in_days: 80 });
  (economy.referralCode as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ code: 'X', share_url: '' });
  (economy.prices as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
    credit_value_usd: 0.01, grifos: [], sumideros: [{ item: 'mastery_report', cost: 300 }],
  });
});
afterEach(cleanup);

describe('MasteryReportScreen', () => {
  it('pinta la instantánea sin sesión y ofrece guardarla en PDF', async () => {
    get.mockResolvedValue(REPORT);
    render(<MasteryReportScreen code="abc123" />);
    expect(await screen.findByText('Ana · @ana')).toBeInTheDocument();
    expect(screen.getByText('81 %')).toBeInTheDocument();
    // ADR-60: la ruta en skills dominadas y la skill por su nombre, sin el % del modelo.
    expect(screen.getByText('3 de 10 habilidades dominadas')).toBeInTheDocument();
    expect(screen.getByText('Bucles')).toBeInTheDocument();
    expect(screen.queryByText(/62 %|97 %/)).toBeNull();
    expect(screen.getByRole('button', { name: 'Guardar como PDF' })).toBeInTheDocument();
    expect(get).toHaveBeenCalledWith('abc123');
  });

  it('un código que no existe dice que no lo encuentra', async () => {
    get.mockRejectedValue(new ApiError('report not found', 404));
    render(<MasteryReportScreen code="nope" />);
    expect(await screen.findByRole('alert')).toHaveTextContent('No encontramos este informe');
  });
});

describe('Cartera — comprar el informe', () => {
  it('compra con un request_id, enseña el enlace y reutiliza el id al reintentar', async () => {
    buy.mockRejectedValueOnce(new Error('network')).mockResolvedValueOnce(REPORT);
    render(<WalletScreen />);
    fireEvent.click(await screen.findByRole('button', { name: 'Generar' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('no se cobra dos veces');

    fireEvent.click(screen.getByRole('button', { name: 'Generar' }));
    expect(await screen.findByRole('link', { name: /\/report\/abc123$/ })).toHaveAttribute('href', '/report/abc123');
    const [first, second] = buy.mock.calls.map((c) => c[0]);
    expect(first).toBe(second);
  });

  it('sin saldo suficiente el botón está desactivado', async () => {
    balance.mockResolvedValue({ balance: 299, currency: 'credits', expires_in_days: 80 });
    render(<WalletScreen />);
    expect(await screen.findByRole('button', { name: 'Generar' })).toBeDisabled();
  });
});
