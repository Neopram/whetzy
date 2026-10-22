/**
 * Fila 24.6: en la app nativa (iOS/Android) el canje de códigos promocionales
 * no se enseña. Las tiendas no permiten comprar ni canjear valor fuera de su
 * propio pago; en web el canje sigue donde estaba.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import WalletScreen from '../pages/WalletScreen';
import { economy } from '../services/api';

const cap = vi.hoisted(() => ({ native: false }));
vi.mock('@capacitor/core', () => ({ Capacitor: { isNativePlatform: () => cap.native } }));

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    economy: { ...actual.economy, balance: vi.fn(), prices: vi.fn(), referralCode: vi.fn() },
  };
});

beforeEach(async () => {
  await i18n.changeLanguage('es');
  cap.native = false;
  (economy.balance as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ balance: 120, currency: 'credits', expires_in_days: 90 });
  (economy.referralCode as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ code: 'PM4HE2EG', share_url: 'https://whetzy.com/r/PM4HE2EG' });
  (economy.prices as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
    credit_value_usd: 0.01, grifos: [], sumideros: [{ item: 'freeze_streak_1day', cost: 150 }, { item: 'mastery_report', cost: 300 }],
  });
});
afterEach(cleanup);

describe('WalletScreen: canje de código (24.6)', () => {
  it('en web se enseña el campo y el botón de canjear', async () => {
    render(<WalletScreen />);
    expect(await screen.findByText('Comodín de racha (protege un día sin estudiar)')).toBeInTheDocument();
    expect(screen.getByLabelText(i18n.t('wallet.promoPlaceholder'))).toBeInTheDocument();
    expect(screen.getByRole('button', { name: i18n.t('wallet.redeem') })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: i18n.t('wallet.promo') })).toBeInTheDocument();
  });

  it('en la app nativa no hay campo, ni botón, ni título de canje; el resto de la cartera sigue', async () => {
    cap.native = true;
    render(<WalletScreen />);
    expect(await screen.findByText('Comodín de racha (protege un día sin estudiar)')).toBeInTheDocument();
    expect(screen.queryByLabelText(i18n.t('wallet.promoPlaceholder'))).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: i18n.t('wallet.redeem') })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: i18n.t('wallet.promo') })).not.toBeInTheDocument();
  });

  it('el informe de dominio se compra con créditos en web y no en la app nativa (24.6)', async () => {
    render(<WalletScreen />);
    expect(await screen.findByRole('button', { name: i18n.t('wallet.reportCta') })).toBeInTheDocument();
  });

  it('en la app nativa el informe de dominio no se compra con créditos (24.6)', async () => {
    cap.native = true;
    render(<WalletScreen />);
    expect(await screen.findByText('Comodín de racha (protege un día sin estudiar)')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: i18n.t('wallet.reportCta') })).not.toBeInTheDocument();
  });
});
