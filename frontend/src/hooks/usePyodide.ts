/**
 * Hook that manages a Pyodide WebWorker lifecycle.
 *
 * Behaviour:
 *  - Worker is created once on mount and kept alive between runs.
 *  - `runCode(code, timeoutMs)` sends code to the worker and returns the result.
 *  - If execution exceeds `timeoutMs` (default 5 s), this thread interrupts the
 *    running Python via a SharedArrayBuffer the worker is watching, and the
 *    worker reports `timedOut: true` itself. The Pyodide instance survives, so
 *    a learner who writes an accidental infinite loop waits 5 s and can retry
 *    immediately.
 *  - Without cross-origin isolation there is no SharedArrayBuffer, so the
 *    fallback is to terminate the worker and boot a fresh one. That costs a
 *    full Pyodide reload (~3-5 s; served from our own origin since 12.9 and
 *    service-worker cached after the first load), which is why it is the
 *    fallback and not the design.
 *
 *  The interrupt has to be written from THIS thread: `runPython` is synchronous,
 *  so while user code runs the worker's own event loop is blocked and a timer
 *  set inside it can never fire. It used to be set inside it (task 12.11).
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
  /** Armed once the interrupt is signalled; see GRACE_MS. */
  killTimer: ReturnType<typeof setTimeout> | null;
}

/**
 * How long to wait for the interrupt to actually land before killing the worker.
 *
 * An interrupt is a request, not a guarantee: Python code is free to catch
 * KeyboardInterrupt, and `while True:` wrapped in `try/except KeyboardInterrupt`
 * swallows every SIGINT we send. Without this the promise would simply never
 * settle and the learner's UI would hang forever waiting on a run that already
 * refused to stop.
 */
const GRACE_MS = 2000;

/** Slot 0: Pyodide's interrupt signal. Slot 1: "this one was our deadline". */
const SLOT_SIGNAL = 0;
const SLOT_DEADLINE = 1;
const SIGINT = 2;

/**
 * Allocates the shared interrupt buffer, or null where SharedArrayBuffer is not
 * available — an insecure context, or a page that is not cross-origin isolated
 * (COOP + COEP; see vite.config.ts for dev and public/_headers for production).
 * Null is a supported degradation: the caller falls back to terminating.
 */
function makeInterruptBuffer(): Int32Array | null {
  try {
    if (typeof SharedArrayBuffer === 'undefined') return null;
    return new Int32Array(new SharedArrayBuffer(8));
  } catch {
    return null;
  }
}

function makeWorker(): Worker {
  return new Worker('/pyodide-worker.js');
}

export function usePyodide(disabled = false) {
  const workerRef = useRef<Worker | null>(null);
  const interruptRef = useRef<Int32Array | null>(null);
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
          clearTimeout(p.timer);
          if (p.killTimer !== null) clearTimeout(p.killTimer);
          pendingRef.current = null;
          setStatus('ready');
          // `timedOut` comes from the worker, which is the only side that knows
          // whether the interrupt actually landed. Hard-coding false here (as
          // this did before 12.11) threw away the answer the whole mechanism
          // exists to produce.
          p.resolve({
            output: data.output ?? '',
            error: data.error ?? null,
            timedOut: data.timedOut === true,
          });
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
    const buffer = makeInterruptBuffer();
    interruptRef.current = buffer;
    // Sent immediately: a worker queues messages until it registers its
    // listeners, so this cannot race with its Pyodide bootstrap.
    if (buffer) w.postMessage({ type: 'init', interruptBuffer: buffer });
  }, [attachWorker]);

  useEffect(() => {
    if (disabled) {
      setStatus('ready');
      return;
    }
    restartWorker();
    return () => {
      workerRef.current?.terminate();
      workerRef.current = null;
    };
  }, [disabled, restartWorker]);

  const runCode = useCallback(
    (code: string, timeoutMs = 5000): Promise<RunResult> => {
      if (status !== 'ready' || !workerRef.current) {
        return Promise.resolve({ output: '', error: 'Engine not ready', timedOut: false });
      }

      setStatus('running');
      const id = Math.random().toString(36).slice(2);

      return new Promise<RunResult>((resolve) => {
        const timer = setTimeout(() => {
          const buffer = interruptRef.current;
          if (buffer) {
            // Flag the deadline before signalling, so the worker can tell this
            // apart from a KeyboardInterrupt the user's own code raised. It
            // resolves through the normal 'result' path, with the output the
            // code managed to print before being stopped, and the Pyodide
            // instance stays alive for the next run.
            Atomics.store(buffer, SLOT_DEADLINE, 1);
            Atomics.store(buffer, SLOT_SIGNAL, SIGINT);
            const pending = pendingRef.current;
            if (pending) {
              pending.killTimer = setTimeout(() => {
                pendingRef.current = null;
                restartWorker();
                resolve({
                  output: '',
                  error: 'TimeoutError: code execution exceeded the time limit and ignored the interrupt',
                  timedOut: true,
                });
              }, GRACE_MS);
            }
            return;
          }
          // No SharedArrayBuffer: nothing can interrupt the blocked worker, so
          // the only way out is to kill it.
          pendingRef.current = null;
          restartWorker();
          resolve({ output: '', error: 'TimeoutError: code execution exceeded the time limit', timedOut: true });
        }, timeoutMs);

        pendingRef.current = { id, resolve, timer, killTimer: null };
        workerRef.current!.postMessage({ type: 'run', id, code });
      });
    },
    [status, restartWorker]
  );

  return { status, runCode };
}
