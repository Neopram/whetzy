/**
 * 46.2b (ADR-67 D4): en la app nativa la vibración sale por
 * `@capacitor/haptics` (impacto o notificación según el evento); en web sigue
 * `navigator.vibrate`. El plugin se importa solo en nativo, así que el bundle
 * web no lo carga. Las mismas puertas que 46.2: primer gesto e interruptor.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { _resetFeedbackFx, armFeedbackFx, emit } from '../lib/feedbackFx';
import { useAppStore } from '../stores/useAppStore';

const haptics = vi.hoisted(() => ({ impact: vi.fn(() => Promise.resolve()), notification: vi.fn(() => Promise.resolve()) }));
vi.mock('@capacitor/haptics', () => ({ Haptics: haptics }));

const vibrate = vi.fn(() => true);
const flush = () => new Promise((r) => setTimeout(r, 0));

function native(on: boolean) {
  (window as unknown as { Capacitor?: unknown }).Capacitor = on ? { isNativePlatform: () => true } : undefined;
}

beforeEach(() => {
  _resetFeedbackFx();
  haptics.impact.mockClear();
  haptics.notification.mockClear();
  vibrate.mockClear();
  Object.defineProperty(navigator, 'vibrate', { value: vibrate, configurable: true, writable: true });
  useAppStore.setState({ soundEnabled: false, hapticEnabled: true });
  armFeedbackFx();
  window.dispatchEvent(new Event('pointerdown'));
});
afterEach(() => native(false));

describe('feedbackFx — vibración nativa (46.2b)', () => {
  it('en nativo, un acierto es un impacto ligero y no se llama a navigator.vibrate', async () => {
    native(true);
    expect(emit({ type: 'correct' }).vibrated).toBe(true);
    await flush();
    expect(haptics.impact).toHaveBeenCalledWith({ style: 'LIGHT' });
    expect(vibrate).not.toHaveBeenCalled();
  });

  it('en nativo, un fallo es una notificación de aviso y una ceremonia una de éxito', async () => {
    native(true);
    emit({ type: 'wrong' });
    emit({ type: 'level_up' });
    await flush();
    expect(haptics.notification).toHaveBeenCalledWith({ type: 'WARNING' });
    expect(haptics.notification).toHaveBeenCalledWith({ type: 'SUCCESS' });
  });

  it('con el interruptor apagado, nada vibra tampoco en nativo', async () => {
    native(true);
    useAppStore.setState({ hapticEnabled: false });
    expect(emit({ type: 'correct' }).vibrated).toBe(false);
    await flush();
    expect(haptics.impact).not.toHaveBeenCalled();
  });

  it('en web sigue navigator.vibrate y el plugin no se usa', async () => {
    emit({ type: 'correct' });
    await flush();
    expect(vibrate).toHaveBeenCalledWith([10]);
    expect(haptics.impact).not.toHaveBeenCalled();
  });

  it('«no lo sé» no vibra en ninguno de los dos', async () => {
    native(true);
    expect(emit({ type: 'idk' }).vibrated).toBe(false);
    await flush();
    expect(haptics.impact).not.toHaveBeenCalled();
    expect(haptics.notification).not.toHaveBeenCalled();
  });
});
