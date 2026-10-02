/**
 * Paddle Billing en la web (H.29): carga de Paddle.js y apertura del checkout.
 *
 * Paddle.js solo se carga en `/checkout`, la única ruta cuyas cabeceras
 * (public/_headers) lo permiten: el resto de la app necesita COOP + COEP para
 * Pyodide, y con `Cross-Origin-Embedder-Policy` el iframe de buy.paddle.com no
 * llega a cargar (comprobado en Chromium el 2026-10-01).
 *
 * API según developer.paddle.com (2026-10-01): script
 * `https://cdn.paddle.com/paddle/v2/paddle.js`, `Paddle.Environment.set`,
 * `Paddle.Initialize({ token, eventCallback })`, `Paddle.Checkout.open({ items,
 * customer, customData, settings })` y los eventos `checkout.completed`,
 * `checkout.closed` y `checkout.error`.
 */

export const PADDLE_JS_URL = 'https://cdn.paddle.com/paddle/v2/paddle.js';

/** Lo que vende la web. `plus` = Pro, `pro` = Pro Max (ADR-41). Las variantes
 *  `_annual` (40.9) solo existen si el backend las sirve en `prices`
 *  (`ANNUAL_PLAN_ENABLED`); el precio real es del dueño. */
export type PaddlePlan = 'plus' | 'pro' | 'plus_annual' | 'pro_annual' | 'certification';

/**
 * Solo los campos que se leen. En `checkout.error` el motivo útil viene en
 * `detail`: con la cuenta sin terminar de dar de alta Paddle manda
 * `code: "validation"` y `detail: "transaction_checkout_not_enabled"`
 * (visto en Chromium el 2026-10-01).
 */
export interface PaddleEvent {
  name?: string;
  code?: string;
  detail?: string;
}

interface PaddleGlobal {
  Environment: { set: (opts: { environment: 'sandbox' }) => void };
  Initialize: (opts: { token: string; eventCallback: (e: PaddleEvent) => void }) => void;
  Checkout: {
    open: (opts: {
      items: { priceId: string; quantity: number }[];
      customer?: { email: string };
      customData?: Record<string, string>;
      settings?: { displayMode?: 'overlay'; locale?: string; allowLogout?: boolean };
    }) => void;
  };
}

declare global {
  interface Window {
    Paddle?: PaddleGlobal;
  }
}

export interface CheckoutRequest {
  plan: PaddlePlan;
  trackId: string | null;
}

/**
 * Lee `?plan=` y `?track=` de la URL. Devuelve null si el plan no es uno de los
 * que se venden, o si es la certificación sin track (no se sabría qué examen
 * desbloquear y el webhook la descartaría).
 */
export function parseCheckoutRequest(search: string): CheckoutRequest | null {
  const params = new URLSearchParams(search);
  const plan = params.get('plan');
  const valid: PaddlePlan[] = ['plus', 'pro', 'plus_annual', 'pro_annual', 'certification'];
  if (!valid.includes(plan as PaddlePlan)) return null;
  const trackId = params.get('track')?.trim() || null;
  if (plan === 'certification' && !trackId) return null;
  return { plan: plan as PaddlePlan, trackId };
}

/** Enlace a la página de pago de un plan. */
export function checkoutHref(plan: PaddlePlan, trackId?: string): string {
  const params = new URLSearchParams({ plan });
  if (trackId) params.set('track', trackId);
  return `/checkout?${params.toString()}`;
}

/**
 * Destino tras iniciar sesión. Solo se acepta volver a `/checkout`: cualquier
 * otro valor (otra web, `//evil.com`, `javascript:`) acaba en `/`, para que
 * `?next=` no sirva de redirección abierta.
 */
export function safeNext(raw: string | null): string {
  if (!raw) return '/';
  if (!raw.startsWith('/checkout')) return '/';
  if (raw.startsWith('//') || raw.includes('\\')) return '/';
  return raw;
}

let loading: Promise<PaddleGlobal> | null = null;

/** Inserta Paddle.js una sola vez y lo inicializa con el token público. */
export function loadPaddle(
  token: string,
  environment: 'sandbox' | 'production',
  onEvent: (e: PaddleEvent) => void,
): Promise<PaddleGlobal> {
  if (loading) return loading;
  loading = new Promise<PaddleGlobal>((resolve, reject) => {
    const script = document.createElement('script');
    script.src = PADDLE_JS_URL;
    script.async = true;
    script.onload = () => {
      const paddle = window.Paddle;
      if (!paddle) {
        reject(new Error('Paddle.js loaded without window.Paddle'));
        return;
      }
      if (environment === 'sandbox') paddle.Environment.set({ environment: 'sandbox' });
      paddle.Initialize({ token, eventCallback: onEvent });
      resolve(paddle);
    };
    script.onerror = () => {
      loading = null;
      reject(new Error('Paddle.js failed to load'));
    };
    document.head.appendChild(script);
  });
  return loading;
}
