/**
 * Tests de src/components/home/StreakFreezeShop.tsx (ledger 35.3).
 *
 * Lo que importa es el dinero de juego: un intento = un id; un reintento tras
 * un fallo de red reutiliza el id (el backend no cobra dos veces); un 409 cierra
 * el intento y el siguiente lleva id nuevo; y si no se puede comprar, se dice
 * por qué en vez de dejar un botón gris mudo.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup, fireEvent } from '@testing-library/react';
import i18n from '../i18n';
import { StreakFreezeShop } from '../components/home/StreakFreezeShop';
import { ApiError, economy, type StreakFreezeQuote } from '../services/api';
import { useAppStore } from '../stores/useAppStore';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, economy: { streakFreeze: vi.fn(), buyStreakFreeze: vi.fn() } };
});

const quoteMock = economy.streakFreeze as unknown as ReturnType<typeof vi.fn>;
const buyMock = economy.buyStreakFreeze as unknown as ReturnType<typeof vi.fn>;

function q(over: Partial<StreakFreezeQuote> = {}): StreakFreezeQuote {
  return {
    price: 150, balance: 400, held: 1, max_held: 3,
    purchases_this_week: 0, max_per_week: 2, can_buy: true, blocked_by: null, ...over,
  };
}

async function openConfirm() {
  fireEvent.click(await screen.findByRole('button', { name: /Comprar un comodín/ }));
  return screen.getByRole('button', { name: 'Sí, comprar' });
}

beforeEach(async () => {
  await i18n.changeLanguage('es');
  quoteMock.mockReset();
  buyMock.mockReset();
});
afterEach(cleanup);

describe('StreakFreezeShop', () => {
  it('bloqueado: botón desactivado y el motivo en texto', async () => {
    quoteMock.mockResolvedValue(q({ balance: 20, can_buy: false, blocked_by: 'insufficient_credits' }));
    render(<StreakFreezeShop />);
    const btn = await screen.findByRole('button', { name: /Comprar un comodín/ });
    expect(btn).toBeDisabled();
    expect(screen.getByText(/Cuesta 150 créditos y tienes 20/)).toBeInTheDocument();
  });

  it('compra en dos toques y actualiza los comodines del usuario', async () => {
    quoteMock.mockResolvedValue(q());
    buyMock.mockResolvedValue({ ...q({ held: 2, balance: 250 }), replayed: false });
    render(<StreakFreezeShop />);

    fireEvent.click(await openConfirm());

    await waitFor(() => expect(screen.getByText('Hecho: ya tienes 2 comodines.')).toBeInTheDocument());
    expect(buyMock).toHaveBeenCalledTimes(1);
    expect(buyMock.mock.calls[0][0]).toMatch(/^[0-9a-f-]{36}$/);
    expect(useAppStore.getState().user.streakFreezeAvailable).toBe(2);
  });

  it('un fallo de red conserva el id: el reintento no cobra dos veces', async () => {
    quoteMock.mockResolvedValue(q());
    buyMock
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce({ ...q({ held: 2 }), replayed: true });
    render(<StreakFreezeShop />);

    fireEvent.click(await openConfirm());
    await screen.findByText(/no se cobra dos veces/);
    fireEvent.click(await openConfirm());

    await waitFor(() => expect(buyMock).toHaveBeenCalledTimes(2));
    expect(buyMock.mock.calls[1][0]).toBe(buyMock.mock.calls[0][0]);
  });

  it('un 409 cierra el intento: el siguiente lleva id nuevo y se explica el motivo', async () => {
    quoteMock.mockResolvedValue(q());
    buyMock
      .mockRejectedValueOnce(new ApiError('weekly_limit', 409))
      .mockResolvedValueOnce({ ...q({ held: 2 }), replayed: false });
    render(<StreakFreezeShop />);

    fireEvent.click(await openConfirm());
    await screen.findByText(/Esta semana ya compraste 2/);
    fireEvent.click(await openConfirm());

    await waitFor(() => expect(buyMock).toHaveBeenCalledTimes(2));
    expect(buyMock.mock.calls[1][0]).not.toBe(buyMock.mock.calls[0][0]);
  });
});
