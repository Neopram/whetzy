// SQL runtime hook — mirrors usePyodide's interface but drives the sql-worker.
// The worker loads sql.js (SQLite WASM) self-hosted under /sql-js/ so no
// third-party CDN is involved (red line 5).
//
// Pass disabled=true to skip worker creation when the current question type
// is not sql_exec. Both useRuntime and this hook are always called (React
// rules), but only the active runtime actually boots its worker.

import { useCallback, useEffect, useRef, useState } from 'react';
import type { PyodideStatus, RunResult } from './usePyodide';

export type { PyodideStatus, RunResult };

function makeWorker(): Worker {
  return new Worker('/sql-worker.js');
}

interface Pending {
  id: string;
  resolve: (r: RunResult) => void;
}

export function useSqlRuntime(disabled = false) {
  const workerRef = useRef<Worker | null>(null);
  const pendingRef = useRef<Pending | null>(null);
  const [status, setStatus] = useState<PyodideStatus>(disabled ? 'ready' : 'loading');

  const attachWorker = useCallback((w: Worker) => {
    w.onmessage = ({ data }) => {
      if (data.type === 'ready') {
        setStatus('ready');
      } else if (data.type === 'loadError') {
        setStatus('error');
      } else if (data.type === 'result') {
        const p = pendingRef.current;
        if (p && p.id === data.id) {
          pendingRef.current = null;
          setStatus('ready');
          p.resolve({
            output: data.output ?? '',
            error: data.error ?? null,
            timedOut: false,
          });
        }
      }
    };
    w.onerror = () => {
      setStatus('error');
      // Sin esto la ejecución en curso no resolvía nunca y la pregunta quedaba colgada.
      const p = pendingRef.current;
      pendingRef.current = null;
      p?.resolve({ output: '', error: 'SQL engine crashed', timedOut: false });
    };
  }, []);

  useEffect(() => {
    if (disabled) {
      setStatus('ready');
      return;
    }
    // Reset to 'loading' so the run button stays disabled until the worker
    // actually sends 'ready'.  Without this, the status is stale at 'ready'
    // from the prior disabled=true phase, the button looks enabled while sql.js
    // is still loading, runCode() posts a message the worker silently drops
    // (SQL===null guard), and the output box never appears (race in 16.9).
    setStatus('loading');
    const w = makeWorker();
    workerRef.current = w;
    attachWorker(w);
    return () => {
      w.terminate();
      workerRef.current = null;
    };
  }, [disabled, attachWorker]);

  const runCode = useCallback(
    (code: string, timeoutMs = 5000): Promise<RunResult> => {
      if (disabled || !workerRef.current) {
        return Promise.resolve({ output: '', error: 'SQL engine not active', timedOut: false });
      }
      if (status !== 'ready') {
        return Promise.resolve({ output: '', error: 'SQL engine not ready', timedOut: false });
      }

      setStatus('running');
      const id = Math.random().toString(36).slice(2);

      return new Promise<RunResult>((resolve) => {
        // sql.js no se puede interrumpir: un CTE recursivo sin LIMIT ocupaba el
        // worker para siempre. Al agotar el tiempo se mata y se arranca otro.
        const timer = setTimeout(() => {
          if (pendingRef.current?.id !== id) return;
          pendingRef.current = null;
          workerRef.current?.terminate();
          setStatus('loading');
          const fresh = makeWorker();
          workerRef.current = fresh;
          attachWorker(fresh);
          resolve({ output: '', error: null, timedOut: true });
        }, timeoutMs);
        pendingRef.current = {
          id,
          resolve: (r) => {
            clearTimeout(timer);
            resolve(r);
          },
        };
        workerRef.current!.postMessage({ type: 'run', id, code });
      });
    },
    [disabled, status, attachWorker]
  );

  return { status, runCode };
}
