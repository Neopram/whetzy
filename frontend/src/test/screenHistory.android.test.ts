/**
 * 42.10: el botón «atrás» de Android. En la WebView de Capacitor, sin un
 * listener de `@capacitor/app`, el botón cierra la app desde cualquier
 * pantalla. Con historial de pantallas debe volver (`history.back`, que
 * recoge el `popstate` de `useScreenHistory`); sin historial, cerrar la app.
 * En web no se registra nada.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

type BackListener = (e: { canGoBack: boolean }) => void;

const cap = vi.hoisted(() => ({ native: false }));
const app = vi.hoisted(() => ({
  listeners: [] as ((e: { canGoBack: boolean }) => void)[],
  remove: vi.fn(() => Promise.resolve()),
  exitApp: vi.fn(() => Promise.resolve()),
  addListener: vi.fn(),
}));

vi.mock('@capacitor/core', () => ({ Capacitor: { isNativePlatform: () => cap.native } }));
vi.mock('@capacitor/app', () => ({ App: { addListener: app.addListener, exitApp: app.exitApp } }));

import { _resetNativeBackButton, installNativeBackButton } from '../lib/screenHistory';

const press = (canGoBack: boolean) => app.listeners.forEach((l) => l({ canGoBack }));

beforeEach(() => {
  _resetNativeBackButton();
  app.listeners = [];
  app.remove.mockClear();
  app.exitApp.mockClear();
  app.addListener.mockReset();
  app.addListener.mockImplementation((event: string, fn: BackListener) => {
    if (event === 'backButton') app.listeners.push(fn);
    return Promise.resolve({ remove: app.remove });
  });
});
afterEach(() => {
  cap.native = false;
  vi.restoreAllMocks();
});

describe('botón atrás de Android (42.10)', () => {
  it('en nativo, con historial de pantallas, vuelve a la anterior', async () => {
    cap.native = true;
    const back = vi.spyOn(window.history, 'back').mockImplementation(() => {});
    await installNativeBackButton();
    expect(app.addListener).toHaveBeenCalledWith('backButton', expect.any(Function));
    press(true);
    expect(back).toHaveBeenCalledTimes(1);
    expect(app.exitApp).not.toHaveBeenCalled();
  });

  it('en nativo, sin historial, cierra la app', async () => {
    cap.native = true;
    const back = vi.spyOn(window.history, 'back').mockImplementation(() => {});
    await installNativeBackButton();
    press(false);
    expect(app.exitApp).toHaveBeenCalledTimes(1);
    expect(back).not.toHaveBeenCalled();
  });

  it('en web no se registra ningún listener', async () => {
    cap.native = false;
    await installNativeBackButton();
    expect(app.addListener).not.toHaveBeenCalled();
  });

  it('llamarla dos veces no registra dos listeners, y se puede quitar', async () => {
    cap.native = true;
    const [off1, off2] = await Promise.all([installNativeBackButton(), installNativeBackButton()]);
    await installNativeBackButton();
    expect(app.addListener).toHaveBeenCalledTimes(1);
    off1();
    off2();
    await vi.waitFor(() => expect(app.remove).toHaveBeenCalledTimes(1));
    // Quitado, se puede volver a instalar.
    await installNativeBackButton();
    expect(app.addListener).toHaveBeenCalledTimes(2);
  });
});
