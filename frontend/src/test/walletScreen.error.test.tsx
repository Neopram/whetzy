/**
 * e2e de esqueletos del 2026-10-24: si una de las tres llamadas de la Cartera
 * fallaba (en local, el 500 de `/economy/referral/code` por la carrera de
 * `uq_referral_user`), el error se tragaba y la pantalla pintaba «0 créditos»:
 * un fallo de red parecía un saldo vacío. Ahora lo dice y deja reintentar.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
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

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  m(economy.balance).mockResolvedValue({ balance: 120, currency: 'credits', expires_in_days: 90 });
  m(economy.prices).mockResolvedValue({ credit_value_usd: 0.01, grifos: [], sumideros: [] });
});
afterEach(cleanup);

describe('Cartera — un fallo de red no es un saldo vacío', () => {
  it('si una llamada falla, lo dice y no pinta «0 créditos»; reintentar vuelve a pedir', async () => {
    m(economy.referralCode).mockRejectedValueOnce(new Error('Network error'));
    render(<WalletScreen />);
    expect(await screen.findByText(i18n.t('common.loadError'))).toBeInTheDocument();
    expect(screen.queryByLabelText(i18n.t('wallet.balance'))).toBeNull();

    m(economy.referralCode).mockResolvedValue({ code: 'PM4HE2EG', share_url: 'https://whetzy.com/r/PM4HE2EG' });
    fireEvent.click(screen.getByRole('button', { name: i18n.t('common.retry') }));
    // El saldo va en CountUp: una copia visible y otra para el lector de pantalla.
    expect((await screen.findByTestId('wallet-balance')).querySelector('.visually-hidden')).toHaveTextContent('120');
  });
});
