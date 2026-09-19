import '@testing-library/jest-dom';

// Polyfill localStorage for jsdom
const store: Record<string, string> = {};
const localStorageMock = {
  getItem: (key: string) => store[key] ?? null,
  setItem: (key: string, value: string) => { store[key] = value; },
  removeItem: (key: string) => { delete store[key]; },
  clear: () => { Object.keys(store).forEach(k => delete store[k]); },
  get length() { return Object.keys(store).length; },
  key: (i: number) => Object.keys(store)[i] ?? null,
};
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock });

// jsdom trae ni Worker ni URL.createObjectURL, y useRuntime('js') usa los dos
// (JS_WORKER_SRC -> Blob -> new Worker(url)). Sin este doble, el test de
// useRuntime muere con `ReferenceError: Worker is not defined` (22.9).
//
// El doble ejecuta el codigo EN EL MISMO hilo reproduciendo el contrato del
// worker real de src/hooks/useRuntime.ts: recibe {code}, captura console.* y
// responde {output, error, timedOut}. Sirve para probar el cableado de runJs
// (promesa, timeout, settle una sola vez, terminate); **NO prueba el aislamiento
// real**, que solo existe en un navegador de verdad y se cubre en e2e.
class FakeWorker {
  onmessage: ((e: { data: unknown }) => void) | null = null;
  onerror: ((e: { message?: string }) => void) | null = null;
  terminated = false;

  postMessage(data: { code: string }): void {
    const logs: string[] = [];
    const log = (...args: unknown[]) => {
      logs.push(args.map(x => (typeof x === 'object' && x !== null ? JSON.stringify(x) : String(x))).join(' '));
    };
    const console_ = { log, error: log, warn: log, info: log, debug: log };
    let error: string | null = null;
    try {
      new Function('console', data.code)(console_);
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    }
    queueMicrotask(() => {
      if (this.terminated) return;
      this.onmessage?.({ data: { output: logs.join('\n'), error, timedOut: false } });
    });
  }

  terminate(): void {
    this.terminated = true;
  }
}

// `configurable: true` es obligatorio: hooks.useSqlRuntime.test.tsx sustituye
// este doble por el suyo con `vi.stubGlobal('Worker', ...)`, y stubGlobal usa
// defineProperty — con la propiedad no configurable, sus 14 tests se caen.
Object.defineProperty(globalThis, 'Worker', {
  value: FakeWorker,
  writable: true,
  configurable: true,
});

if (typeof URL.createObjectURL !== 'function') {
  URL.createObjectURL = () => 'blob:fake';
  URL.revokeObjectURL = () => undefined;
}
