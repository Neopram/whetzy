/**
 * Bus único de «juice» (46.2, docs/PLAN_UI_AVANZADA.md §6): todo sonido o
 * vibración de la app sale de `emit()` y nadie llama a `AudioContext` ni a
 * `navigator.vibrate` por su cuenta. La animación la pinta cada pantalla; aquí
 * solo se decide el nivel y se suena / vibra.
 *
 * Reglas (plan §6.0):
 * - cinco niveles con presupuesto fijo (`TIER_BUDGET`);
 * - coalescencia: de varios eventos a la vez sale uno por nivel y los de
 *   nivel 4 se encolan para después del resumen (`emitMany`, `takeCeremonies`);
 * - nada suena ni vibra antes del primer gesto del usuario (política de
 *   autoplay) ni con su interruptor apagado (`soundEnabled`, `hapticEnabled`);
 * - sonido sintetizado (cero ficheros, cero licencias), ganancia 0,2.
 *
 * Fuera del navegador (prerender de la landing, SSR) no hace nada.
 */
import { useAppStore } from '../stores/useAppStore';

export type FxType =
  | 'tap' | 'correct' | 'wrong' | 'idk'
  | 'combo' | 'mission'
  | 'session_end'
  | 'level_up' | 'badge' | 'streak';

export type FxTier = 0 | 1 | 2 | 3 | 4;

export interface FxEvent {
  type: FxType;
  /** combo: multiplicador cruzado (2, 3 o 5); streak: días del hito;
   *  session_end: la nota de la sesión (`GRADE_RANK`). */
  value?: number;
}

export const TIER: Record<FxType, FxTier> = {
  tap: 0,
  correct: 1, wrong: 1, idk: 1,
  combo: 2, mission: 2,
  session_end: 3,
  level_up: 4, badge: 4, streak: 4,
};

/** Duración máxima (ms), si bloquea la entrada y si suena, por nivel. */
export const TIER_BUDGET: Record<FxTier, { maxMs: number; blocks: boolean; sound: boolean }> = {
  0: { maxMs: 120, blocks: false, sound: false },
  1: { maxMs: 400, blocks: false, sound: true },
  2: { maxMs: 700, blocks: false, sound: true },
  3: { maxMs: 2500, blocks: true, sound: true },
  4: { maxMs: 3000, blocks: true, sound: true },
};

const VIBRATION: Partial<Record<FxType, number[]>> = {
  correct: [10],
  wrong: [20, 40, 20],
  combo: [30],
  mission: [30],
  level_up: [50, 30, 50],
  badge: [50, 30, 50],
  streak: [50, 30, 50],
};

export interface FxResult {
  tier: FxTier;
  sounded: boolean;
  vibrated: boolean;
}

type Listener = (event: FxEvent, result: FxResult) => void;
const listeners = new Set<Listener>();

/** Para la analítica de 46.6 (`fx_emitted`): se avisa de cada emisión. */
export function onFx(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

// ── Primer gesto ────────────────────────────────────────────────────────────
let gestured = false;
let armed = false;

/** Engancha una vez los listeners de primer gesto; idempotente. */
export function armFeedbackFx(): void {
  if (armed || typeof window === 'undefined') return;
  armed = true;
  const unlock = () => {
    gestured = true;
    window.removeEventListener('pointerdown', unlock, true);
    window.removeEventListener('keydown', unlock, true);
  };
  window.addEventListener('pointerdown', unlock, true);
  window.addEventListener('keydown', unlock, true);
}

// ── Sonido sintetizado ──────────────────────────────────────────────────────
let ctx: AudioContext | null = null;

function audio(): AudioContext | null {
  if (ctx) return ctx;
  const Ctor: typeof AudioContext | undefined =
    typeof window === 'undefined'
      ? undefined
      : window.AudioContext
        ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctor) return null;
  ctx = new Ctor();
  return ctx;
}

const NOTE: Record<string, number> = {
  C5: 523.25, E5: 659.25, G5: 783.99, C6: 1046.5, E6: 1318.51, G6: 1567.98,
};

// Lo programado del recuento (46.7b), para poder cortarlo si se salta.
let pending: OscillatorNode[] = [];

function tone(ac: AudioContext, freq: number, start: number, dur: number, wave: OscillatorType, gainValue = 0.2) {
  const osc = ac.createOscillator();
  const gain = ac.createGain();
  osc.type = wave;
  osc.frequency.value = freq;
  // Ganancia maestra 0,2 con caída exponencial: sin clics al cortar.
  gain.gain.setValueAtTime(gainValue, start);
  gain.gain.exponentialRampToValueAtTime(0.001, start + dur);
  osc.connect(gain).connect(ac.destination);
  osc.start(start);
  osc.stop(start + dur);
  return osc;
}

/** Nota S–F → rango para `session_end` (S suena más alto y más largo). */
export const GRADE_RANK = { F: 0, C: 1, B: 2, A: 3, S: 4 } as const;

/** Duración del recuento del resumen (§6.2): los tics duran lo mismo. */
export const COUNT_MS = 1000;

/** Tic a 12 Hz durante el recuento y una nota final según la nota (§6.1). */
function sessionEnd(ac: AudioContext, rank: number) {
  const { C5, E5, G5, C6, E6 } = NOTE;
  const t0 = ac.currentTime;
  const ticks = Math.round((COUNT_MS / 1000) * 12);
  for (let i = 0; i < ticks; i++) pending.push(tone(ac, 2000, t0 + i / 12, 0.02, 'sine', 0.05));
  const finale = [[C5], [C5, E5], [E5, G5], [G5, C6], [G5, C6, E6]][Math.max(0, Math.min(4, rank))];
  finale.forEach((f, i) => pending.push(tone(ac, f, t0 + COUNT_MS / 1000 + i * 0.12, 0.12, 'triangle')));
}

/** Corta lo que quede del recuento (el alumno pulsó «Saltar recuento»). */
export function cancelFx(): void {
  for (const osc of pending) {
    try { osc.stop(); } catch { /* ya terminado */ }
  }
  pending = [];
}

function sequence(ac: AudioContext, notes: number[], step: number, wave: OscillatorType = 'triangle') {
  const t0 = ac.currentTime;
  notes.forEach((f, i) => tone(ac, f, t0 + i * step, step, wave));
}

function chispa(ac: AudioContext) {
  const len = Math.floor(ac.sampleRate * 0.2);
  const buf = ac.createBuffer(1, len, ac.sampleRate);
  const data = buf.getChannelData(0);
  for (let i = 0; i < len; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / len);
  const src = ac.createBufferSource();
  src.buffer = buf;
  const filter = ac.createBiquadFilter();
  filter.type = 'bandpass';
  filter.frequency.value = 3000;
  const gain = ac.createGain();
  gain.gain.value = 0.2;
  src.connect(filter).connect(gain).connect(ac.destination);
  src.start();
}

/** Paleta del plan §6.1. Devuelve false si el evento no suena («no lo sé»). */
function play(ac: AudioContext, e: FxEvent): boolean {
  const { C5, E5, G5, C6, E6, G6 } = NOTE;
  switch (e.type) {
    case 'correct': sequence(ac, [C5, E5], 0.09); return true;
    case 'wrong': tone(ac, 180, ac.currentTime, 0.12, 'sine'); return true;
    case 'combo': {
      const n = e.value === 5 ? 5 : e.value === 3 ? 4 : 3;
      sequence(ac, [C5, E5, G5, C6, E6].slice(0, n), 0.07);
      return true;
    }
    case 'mission': sequence(ac, [G5, C6, E6], 0.08); return true;
    case 'session_end':
      if (e.value === undefined) sequence(ac, [G5, C6], 0.15);
      else sessionEnd(ac, e.value);
      return true;
    case 'level_up':
    case 'badge': sequence(ac, [C5, E5, G5, C6, G6], 0.12); return true;
    case 'streak': chispa(ac); tone(ac, C6, ac.currentTime + 0.2, 0.2, 'triangle'); return true;
    default: return false; // tap, idk: silencio
  }
}

// ── Emisión ─────────────────────────────────────────────────────────────────
export function emit(event: FxEvent): FxResult {
  const tier = TIER[event.type];
  const result: FxResult = { tier, sounded: false, vibrated: false };
  if (typeof window === 'undefined') return result;
  const { soundEnabled, hapticEnabled } = useAppStore.getState();

  if (gestured && soundEnabled && TIER_BUDGET[tier].sound) {
    const ac = audio();
    if (ac) {
      if (ac.state === 'suspended') void ac.resume();
      result.sounded = play(ac, event);
    }
  }
  const pattern = VIBRATION[event.type];
  if (gestured && hapticEnabled && pattern && typeof navigator.vibrate === 'function') {
    result.vibrated = navigator.vibrate(pattern);
  }
  listeners.forEach((l) => l(event, result));
  return result;
}

// ── Coalescencia ────────────────────────────────────────────────────────────
const ceremonies: FxEvent[] = [];

/** Varios eventos de una misma respuesta: uno por nivel (el último gana, que es
 *  el de más valor: el combo ×5 sobre el ×3), y los de nivel 4 se guardan para
 *  `takeCeremonies()` al cerrar la sesión. Nunca dos celebraciones apiladas. */
export function emitMany(events: FxEvent[]): FxResult[] {
  const byTier = new Map<FxTier, FxEvent>();
  for (const e of events) {
    if (TIER[e.type] === 4) ceremonies.push(e);
    else byTier.set(TIER[e.type], e);
  }
  return [...byTier.keys()].sort((a, b) => a - b).map((t) => emit(byTier.get(t)!));
}

/** Ceremonias pendientes, como mucho una por sesión (plan §6.0, nivel 4): la
 *  primera se celebra y el resto vuelve como tarjetas estáticas. */
export function takeCeremonies(): { ceremony: FxEvent | null; cards: FxEvent[] } {
  const all = ceremonies.splice(0);
  return { ceremony: all[0] ?? null, cards: all.slice(1) };
}

/** Solo para tests: vuelve al estado de arranque. */
export function _resetFeedbackFx(): void {
  gestured = false;
  armed = false;
  ctx = null;
  ceremonies.length = 0;
  pending = [];
  listeners.clear();
}
