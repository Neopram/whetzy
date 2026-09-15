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
    w.onerror = () => setStatus('error');
  }, []);

  useEffect(() => {
    if (disabled) {
      setStatus('ready');
      return;
    }
    const w = makeWorker();
    workerRef.current = w;
    attachWorker(w);
    return () => {
      w.terminate();
      workerRef.current = null;
    };
  }, [disabled, attachWorker]);

  const runCode = useCallback(
    (code: string): Promise<RunResult> => {
      if (disabled || !workerRef.current) {
        return Promise.resolve({ output: '', error: 'SQL engine not active', timedOut: false });
      }
      if (status !== 'ready') {
        return Promise.resolve({ output: '', error: 'SQL engine not ready', timedOut: false });
      }

      setStatus('running');
      const id = Math.random().toString(36).slice(2);

      return new Promise<RunResult>((resolve) => {
        pendingRef.current = { id, resolve };
        workerRef.current!.postMessage({ type: 'run', id, code });
      });
    },
    [disabled, status]
  );

  return { status, runCode };
}
