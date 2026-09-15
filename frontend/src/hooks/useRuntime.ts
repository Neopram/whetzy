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
//   'js'     — stub (future: sandboxed JS Worker or iframe)

import { usePyodide } from './usePyodide';
import { useSqlRuntime } from './useSqlRuntime';
import type { RunResult } from './usePyodide';

export type RuntimeType = 'python' | 'sql' | 'js';

const JS_STUB_RESULT: RunResult = {
  output: '',
  error: 'JS runtime not yet available',
  timedOut: false,
};

export function useRuntime(type: RuntimeType) {
  const python = usePyodide(type !== 'python');
  const sql = useSqlRuntime(type !== 'sql');

  if (type === 'sql') return { status: sql.status, runCode: sql.runCode };
  if (type === 'js') {
    return {
      status: 'ready' as const,
      runCode: (_code: string) => Promise.resolve(JS_STUB_RESULT),
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
