/**
 * Perfil y pago web (H.29): quien no paga ve los dos planes que llevan a
 * `/checkout`; quien paga por Paddle puede cancelar desde aquí, como prometen
 * los Términos, y se cancela al final del periodo pagado.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { ProfileScreen } from '../pages/ProfileScreen';
import { useAppStore } from '../stores/useAppStore';
import { billing } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    gamification: { ...actual.gamification, badges: vi.fn().mockResolvedValue([]) },
    billing: { ...actual.billing, subscription: vi.fn(), cancelPaddle: vi.fn(), paddleConfig: vi.fn() },
  };
});

const sub = billing.subscription as unknown as ReturnType<typeof vi.fn>;
const cancel = billing.cancelPaddle as unknown as ReturnType<typeof vi.fn>;
const paddleConfig = billing.paddleConfig as unknown as ReturnType<typeof vi.fn>;

const NO_ANNUAL = {
  enabled: true, environment: 'production', client_token: 'live_x',
  prices: { plus: 'pri_plus', pro: 'pri_pro', certification: 'pri_cert', plus_annual: null, pro_annual: null },
};

const PADDLE_SUB = {
  is_premium: true,
  subscription_status: 'active',
  subscription_tier: 'plus',
  subscription_provider: 'paddle',
  stripe_customer_id: null,
  stripe_subscription_id: null,
};

beforeEach(async () => {
  await i18n.changeLanguage('es');
  sub.mockReset();
  cancel.mockReset();
  paddleConfig.mockReset();
  paddleConfig.mockResolvedValue(NO_ANNUAL);
});
afterEach(() => {
  cleanup();
  useAppStore.getState().updateUser({ isPremium: false, grantedTier: null, grantedUntil: null });
});

describe('Perfil — planes y suscripción', () => {
  it('sin plan: Pro y Pro Max llevan al pago', () => {
    useAppStore.getState().updateUser({ isPremium: false });
    render(<ProfileScreen />);
    expect(screen.getByRole('link', { name: /^Pro · 14,99/ })).toHaveAttribute('href', '/checkout?plan=plus');
    expect(screen.getByRole('link', { name: /^Pro Max · 19,99/ })).toHaveAttribute('href', '/checkout?plan=pro');
  });

  it('plan anual apagado (ANNUAL_PLAN_ENABLED=false): no se ofrece', async () => {
    useAppStore.getState().updateUser({ isPremium: false });
    render(<ProfileScreen />);
    await waitFor(() => expect(paddleConfig).toHaveBeenCalled());
    expect(screen.queryByText(/plan anual/i)).toBeNull();
  });

  it('plan anual encendido: aparece junto a los mensuales, con su propio enlace', async () => {
    paddleConfig.mockResolvedValue({
      ...NO_ANNUAL,
      prices: { ...NO_ANNUAL.prices, plus_annual: 'pri_plus_annual', pro_annual: 'pri_pro_annual' },
    });
    useAppStore.getState().updateUser({ isPremium: false });
    render(<ProfileScreen />);
    expect(await screen.findByRole('link', { name: /^Pro · plan anual/ })).toHaveAttribute(
      'href', '/checkout?plan=plus_annual',
    );
    expect(screen.getByRole('link', { name: /^Pro Max · plan anual/ })).toHaveAttribute(
      'href', '/checkout?plan=pro_annual',
    );
  });

  it('plan anual encendido solo para Pro: Pro Max anual no aparece sin su propio id', async () => {
    paddleConfig.mockResolvedValue({
      ...NO_ANNUAL,
      prices: { ...NO_ANNUAL.prices, plus_annual: 'pri_plus_annual', pro_annual: null },
    });
    useAppStore.getState().updateUser({ isPremium: false });
    render(<ProfileScreen />);
    await screen.findByRole('link', { name: /^Pro · plan anual/ });
    expect(screen.queryByRole('link', { name: /^Pro Max · plan anual/ })).toBeNull();
  });

  it('con plan de Paddle: cancelar pide confirmación y llama a Paddle una vez', async () => {
    useAppStore.getState().updateUser({ isPremium: true });
    sub.mockResolvedValue(PADDLE_SUB);
    cancel.mockResolvedValue({ cancel_requested: true, access_until: null });
    render(<ProfileScreen />);

    fireEvent.click(await screen.findByRole('button', { name: 'Cancelar suscripción' }));
    expect(cancel).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Sí, cancelar' }));

    expect(await screen.findByText(/conservas el acceso hasta el final del periodo pagado/)).toBeInTheDocument();
    expect(cancel).toHaveBeenCalledTimes(1);
  });

  it('con un plan ganado invitando amigos dice cuál y hasta cuándo, sin ofrecer cancelar', async () => {
    useAppStore.getState().updateUser({ isPremium: true, grantedTier: 'pro', grantedUntil: '2027-04-21T12:00:00Z' });
    sub.mockResolvedValue({ ...PADDLE_SUB, is_premium: false, subscription_provider: null });
    render(<ProfileScreen />);
    expect(screen.getByText('Tienes Pro Max hasta el 21 de abril de 2027: lo ganaste invitando amigos.')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /^Pro · 14,99/ })).toBeNull();
    await act(async () => {});
    expect(screen.queryByRole('button', { name: 'Cancelar suscripción' })).toBeNull();
  });

  it('con plan de una tienda no ofrece cancelar aquí', async () => {
    useAppStore.getState().updateUser({ isPremium: true });
    sub.mockResolvedValue({ ...PADDLE_SUB, subscription_provider: 'revenuecat' });
    render(<ProfileScreen />);
    await waitFor(() => expect(sub).toHaveBeenCalled());
    await act(async () => {}); // deja que la respuesta llegue al render
    expect(screen.queryByRole('button', { name: 'Cancelar suscripción' })).toBeNull();
  });
});

describe('Perfil — correos con ofertas', () => {
  it('el interruptor da de baja en el servidor y vuelve atrás si falla', async () => {
    const { auth } = await import('../services/api');
    const set = vi.spyOn(auth, 'setMarketingEmails');
    useAppStore.getState().updateUser({ isPremium: false, marketingEmails: true });
    render(<ProfileScreen />);
    const sw = screen.getByRole('switch', { name: 'Correos con ofertas' });

    set.mockResolvedValueOnce({ marketing: false });
    fireEvent.click(sw);
    await waitFor(() => expect(set).toHaveBeenCalledWith(false));
    expect(sw).toHaveAttribute('aria-checked', 'false');

    set.mockRejectedValueOnce(new Error('offline'));
    fireEvent.click(sw);
    await waitFor(() => expect(sw).toHaveAttribute('aria-checked', 'false'));
    expect(set).toHaveBeenLastCalledWith(true);
    set.mockRestore();
  });
});
