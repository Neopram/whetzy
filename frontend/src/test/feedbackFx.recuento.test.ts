/**
 * 46.7b (docs/PLAN_UI_AVANZADA.md §6.1): el cierre de sesión suena como un
 * tic a 12 Hz durante el recuento (1 s) y una nota final según la nota S–F.
 * Si el alumno salta el recuento, `cancelFx()` corta lo que quede.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { _resetFeedbackFx, armFeedbackFx, cancelFx, emit, GRADE_RANK } from '../lib/feedbackFx';
import { useAppStore } from '../stores/useAppStore';

let oscillators = 0;
let cancelled = 0;

class FakeParam {
  value = 0;
  setValueAtTime() { return this; }
  exponentialRampToValueAtTime() { return this; }
}
class FakeNode {
  frequency = new FakeParam();
  gain = new FakeParam();
  type = '';
  connect(n: unknown) { return n; }
  start() { /* */ }
  stop(when?: number) { if (when === undefined) cancelled++; }
}
class FakeAudioContext {
  currentTime = 0;
  sampleRate = 8000;
  state = 'running';
  destination = {};
  createOscillator() { oscillators++; return new FakeNode(); }
  createGain() { return new FakeNode(); }
  // El búfer mudo con que 46.2c despierta el audio en el primer toque.
  createBufferSource() { return new FakeNode(); }
  createBuffer(_c: number, len: number) { return { getChannelData: () => new Float32Array(len) }; }
  resume() { return Promise.resolve(); }
}

beforeEach(() => {
  _resetFeedbackFx();
  oscillators = 0;
  cancelled = 0;
  vi.stubGlobal('AudioContext', FakeAudioContext);
  useAppStore.setState({ soundEnabled: true, hapticEnabled: false });
  armFeedbackFx();
  window.dispatchEvent(new Event('pointerdown'));
});
afterEach(() => vi.unstubAllGlobals());

describe('feedbackFx — cierre de sesión con recuento (46.7b)', () => {
  it('nota S: 12 tics y la nota final de tres tonos', () => {
    expect(emit({ type: 'session_end', value: GRADE_RANK.S }).sounded).toBe(true);
    expect(oscillators).toBe(12 + 3);
  });

  it('nota F: 12 tics y un solo tono, sin fanfarria', () => {
    emit({ type: 'session_end', value: GRADE_RANK.F });
    expect(oscillators).toBe(12 + 1);
  });

  it('sin nota (llamada antigua) suena como antes, sin tics', () => {
    emit({ type: 'session_end' });
    expect(oscillators).toBe(2);
  });

  it('saltar corta todo lo programado del recuento', () => {
    emit({ type: 'session_end', value: GRADE_RANK.A });
    cancelFx();
    expect(cancelled).toBe(12 + 2);
    // Lo ya cortado no se vuelve a cortar.
    cancelFx();
    expect(cancelled).toBe(12 + 2);
  });
});
