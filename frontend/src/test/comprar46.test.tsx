/**
 * 46.15 bloque E (docs/PLAN_UI_AVANZADA.md §7.5): comprar.
 * - Checkout: el éxito se dibuja solo cuando el servidor confirma el plan
 *   (`active`, tras sondear `/auth/me`). Que Paddle diga `checkout.completed`
 *   no basta: «activando» no lleva check.
 * - Catálogo: las tarjetas entran escalonadas.
 * Con movimiento reducido, check estático y sin escalonado.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { MarketplaceScreen } from '../pages/MarketplaceScreen';
import { auth, billing, content, progress } from '../services/api';
import { useAppStore } from '../stores/useAppStore';

let reduce = false;
vi.mock('framer-motion', async (importOriginal) => {
  const actual = await importOriginal<typeof import('framer-motion')>();
  return { ...actual, useReducedMotion: () => reduce };
});
const open = vi.fn();
vi.mock('../lib/paddle', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/paddle')>();
  return { ...actual, loadPaddle: vi.fn(async () => ({ Checkout: { open } })) };
});
vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: { ...actual.auth, me: vi.fn() },
    billing: { ...actual.billing, paddleConfig: vi.fn() },
    content: { ...actual.content, tracks: vi.fn() },
    progress: { ...actual.progress, dashboard: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;
const USER = { id: 'u1', email: 'a@example.com', language: 'es', is_premium: false };

beforeEach(async () => {
  vi.clearAllMocks();
  reduce = false;
  await i18n.changeLanguage('es');
  m(billing.paddleConfig).mockResolvedValue({
    enabled: true, environment: 'production', client_token: 'live_x', prices: { plus: 'pri_plus' },
  });
});
afterEach(() => { cleanup(); vi.useRealTimers(); });

async function payAndComplete() {
  const { loadPaddle } = await import('../lib/paddle');
  let emit: (e: { name: string }) => void = () => {};
  m(loadPaddle).mockImplementationOnce(async (_t: string, _e: string, onEvent: typeof emit) => {
    emit = onEvent;
    return { Checkout: { open } };
  });
  window.history.pushState({}, '', '/checkout?plan=plus');
  const { CheckoutScreen } = await import('../pages/CheckoutScreen');
  render(<CheckoutScreen />);
  fireEvent.click(await screen.findByRole('checkbox'));
  fireEvent.click(screen.getByRole('button', { name: 'Ir al pago' }));
  vi.useFakeTimers({ toFake: ['setTimeout'] });
  act(() => emit({ name: 'checkout.completed' }));
}

describe('Checkout — éxito solo con el servidor (46.15 E)', () => {
  it('Paddle completa: «activando» sin check; el servidor confirma: check dibujado', async () => {
    m(auth.me).mockResolvedValueOnce(USER).mockResolvedValue({ ...USER, is_premium: true });
    await payAndComplete();
    expect(screen.getByRole('status')).toHaveTextContent(/Activando|activando/);
    expect(screen.queryByTestId('drawn-check')).toBeNull();
    await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
    expect(screen.getByTestId('drawn-check')).toHaveAttribute('data-fx', 'draw');
  });

  it('el servidor aún no lo confirma: sin check', async () => {
    m(auth.me).mockResolvedValue(USER);
    await payAndComplete();
    await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
    expect(screen.queryByTestId('drawn-check')).toBeNull();
  });
});

describe('Catálogo (46.15 E)', () => {
  const TRACK = (id: string) => ({
    id, name_es: `Ruta ${id}`, name_en: `Track ${id}`, order: 1, icon: '🐍', color: '#000',
    total_questions: 10, is_certification: false, cert_provider: null,
    exam_question_count: null, exam_duration_minutes: null,
  });

  it('las tarjetas entran escalonadas; con movimiento reducido, no', async () => {
    useAppStore.setState((s) => ({ user: { ...s.user, language: 'es' } }));
    m(content.tracks).mockResolvedValue([TRACK('track01'), TRACK('track02')]);
    m(progress.dashboard).mockResolvedValue({ tracks: [] });
    render(<MarketplaceScreen />);
    await screen.findByText('Ruta track02');
    expect(screen.getByRole('list')).toHaveAttribute('data-enter', 'stagger');
    cleanup();
    reduce = true;
    render(<MarketplaceScreen />);
    await screen.findByText('Ruta track02');
    expect(screen.getByRole('list')).not.toHaveAttribute('data-enter');
  });
});
