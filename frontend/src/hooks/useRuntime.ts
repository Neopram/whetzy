// Unified runtime abstraction over Python (Pyodide), SQL (sql.js), and JS.
//
// Both usePyodide and useSqlRuntime are always called unconditionally (React
// hook rules). Each accepts a `disabled` flag so only the active runtime
// actually creates its worker. Passing the runtime type to this hook routes
// the returned { status, runCode } to the correct underlying runtime.
//
// Supported runtimes:
//   'python' — Pyodide WASM, used for fill_blank_exec and fix_bug questions
//   'sql'    — sql.js WASM (SQLite), used for sql_exec questions
//   'js'     — Blob URL Web Worker sandbox: no eval on main thread, console
//              captured, timeout via terminate(), no DOM access

import { usePyodide } from './usePyodide';
import { useSqlRuntime } from './useSqlRuntime';
import type { RunResult } from './usePyodide';

export type RuntimeType = 'python' | 'sql' | 'js';

// Worker source is inlined as a string so it can be loaded via Blob URL with
// no extra build step and no CDN dependency (red line 5). The Worker has no
// DOM access by design (Workers never do), and `new Function` runs in the
// Worker global scope — isolated from the main thread. console.log/warn/error/
// info are all redirected to the logs array so the learner sees full output.
const JS_WORKER_SRC = `
self.onmessage = function(e) {
  var logs = [];
  var _log = function() {
    var args = Array.prototype.slice.call(arguments);
    logs.push(args.map(function(x) {
      return typeof x === 'object' ? JSON.stringify(x) : String(x);
    }).join(' '));
  };
  var c = { log: _log, error: _log, warn: _log, info: _log, debug: _log };
  try {
    new Function('console', e.data.code)(c);
    self.postMessage({ output: logs.join('\\n'), error: null, timedOut: false });
  } catch (err) {
    self.postMessage({ output: logs.join('\\n'), error: err.message, timedOut: false });
  }
};
`;

function runJs(code: string, timeoutMs = 5000): Promise<RunResult> {
  return new Promise<RunResult>((resolve) => {
    const blob = new Blob([JS_WORKER_SRC], { type: 'application/javascript' });
    const url = URL.createObjectURL(blob);
    const worker = new Worker(url);
    let settled = false;
    const settle = (result: RunResult) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      worker.terminate();
      URL.revokeObjectURL(url);
      resolve(result);
    };
    const timer = setTimeout(() => {
      settle({ output: '', error: null, timedOut: true });
    }, timeoutMs);
    worker.onmessage = (e) => settle(e.data as RunResult);
    worker.onerror = (e) => settle({ output: '', error: e.message ?? 'Worker error', timedOut: false });
    worker.postMessage({ code });
  });
}

export function useRuntime(type: RuntimeType) {
  const python = usePyodide(type !== 'python');
  const sql = useSqlRuntime(type !== 'sql');

  if (type === 'sql') return { status: sql.status, runCode: sql.runCode };
  if (type === 'js') {
    return {
      status: 'ready' as const,
      runCode: runJs,
    };
  }
  return { status: python.status, runCode: python.runCode };
}

/** Derive the runtime type from a question type string. */
export function runtimeForQuestion(questionType?: string): RuntimeType {
  if (questionType === 'sql_exec') return 'sql';
  if (questionType === 'js_exec') return 'js';
  return 'python';
}
