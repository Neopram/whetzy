/**
 * Cartera (design/v2, bug #7 de la auditoría): cada fila con su texto, nunca
 * el identificador del backend («module done», «wallet.10/month»), y lo que no
 * tenga texto no se pinta. Los hitos de la escalera de referidos (ADR-35) salen
 * con su premio, y el de un premio desconocido no se pinta.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import WalletScreen from '../pages/WalletScreen';
import { economy } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    economy: { ...actual.economy, balance: vi.fn(), prices: vi.fn(), referralCode: vi.fn() },
  };
});

beforeEach(async () => {
  await i18n.changeLanguage('es');
  (economy.balance as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ balance: 0, currency: 'credits', expires_in_days: 90 });
  (economy.referralCode as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ code: 'PM4HE2EG', share_url: 'https://whetzy.com/r/PM4HE2EG' });
  (economy.prices as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
    credit_value_usd: 0.01,
    grifos: [
      {
        event: 'referral_activated', credits: 300, cap: '10/month',
        milestones: [{ at: 3, reward: 'pro_month' }, { at: 10, reward: 'pro_max_6_months' }, { at: 99, reward: 'mystery_prize' }],
      },
      { event: 'referral_welcome', credits: 200, cap: 'once' },
      { event: 'something_new', credits: 10, cap: '10/month' },
    ],
    sumideros: [{ item: 'freeze_streak_1day', cost: 150 }, { item: 'mystery_item', cost: 5 }],
  });
});
afterEach(cleanup);

describe('WalletScreen v2', () => {
  it('pinta textos, no identificadores, y oculta lo que no tiene texto', async () => {
    render(<WalletScreen />);
    expect(await screen.findByText('Un amigo que invitaste se activa')).toBeInTheDocument();
    expect(screen.getByText('+300')).toBeInTheDocument();
    expect(screen.getByText(/verificar su email, hacer el diagnóstico, terminar su primer módulo y llegar a 3 días de racha/)).toBeInTheDocument();
    expect(screen.getByText('al 3.º, 1 mes de Pro · al 10.º, 6 meses de Pro Max')).toBeInTheDocument();
    expect(screen.getByText('Te registras con el código de un amigo')).toBeInTheDocument();
    expect(screen.getByText('Caducan a los 30 días si no haces el diagnóstico.')).toBeInTheDocument();
    expect(screen.getByText('Comodín de racha (protege un día sin estudiar)')).toBeInTheDocument();
    expect(screen.getByText('−150')).toBeInTheDocument();
    for (const raw of [/referral/i, /something/i, /mystery/i, /10\/month/, /wallet\./, /99/]) {
      expect(screen.queryByText(raw)).not.toBeInTheDocument();
    }
  });

  it('sin el referido entre las fuentes no hay «Invitar amigos»: no se promete lo que no se abona', async () => {
    (economy.prices as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      credit_value_usd: 0.01, grifos: [], sumideros: [{ item: 'freeze_streak_1day', cost: 150 }],
    });
    render(<WalletScreen />);
    expect(await screen.findByText('Comodín de racha (protege un día sin estudiar)')).toBeInTheDocument();
    expect(screen.queryByText('Invitar amigos')).not.toBeInTheDocument();
    expect(screen.queryByText('PM4HE2EG')).not.toBeInTheDocument();
    expect(screen.queryByText('Cómo ganar créditos')).not.toBeInTheDocument();
  });

  it('con el referido listado, el código para compartir sí sale', async () => {
    render(<WalletScreen />);
    expect(await screen.findByText('Invitar amigos')).toBeInTheDocument();
    expect(screen.getByText('PM4HE2EG')).toBeInTheDocument();
  });
});
