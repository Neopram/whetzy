/**
 * Rediseño de /checkout (plan de Paddle, tarea 3, 2026-10-21). Antes la página solo
 * tenía título, aviso, casilla y «Ir al pago»: no decía qué se compraba ni cuánto
 * costaba, y un fallo de Paddle salía con su código crudo
 * (`transaction_checkout_not_enabled`, la cuenta sin terminar de dar de alta).
 *
 * Lo que se fija aquí:
 * - el resumen del plan y el botón muestran el precio de la landing
 *   (`landing.planPro` / `landing.planProMax`, atados a `backend/app/core/prices.py`);
 * - el selector cambia de plan, la URL y el precio que se abre en Paddle;
 * - el error de cuenta sin alta sale en palabras; el código, solo plegado;
 * - debajo del botón, cancelar, reembolsos y quién cobra.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { act, render, screen, fireEvent, cleanup, within } from '@testing-library/react';
import i18n from '../i18n';
import { auth, billing } from '../services/api';

const open = vi.fn();
let emit: (e: { name: string; code?: string; detail?: string }) => void = () => {};

vi.mock('../lib/paddle', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/paddle')>();
  return {
    ...actual,
    loadPaddle: vi.fn(async (_t: string, _e: string, onEvent: typeof emit) => {
      emit = onEvent;
      return { Checkout: { open } };
    }),
  };
});

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: { ...actual.auth, me: vi.fn() },
    billing: { ...actual.billing, paddleConfig: vi.fn() },
  };
});

const me = auth.me as unknown as ReturnType<typeof vi.fn>;
const config = billing.paddleConfig as unknown as ReturnType<typeof vi.fn>;

const USER = { id: 'u1', email: 'alumno@example.com', language: 'es', is_premium: false };
const CONFIG = {
  enabled: true,
  environment: 'production',
  client_token: 'live_x',
  prices: { plus: 'pri_plus', pro: 'pri_pro', certification: null },
};

async function renderAt(search: string, language = 'es') {
  me.mockResolvedValue({ ...USER, language });
  window.history.pushState({}, '', `/checkout${search}`);
  const { CheckoutScreen } = await import('../pages/CheckoutScreen');
  render(<CheckoutScreen />);
  await screen.findByRole('checkbox');
}

beforeEach(async () => {
  await i18n.changeLanguage('es');
  open.mockReset();
  config.mockResolvedValue(CONFIG);
});

afterEach(() => {
  cleanup();
});

describe('resumen del plan y precio', () => {
  it('Pro: nombre, precio de la landing y sus ventajas; el botón lleva el importe', async () => {
    await renderAt('?plan=plus');
    const summary = screen.getByRole('region', { name: /Pro/ });
    expect(summary).toHaveTextContent('14,99 $');
    expect(summary).toHaveTextContent('al mes');
    expect(within(summary).getAllByRole('listitem').length).toBeGreaterThanOrEqual(3);
    expect(screen.getByRole('button', { name: 'Pagar 14,99 $ al mes' })).toBeInTheDocument();
  });

  it('en inglés, con el precio en dólares a la inglesa', async () => {
    await renderAt('?plan=pro', 'en');
    expect(screen.getByRole('button', { name: 'Pay $19.99 per month' })).toBeInTheDocument();
  });

  it('el selector pasa a Pro Max: cambia precio, URL y lo que se abre en Paddle', async () => {
    await renderAt('?plan=plus');
    fireEvent.click(screen.getByRole('radio', { name: /Pro Max/ }));
    expect(window.location.search).toBe('?plan=pro');
    const pay = screen.getByRole('button', { name: 'Pagar 19,99 $ al mes' });
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(pay);
    expect(open.mock.calls[0][0]).toMatchObject({ items: [{ priceId: 'pri_pro', quantity: 1 }] });
  });

  it('debajo del botón: cancelar cuando quieras, reembolsos y quién cobra', async () => {
    await renderAt('?plan=plus');
    expect(screen.getByText(/Cancela cuando quieras/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Política de reembolsos' })).toHaveAttribute('href', '/refund');
    expect(screen.getAllByText(/Paddle/).length).toBeGreaterThan(0);
  });
});

describe('errores en palabras', () => {
  it('cuenta de Paddle sin alta: lo dice claro y el código queda plegado', async () => {
    await renderAt('?plan=plus');
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: /Pagar/ }));
    act(() => emit({ name: 'checkout.error', code: 'validation', detail: 'transaction_checkout_not_enabled' }));
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('Los pagos aún no están activos');
    expect(alert).toHaveTextContent('No se ha cobrado nada');
    expect(alert).not.toHaveTextContent('transaction_checkout_not_enabled');
    expect(screen.getByText('transaction_checkout_not_enabled').closest('details')).not.toBeNull();
  });
});
