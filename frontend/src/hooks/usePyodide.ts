/**
 * Hook that manages a Pyodide WebWorker lifecycle.
 *
 * Behaviour:
 *  - Worker is created once on mount and kept alive between runs.
 *  - `runCode(code, timeoutMs)` sends code to the worker and returns the result.
 *  - If execution exceeds `timeoutMs` (default 5 s), the worker is terminated
 *    and a fresh one is started.  Pyodide reload takes ~3-5 s (served from
 *    our own origin since 12.9 and cached by the service worker after the
 *    first load), so keep timeouts generous for the UX.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

export type PyodideStatus = 'loading' | 'ready' | 'running' | 'error';

export interface RunResult {
  output: string;
  error: string | null;
  timedOut: boolean;
}

interface Pending {
  id: string;
  resolve: (r: RunResult) => void;
  timer: ReturnType<typeof setTimeout>;
}

function makeWorker(): Worker {
  return new Worker('/pyodide-worker.js');
}

export function usePyodide() {
  const workerRef = useRef<Worker | null>(null);
  const pendingRef = useRef<Pending | null>(null);
  const [status, setStatus] = useState<PyodideStatus>('loading');

  const attachWorker = useCallback((w: Worker) => {
    w.onmessage = ({ data }) => {
      if (data.type === 'ready') {
        setStatus('ready');
      } else if (data.type === 'loadError') {
        setStatus('error');
      } else if (data.type === 'result') {
        const p = pendingRef.current;
        if (p && p.id === data.id) {
          clearTimeout(p.timer);
          pendingRef.current = null;
          setStatus('ready');
          p.resolve({ output: data.output ?? '', error: data.error ?? null, timedOut: false });
        }
      }
    };
    w.onerror = () => setStatus('error');
  }, []);

  const restartWorker = useCallback(() => {
    workerRef.current?.terminate();
    setStatus('loading');
    const w = makeWorker();
    workerRef.current = w;
    attachWorker(w);
  }, [attachWorker]);

  useEffect(() => {
    restartWorker();
    return () => {
      workerRef.current?.terminate();
      workerRef.current = null;
    };
  }, [restartWorker]);

  const runCode = useCallback(
    (code: string, timeoutMs = 5000): Promise<RunResult> => {
      if (status !== 'ready' || !workerRef.current) {
        return Promise.resolve({ output: '', error: 'Engine not ready', timedOut: false });
      }

      setStatus('running');
      const id = Math.random().toString(36).slice(2);

      return new Promise<RunResult>((resolve) => {
        const timer = setTimeout(() => {
          pendingRef.current = null;
          restartWorker(); // kills the hung worker, boots a fresh one
          resolve({ output: '', error: null, timedOut: true });
        }, timeoutMs);

        pendingRef.current = { id, resolve, timer };
        workerRef.current!.postMessage({ type: 'run', id, code });
      });
    },
    [status, restartWorker]
  );

  return { status, runCode };
}
