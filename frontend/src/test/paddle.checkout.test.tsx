/**
 * Pago web con Paddle (H.29): la página `/checkout`, sus cabeceras y los
 * enlaces que llevan a ella.
 *
 * Lo que se fija aquí:
 * - sin sesión se va a iniciar sesión y se vuelve al pago (`?next=`), sin que
 *   `next` sirva de redirección abierta;
 * - el pago no se abre sin la casilla de renuncia al desistimiento (art. 16.m)
 *   y Paddle recibe `custom_data.user_id`, que es como el webhook sabe a quién
 *   dar el plan;
 * - `/checkout` es la única ruta cuya CSP deja entrar a Paddle, y la única sin
 *   COEP (bajo COEP el iframe de Paddle no carga; comprobado en Chromium).
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { act, render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';
import '../i18n';
import i18n from '../i18n';
import { ApiError, auth, billing, exams } from '../services/api';
import { checkoutHref, parseCheckoutRequest, safeNext } from '../lib/paddle';

const open = vi.fn();

vi.mock('../lib/paddle', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/paddle')>();
  return {
    ...actual,
    loadPaddle: vi.fn(async () => ({ Checkout: { open } })),
  };
});

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: { ...actual.auth, me: vi.fn() },
    billing: { ...actual.billing, paddleConfig: vi.fn() },
    exams: { ...actual.exams, certificationAccess: vi.fn() },
  };
});

const me = auth.me as unknown as ReturnType<typeof vi.fn>;
const config = billing.paddleConfig as unknown as ReturnType<typeof vi.fn>;
const certAccess = exams.certificationAccess as unknown as ReturnType<typeof vi.fn>;
const NOT_BOUGHT = { track_id: 'track08', price_usd: 39.99, paywall_enabled: true, purchased: false, can_start: false };

const USER = {
  id: '11111111-1111-1111-1111-111111111111',
  email: 'alumno@example.com',
  language: 'es',
  is_premium: false,
};

const CONFIG = {
  enabled: true,
  environment: 'production',
  client_token: 'live_x',
  prices: { plus: 'pri_plus', pro: 'pri_pro', certification: 'pri_cert' },
};

async function renderAt(search: string) {
  window.history.pushState({}, '', `/checkout${search}`);
  const { CheckoutScreen } = await import('../pages/CheckoutScreen');
  render(<CheckoutScreen />);
}

beforeEach(async () => {
  await i18n.changeLanguage('es');
  open.mockReset();
  me.mockReset();
  config.mockReset();
  config.mockResolvedValue(CONFIG);
  certAccess.mockReset();
  certAccess.mockResolvedValue(NOT_BOUGHT);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('enlaces y parámetros', () => {
  it('lee solo los planes que se venden; la certificación exige track', () => {
    expect(parseCheckoutRequest('?plan=plus')).toEqual({ plan: 'plus', trackId: null });
    expect(parseCheckoutRequest('?plan=pro')).toEqual({ plan: 'pro', trackId: null });
    expect(parseCheckoutRequest('?plan=certification&track=track08')).toEqual({
      plan: 'certification',
      trackId: 'track08',
    });
    expect(parseCheckoutRequest('?plan=certification')).toBeNull();
    expect(parseCheckoutRequest('?plan=creator')).toBeNull();
    expect(parseCheckoutRequest('')).toBeNull();
    expect(checkoutHref('certification', 'track08')).toBe('/checkout?plan=certification&track=track08');
  });

  it('next solo devuelve a /checkout: nunca a otra web', () => {
    expect(safeNext('/checkout?plan=plus')).toBe('/checkout?plan=plus');
    for (const evil of ['https://evil.com', '//evil.com', '/\\evil.com', 'javascript:alert(1)', '/profile', null]) {
      expect(safeNext(evil)).toBe('/');
    }
  });
});

describe('/checkout', () => {
  it('sin sesión manda a iniciar sesión y vuelve al mismo pago', async () => {
    me.mockRejectedValue(new ApiError('Unauthorized', 401));
    const assign = vi.fn();
    vi.spyOn(window, 'location', 'get').mockReturnValue({
      ...window.location,
      pathname: '/checkout',
      search: '?plan=plus',
      assign,
    } as Location);
    await renderAt('?plan=plus');
    await waitFor(() => expect(assign).toHaveBeenCalledWith('/auth?next=%2Fcheckout%3Fplan%3Dplus'));
    expect(open).not.toHaveBeenCalled();
  });

  it('no abre Paddle sin la casilla; con ella, manda el user_id y la renuncia', async () => {
    me.mockResolvedValue(USER);
    await renderAt('?plan=pro');
    const pay = await screen.findByRole('button', { name: 'Ir al pago' });

    fireEvent.click(pay);
    expect(open).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(/renuncia al desistimiento/);

    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(pay);
    expect(open).toHaveBeenCalledTimes(1);
    expect(open.mock.calls[0][0]).toMatchObject({
      items: [{ priceId: 'pri_pro', quantity: 1 }],
      customer: { email: USER.email },
      customData: { user_id: USER.id, eu_withdrawal_waiver: 'accepted' },
    });
  });

  it('la certificación lleva el track para que el webhook sepa qué examen abrir', async () => {
    me.mockResolvedValue(USER);
    await renderAt('?plan=certification&track=track08');
    fireEvent.click(await screen.findByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: 'Ir al pago' }));
    expect(open.mock.calls[0][0]).toMatchObject({
      items: [{ priceId: 'pri_cert', quantity: 1 }],
      customData: { user_id: USER.id, track_id: 'track08' },
    });
  });

  it('una certificación ya comprada no se cobra otra vez', async () => {
    me.mockResolvedValue(USER);
    certAccess.mockResolvedValue({ ...NOT_BOUGHT, purchased: true, can_start: true });
    await renderAt('?plan=certification&track=track08');
    expect(await screen.findByText(/Ya tienes/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Ir al pago' })).toBeNull();
  });

  it('quien ya tiene plan no paga dos veces', async () => {
    me.mockResolvedValue({ ...USER, is_premium: true });
    await renderAt('?plan=plus');
    expect(await screen.findByText(/Ya tienes este plan/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Ir al pago' })).toBeNull();
  });

  it('un error de Paddle se muestra con su código', async () => {
    me.mockResolvedValue(USER);
    const { loadPaddle } = await import('../lib/paddle');
    let emit: (e: { name: string; code?: string; detail?: string }) => void = () => {};
    (loadPaddle as unknown as ReturnType<typeof vi.fn>).mockImplementationOnce(async (_t, _e, onEvent) => {
      emit = onEvent;
      return { Checkout: { open } };
    });
    await renderAt('?plan=plus');
    fireEvent.click(await screen.findByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: 'Ir al pago' }));
    // Forma real del evento con la cuenta sin terminar de dar de alta.
    act(() => emit({ name: 'checkout.error', code: 'validation', detail: 'transaction_checkout_not_enabled' }));
    expect(screen.getByRole('alert')).toHaveTextContent('(transaction_checkout_not_enabled)');
  });

  it('sin Paddle configurado no ofrece pagar', async () => {
    me.mockResolvedValue(USER);
    config.mockResolvedValue({ ...CONFIG, enabled: false });
    await renderAt('?plan=plus');
    expect(await screen.findByText(/El pago aún no está disponible/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Ir al pago' })).toBeNull();
  });
});

describe('public/_headers', () => {
  const raw = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), '..', '..', 'public', '_headers'),
    'utf8',
  );
  const rules = new Map<string, string[]>();
  let current = '';
  for (const line of raw.split('\n')) {
    if (!line.trim() || line.trim().startsWith('#')) continue;
    if (!line.startsWith(' ')) {
      current = line.trim();
      rules.set(current, []);
    } else {
      rules.get(current)?.push(line.trim());
    }
  }
  const csp = (rule: string) =>
    (rules.get(rule) ?? []).find((h) => h.startsWith('Content-Security-Policy:')) ?? '';

  it('el resto del sitio no deja entrar a Paddle y conserva COEP', () => {
    expect(csp('/*')).not.toContain('paddle');
    expect(rules.get('/*')).toContain('Cross-Origin-Embedder-Policy: credentialless');
  });

  it('/checkout quita COEP y COOP y su CSP permite paddle.js y el iframe', () => {
    const checkout = rules.get('/checkout') ?? [];
    expect(checkout).toContain('! Cross-Origin-Embedder-Policy');
    expect(checkout).toContain('! Cross-Origin-Opener-Policy');
    expect(checkout).toContain('! Content-Security-Policy');
    expect(csp('/checkout')).toMatch(/script-src [^;]*https:\/\/cdn\.paddle\.com/);
    expect(csp('/checkout')).toMatch(/frame-src [^;]*https:\/\/buy\.paddle\.com/);
    expect(csp('/checkout')).toContain("frame-ancestors 'none'");
  });
});

describe('textos legales publicados', () => {
  const legal = (lang: 'es' | 'en') =>
    JSON.parse(
      readFileSync(join(dirname(fileURLToPath(import.meta.url)), '..', 'i18n', lang, 'common.json'), 'utf8'),
    ).legal as Record<string, string>;

  it.each(['es', 'en'] as const)('%s: cobra Paddle, no Stripe (el dueño descartó Stripe)', (lang) => {
    const texts = Object.values(legal(lang)).filter((v) => typeof v === 'string').join(' ');
    expect(texts).not.toMatch(/Stripe/);
    expect(legal(lang).termsP4payments).toMatch(/Paddle\.com/);
    expect(legal(lang).termsP4payments).toContain('whetzy.com/refund');
  });

  it.each(['es', 'en'] as const)('%s: /refund se pinta con su título', async (lang) => {
    await i18n.changeLanguage(lang);
    const { LegalScreen } = await import('../pages/LegalScreen');
    render(<LegalScreen doc="refund" />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(legal(lang).refundTitle);
    expect(screen.getByText(legal(lang).termsP5withdrawal)).toBeInTheDocument();
  });
});
