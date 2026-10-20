/**
 * Analítica de efectos (46.6a, ADR-68, docs/PLAN_UI_AVANZADA.md §7.2).
 *
 * Escucha `onFx()` de feedbackFx y los interruptores de sonido y vibración, y
 * manda los eventos en lote a `POST /analytics/client-events`. El servidor los
 * guarda sin `user_id` ni IP: sirven para saber qué nivel se salta demasiado
 * (plan §6.0 punto 5), no quién lo salta.
 *
 * No se manda nada:
 * - fuera del navegador (prerender, SSR);
 * - sin sesión iniciada;
 * - si el navegador pide no ser seguido (Global Privacy Control o Do Not Track).
 */
import { clientEvents, type ClientEvent } from '../services/api';
import { DEFAULT_USER_ID, useAppStore } from '../stores/useAppStore';
import { onFx, TIER, type FxType } from './feedbackFx';

export const FLUSH_MS = 10_000;
export const MAX_BATCH = 50;

let queue: ClientEvent[] = [];
let timer: ReturnType<typeof setTimeout> | null = null;
let started = false;
let unsubscribe: Array<() => void> = [];

function trackingRefused(): boolean {
  const nav = navigator as Navigator & { globalPrivacyControl?: boolean };
  const win = window as Window & { doNotTrack?: string };
  return nav.globalPrivacyControl === true || nav.doNotTrack === '1' || win.doNotTrack === '1';
}

function allowed(): boolean {
  if (typeof window === 'undefined') return false;
  if (useAppStore.getState().user.id === DEFAULT_USER_ID) return false;
  return !trackingRefused();
}

function enqueue(e: ClientEvent): void {
  if (!allowed()) return;
  queue.push(e);
  if (queue.length >= MAX_BATCH) {
    flushFx();
  } else if (!timer) {
    timer = setTimeout(() => flushFx(), FLUSH_MS);
  }
}

/** Manda lo pendiente; `keepalive` para que sobreviva al cierre de la página. */
export function flushFx(keepalive = false): void {
  if (timer) {
    clearTimeout(timer);
    timer = null;
  }
  while (queue.length > 0) {
    const batch = queue.splice(0, MAX_BATCH);
    // Sin red o con 429 el lote se pierde: es un recuento, no un registro que haya que garantizar.
    void clientEvents.send(batch, keepalive).catch(() => {});
  }
}

/** «Saltar» en el resumen (nivel 3) o en una ceremonia (nivel 4). */
export function trackFxSkipped(fx: FxType): void {
  const tier = TIER[fx];
  if (tier !== 3 && tier !== 4) return;
  enqueue({ type: 'fx_skipped', tier, fx });
}

/** Engancha los oyentes una sola vez; idempotente. */
export function startFxAnalytics(): void {
  if (started || typeof window === 'undefined') return;
  started = true;
  const onPageHide = () => flushFx(true);
  unsubscribe = [
    onFx((event, result) => {
      enqueue({ type: 'fx_emitted', tier: result.tier, fx: event.type, sounded: result.sounded, vibrated: result.vibrated });
    }),
    // Se engancha después de leer las preferencias guardadas: cargarlas no es «cambiarlas».
    useAppStore.subscribe((s, prev) => {
      if (s.soundEnabled !== prev.soundEnabled) enqueue({ type: 'sound_toggled', enabled: s.soundEnabled });
      if (s.hapticEnabled !== prev.hapticEnabled) enqueue({ type: 'haptic_toggled', enabled: s.hapticEnabled });
    }),
    () => window.removeEventListener('pagehide', onPageHide),
  ];
  window.addEventListener('pagehide', onPageHide);
}

/** Solo para tests. */
export function _resetFxAnalytics(): void {
  if (timer) clearTimeout(timer);
  timer = null;
  queue = [];
  started = false;
  unsubscribe.forEach((u) => u());
  unsubscribe = [];
}
