/**
 * 46.2 (docs/PLAN_UI_AVANZADA.md §6): el bus de sonido y vibración. Lo que
 * vigila: sin gesto previo o con el interruptor apagado no se crea ni un
 * AudioContext ni se llama a `vibrate`; un evento por nivel; como mucho una
 * ceremonia por sesión; y, desde 46.9 (ADR-67 D3), el sonido viene encendido salvo que el alumno
 * lo haya apagado él.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  _resetFeedbackFx, armFeedbackFx, emit, emitMany, onFx, takeCeremonies, TIER,
} from '../lib/feedbackFx';
import { useAppStore } from '../stores/useAppStore';

let contexts = 0;
let oscillators = 0;

class FakeParam {
  value = 0;
  setValueAtTime() { return this; }
  exponentialRampToValueAtTime() { return this; }
}
class FakeNode {
  frequency = new FakeParam();
  gain = new FakeParam();
  type = '';
  buffer: unknown = null;
  connect(n: unknown) { return n; }
  start() { /* */ }
  stop() { /* */ }
}
class FakeAudioContext {
  currentTime = 0;
  sampleRate = 8000;
  state = 'running';
  destination = {};
  constructor() { contexts++; }
  createOscillator() { oscillators++; return new FakeNode(); }
  createGain() { return new FakeNode(); }
  createBiquadFilter() { return new FakeNode(); }
  createBufferSource() { return new FakeNode(); }
  createBuffer(_c: number, len: number) { return { getChannelData: () => new Float32Array(len) }; }
  resume() { return Promise.resolve(); }
}

const vibrate = vi.fn(() => true);

function gesture() {
  window.dispatchEvent(new Event('pointerdown'));
}

beforeEach(() => {
  _resetFeedbackFx();
  contexts = 0;
  oscillators = 0;
  vibrate.mockClear();
  vi.stubGlobal('AudioContext', FakeAudioContext);
  Object.defineProperty(navigator, 'vibrate', { value: vibrate, configurable: true, writable: true });
  useAppStore.setState({ soundEnabled: true, hapticEnabled: true });
  armFeedbackFx();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('feedbackFx — puertas', () => {
  it('antes del primer gesto no suena ni vibra, aunque los interruptores estén encendidos', () => {
    const r = emit({ type: 'correct' });
    expect(r).toEqual({ tier: 1, sounded: false, vibrated: false });
    expect(contexts).toBe(0);
    expect(vibrate).not.toHaveBeenCalled();
  });

  it('con los interruptores apagados: cero AudioContext y cero vibrate, también tras el gesto', () => {
    useAppStore.setState({ soundEnabled: false, hapticEnabled: false });
    gesture();
    for (const type of Object.keys(TIER) as (keyof typeof TIER)[]) emit({ type });
    expect(contexts).toBe(0);
    expect(vibrate).not.toHaveBeenCalled();
  });

  it('tras el gesto y con los interruptores encendidos, un acierto suena y vibra 10 ms', () => {
    gesture();
    const r = emit({ type: 'correct' });
    expect(r).toEqual({ tier: 1, sounded: true, vibrated: true });
    expect(contexts).toBe(1);
    expect(oscillators).toBe(2); // C5 → E5
    expect(vibrate).toHaveBeenCalledWith([10]);
  });

  it('«no lo sé» no suena ni vibra: declararlo no se castiga ni se premia', () => {
    gesture();
    expect(emit({ type: 'idk' })).toEqual({ tier: 1, sounded: false, vibrated: false });
    expect(vibrate).not.toHaveBeenCalled();
  });

  it('el combo suena una nota más por multiplicador (×2 → 3, ×3 → 4, ×5 → 5)', () => {
    gesture();
    const notas = [2, 3, 5].map((value) => {
      const antes = oscillators;
      emit({ type: 'combo', value });
      return oscillators - antes;
    });
    expect(notas).toEqual([3, 4, 5]);
  });
});

describe('feedbackFx — coalescencia', () => {
  it('varios eventos a la vez: uno por nivel, y los de nivel 4 se guardan para el final', () => {
    gesture();
    const vistos: string[] = [];
    onFx((e) => vistos.push(e.type));
    emitMany([
      { type: 'correct' },
      { type: 'combo', value: 3 },
      { type: 'mission' },
      { type: 'level_up' },
      { type: 'badge' },
    ]);
    expect(vistos).toEqual(['correct', 'mission']);
    expect(takeCeremonies()).toEqual({
      ceremony: { type: 'level_up' },
      cards: [{ type: 'badge' }],
    });
    // Tomadas una vez, no vuelven.
    expect(takeCeremonies()).toEqual({ ceremony: null, cards: [] });
  });
});

describe('preferencias guardadas', () => {
  it('46.9 (ADR-67 D3): el sonido arranca encendido y sin elección registrada', () => {
    expect(useAppStore.getInitialState().soundEnabled).toBe(true);
    expect(useAppStore.getInitialState().soundChosen).toBe(false);
  });

  it('tocar el interruptor registra que el alumno eligió', () => {
    useAppStore.setState({ soundEnabled: true, soundChosen: false });
    useAppStore.getState().toggleSound();
    expect(useAppStore.getState()).toMatchObject({ soundEnabled: false, soundChosen: true });
  });

  it('migración v0 → v2: el true guardado antes de 46.2 (nadie lo eligió) queda encendido', async () => {
    const migrate = useAppStore.persist.getOptions().migrate!;
    const out = (await migrate({ soundEnabled: true, hapticEnabled: true, language: 'en' }, 0)) as Record<string, unknown>;
    expect(out).toMatchObject({ soundEnabled: true, soundChosen: false, hapticEnabled: true, language: 'en' });
  });

  it('migración v1 → v2: el false de 46.2 no distingue elección de valor forzado y pasa a encendido; el true se queda', async () => {
    const migrate = useAppStore.persist.getOptions().migrate!;
    expect(await migrate({ soundEnabled: false, language: 'es' }, 1)).toMatchObject({ soundEnabled: true, soundChosen: false });
    expect(await migrate({ soundEnabled: true, language: 'es' }, 1)).toMatchObject({ soundEnabled: true, soundChosen: false });
    expect(useAppStore.persist.getOptions().version).toBe(2);
  });

  it('la elección se guarda con el resto de preferencias', () => {
    const partialize = useAppStore.persist.getOptions().partialize!;
    const saved = partialize({ ...useAppStore.getState(), soundEnabled: false, soundChosen: true }) as Record<string, unknown>;
    expect(saved).toMatchObject({ soundEnabled: false, soundChosen: true });
  });
});
