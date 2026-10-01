/**
 * Cartera (design/v2, bug #7 de la auditoría): cada fila con su texto, nunca
 * el identificador del backend («module done», «wallet.10/month»), y lo que no
 * tenga texto no se pinta. La escalera de referidos sale con sus cifras reales.
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
      { event: 'referral_activated', credits: 50, cap: 'ladder', ladder: [[1, 50], [3, 100]] },
      { event: 'something_new', credits: 10, cap: '10/month' },
    ],
    sumideros: [{ item: 'freeze_streak_1day', cost: 150 }, { item: 'mystery_item', cost: 5 }],
  });
});
afterEach(cleanup);

describe('WalletScreen v2', () => {
  it('pinta textos, no identificadores, y oculta lo que no tiene texto', async () => {
    render(<WalletScreen />);
    expect(await screen.findByText('Un amigo que invitaste se registra y empieza a estudiar')).toBeInTheDocument();
    expect(screen.getByText('desde el 1.º: +50 · desde el 3.º: +100')).toBeInTheDocument();
    expect(screen.getByText('Comodín de racha (protege un día sin estudiar)')).toBeInTheDocument();
    expect(screen.getByText('−150')).toBeInTheDocument();
    for (const raw of [/referral/i, /something/i, /mystery/i, /10\/month/, /wallet\./]) {
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
