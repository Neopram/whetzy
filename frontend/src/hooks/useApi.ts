import { useEffect, useState, useCallback, useRef } from 'react';

interface State<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/** Minimal fetch-on-mount hook. `deps` re-runs the fetcher when they change. */
export function useApi<T>(fetcher: () => Promise<T>, deps: unknown[] = []): State<T> & { reload: () => void } {
  const [state, setState] = useState<State<T>>({ data: null, loading: true, error: null });
  // Cancela la petición anterior, venga del efecto o de `reload()`: si no, la
  // respuesta tardía de un reintento pisaba la de unos deps nuevos (§7 de 43.5).
  const cancelPrevious = useRef<() => void>(() => {});

  const run = useCallback(() => {
    cancelPrevious.current();
    let cancelled = false;
    const cancel = () => { cancelled = true; };
    cancelPrevious.current = cancel;
    setState((s) => ({ ...s, loading: true, error: null }));
    fetcher()
      .then((data) => { if (!cancelled) setState({ data, loading: false, error: null }); })
      .catch((e) => { if (!cancelled) setState({ data: null, loading: false, error: e instanceof Error ? e.message : 'Error' }); });
    return cancel;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(run, [run]);

  return { ...state, reload: run };
}
