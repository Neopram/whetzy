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
    billing: { ...actual.billing, subscription: vi.fn(), cancelPaddle: vi.fn() },
  };
});

const sub = billing.subscription as unknown as ReturnType<typeof vi.fn>;
const cancel = billing.cancelPaddle as unknown as ReturnType<typeof vi.fn>;

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
});
afterEach(() => {
  cleanup();
  useAppStore.getState().updateUser({ isPremium: false });
});

describe('Perfil — planes y suscripción', () => {
  it('sin plan: Pro y Pro Max llevan al pago', () => {
    useAppStore.getState().updateUser({ isPremium: false });
    render(<ProfileScreen />);
    expect(screen.getByRole('link', { name: /^Pro · 14,99/ })).toHaveAttribute('href', '/checkout?plan=plus');
    expect(screen.getByRole('link', { name: /^Pro Max · 19,99/ })).toHaveAttribute('href', '/checkout?plan=pro');
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

  it('con plan de una tienda no ofrece cancelar aquí', async () => {
    useAppStore.getState().updateUser({ isPremium: true });
    sub.mockResolvedValue({ ...PADDLE_SUB, subscription_provider: 'revenuecat' });
    render(<ProfileScreen />);
    await waitFor(() => expect(sub).toHaveBeenCalled());
    await act(async () => {}); // deja que la respuesta llegue al render
    expect(screen.queryByRole('button', { name: 'Cancelar suscripción' })).toBeNull();
  });
});
