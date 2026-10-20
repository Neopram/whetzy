/**
 * 46.2c: el audio se enciende dentro del primer toque y los interruptores dan
 * una muestra al encenderse.
 *
 * El sonido se emite cuando el servidor contesta, fuera del gesto. En Safari
 * de iOS un AudioContext creado o reanudado fuera de un gesto se queda en
 * silencio; por eso el contexto se crea y se desbloquea (búfer mudo) en el
 * primer `pointerdown`. Encender un interruptor en Perfil suena o vibra en ese
 * mismo toque: el alumno comprueba al momento si su aparato lo hace.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { _resetFeedbackFx, armFeedbackFx, emit, preview } from '../lib/feedbackFx';
import { useAppStore } from '../stores/useAppStore';

let contexts = 0;
let oscillators = 0;
let bufferStarts = 0;
let resumes = 0;
let ctxState = 'suspended';

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
  constructor(private kind: 'osc' | 'buf' | 'other' = 'other') {}
  connect(n: unknown) { return n; }
  start() { if (this.kind === 'buf') bufferStarts++; }
  stop() { /* */ }
}
class FakeAudioContext {
  currentTime = 0;
  sampleRate = 8000;
  destination = {};
  get state() { return ctxState; }
  constructor() { contexts++; }
  createOscillator() { oscillators++; return new FakeNode('osc'); }
  createGain() { return new FakeNode(); }
  createBiquadFilter() { return new FakeNode(); }
  createBufferSource() { return new FakeNode('buf'); }
  createBuffer(_c: number, len: number) { return { getChannelData: () => new Float32Array(len) }; }
  resume() { resumes++; ctxState = 'running'; return Promise.resolve(); }
}

const vibrate = vi.fn(() => true);

beforeEach(() => {
  _resetFeedbackFx();
  contexts = 0;
  oscillators = 0;
  bufferStarts = 0;
  resumes = 0;
  ctxState = 'suspended';
  vibrate.mockClear();
  vi.stubGlobal('AudioContext', FakeAudioContext);
  Object.defineProperty(navigator, 'vibrate', { value: vibrate, configurable: true, writable: true });
  useAppStore.setState({ soundEnabled: true, hapticEnabled: true });
  armFeedbackFx();
});
afterEach(() => vi.unstubAllGlobals());

describe('feedbackFx — primer toque (46.2c)', () => {
  it('con el sonido encendido, el primer toque crea, reanuda y desbloquea el audio', () => {
    window.dispatchEvent(new Event('pointerdown'));
    expect(contexts).toBe(1);
    expect(resumes).toBe(1);
    expect(bufferStarts).toBe(1); // el búfer mudo que desbloquea iOS
  });

  it('lo que suena después (al contestar el servidor) reutiliza ese contexto', () => {
    window.dispatchEvent(new Event('pointerdown'));
    emit({ type: 'correct' });
    expect(contexts).toBe(1);
    expect(oscillators).toBe(2);
  });

  it('con el sonido apagado, el primer toque no crea ningún AudioContext', () => {
    useAppStore.setState({ soundEnabled: false });
    window.dispatchEvent(new Event('pointerdown'));
    expect(contexts).toBe(0);
  });

  it('también desbloquea con teclado', () => {
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    expect(bufferStarts).toBe(1);
  });
});

describe('feedbackFx — muestra al encender (46.2c)', () => {
  it('preview("sound") suena y no vibra', () => {
    window.dispatchEvent(new Event('pointerdown'));
    expect(preview('sound')).toBe(true);
    expect(oscillators).toBeGreaterThan(0);
    expect(vibrate).not.toHaveBeenCalled();
  });

  it('preview("haptic") vibra y no suena', () => {
    window.dispatchEvent(new Event('pointerdown'));
    expect(preview('haptic')).toBe(true);
    expect(vibrate).toHaveBeenCalledWith([10]);
    expect(oscillators).toBe(0);
  });

  it('con su interruptor apagado, la muestra no hace nada', () => {
    useAppStore.setState({ soundEnabled: false, hapticEnabled: false });
    window.dispatchEvent(new Event('pointerdown'));
    expect(preview('sound')).toBe(false);
    expect(preview('haptic')).toBe(false);
    expect(contexts).toBe(0);
    expect(vibrate).not.toHaveBeenCalled();
  });
});
