/**
 * 46.6 (ADR-68): el embudo de pago y la encuesta de la primera sesión, con la
 * analítica propia. Ver el pago y abrir Paddle se cuentan por plan; la encuesta
 * tiene tres respuestas cerradas, sale una vez por navegador y no se enseña si
 * el navegador pide no ser seguido (su respuesta se tiraría).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import i18n from '../i18n';
import { auth, billing, clientEvents, type ClientEvent } from '../services/api';
import { _resetFxAnalytics, flushFx } from '../lib/fxAnalytics';
import { FirstSessionSurvey, SURVEY_KEY } from '../components/quiz/FirstSessionSurvey';
import { DEFAULT_USER_ID, useAppStore } from '../stores/useAppStore';

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
  };
});

const me = auth.me as unknown as ReturnType<typeof vi.fn>;
const config = billing.paddleConfig as unknown as ReturnType<typeof vi.fn>;
const send = vi.spyOn(clientEvents, 'send').mockResolvedValue({ accepted: 1 });

function sent(): ClientEvent[] {
  flushFx();
  return send.mock.calls.flatMap(([batch]) => batch);
}

function setStoreUser(id: string) {
  useAppStore.setState((s) => ({ user: { ...s.user, id } }));
}

beforeEach(async () => {
  await i18n.changeLanguage('es');
  _resetFxAnalytics();
  send.mockClear();
  open.mockReset();
  localStorage.removeItem(SURVEY_KEY);
  setStoreUser(DEFAULT_USER_ID);
  Object.defineProperty(navigator, 'globalPrivacyControl', { value: undefined, configurable: true });
  Object.defineProperty(navigator, 'doNotTrack', { value: null, configurable: true });
  me.mockResolvedValue({ id: 'u1', email: 'alumno@example.com', language: 'es', is_premium: false });
  config.mockResolvedValue({
    enabled: true,
    environment: 'production',
    client_token: 'live_x',
    prices: { plus: 'pri_plus', pro: 'pri_pro', certification: null },
  });
});

afterEach(() => cleanup());

describe('embudo de pago', () => {
  it('cuenta ver el pago y abrir Paddle con el plan elegido, aunque el store no tenga al usuario', async () => {
    window.history.pushState({}, '', '/checkout?plan=plus');
    const { CheckoutScreen } = await import('../pages/CheckoutScreen');
    render(<CheckoutScreen />);
    await screen.findByRole('checkbox');
    expect(sent()).toEqual([{ type: 'checkout_viewed', plan: 'plus' }]);

    fireEvent.click(screen.getByRole('radio', { name: /Pro Max/ }));
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: /Pagar/ }));
    expect(open).toHaveBeenCalledTimes(1);
    expect(sent()).toContainEqual({ type: 'checkout_opened', plan: 'pro' });
  });

  it('sin el consentimiento marcado no cuenta «abrir»: Paddle no se abrió', async () => {
    window.history.pushState({}, '', '/checkout?plan=plus');
    const { CheckoutScreen } = await import('../pages/CheckoutScreen');
    render(<CheckoutScreen />);
    await screen.findByRole('checkbox');
    fireEvent.click(screen.getByRole('button', { name: /Pagar/ }));
    expect(open).not.toHaveBeenCalled();
    expect(sent().map((e) => e.type)).toEqual(['checkout_viewed']);
  });
});

describe('encuesta de la primera sesión', () => {
  it('una respuesta cerrada, se manda sin texto y no vuelve a salir', () => {
    setStoreUser('u-1');
    const { unmount } = render(<FirstSessionSurvey />);
    expect(screen.getByRole('heading', { name: '¿Te ha servido esta sesión?' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Algo' }));
    expect(screen.getByRole('status')).toHaveTextContent('Gracias');
    expect(sent()).toEqual([{ type: 'first_session_survey', answer: 'somewhat' }]);
    unmount();
    render(<FirstSessionSurvey />);
    expect(screen.queryByRole('heading', { name: /servido/ })).toBeNull();
  });

  it('«Ahora no» la cierra para siempre sin mandar nada', () => {
    setStoreUser('u-1');
    render(<FirstSessionSurvey />);
    fireEvent.click(screen.getByRole('button', { name: 'Ahora no' }));
    expect(screen.queryByRole('heading', { name: /servido/ })).toBeNull();
    expect(localStorage.getItem(SURVEY_KEY)).toBe('done');
    expect(sent()).toEqual([]);
  });

  it.each([
    ['sin sesión', () => {}],
    ['con Global Privacy Control', () => Object.defineProperty(navigator, 'globalPrivacyControl', { value: true, configurable: true })],
    ['con Do Not Track', () => Object.defineProperty(navigator, 'doNotTrack', { value: '1', configurable: true })],
  ])('%s no se enseña: la respuesta se tiraría', (label, arrange) => {
    if (label !== 'sin sesión') setStoreUser('u-1');
    arrange();
    render(<FirstSessionSurvey />);
    expect(screen.queryByRole('heading', { name: /servido/ })).toBeNull();
  });

  it('en inglés', async () => {
    await i18n.changeLanguage('en');
    setStoreUser('u-1');
    render(<FirstSessionSurvey />);
    expect(screen.getByRole('heading', { name: 'Was this session useful?' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Not really' })).toBeInTheDocument();
  });
});
