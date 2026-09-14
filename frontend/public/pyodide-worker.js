// Pyodide WebWorker — hardened sandbox with import blocking and a 5-second
// timeout enforced by the MAIN thread (see the note on interruptBuffer below).
// Messages IN:  { type: 'init', interruptBuffer: Int32Array on a SharedArrayBuffer }
//               { type: 'run', id: string, code: string }
// Messages OUT: { type: 'ready' }
//               { type: 'result', id, output, error, timedOut }
//               { type: 'loadError', message }

// Same-origin, served by pyodideSelfHostPlugin in vite.config.ts from the
// pinned `pyodide` dependency — never a third-party CDN (task 12.9, red line 5).
importScripts('/pyodide/pyodide.js');

const TIMEOUT_MS = 5_000;

// Python modules that user code may not import (security-sensitive).
const BLOCKED_MODULES = [
  'os', 'subprocess', 'socket', 'multiprocessing', 'threading',
  'ctypes', 'cffi', 'signal', 'mmap', 'fcntl',
  'posix', 'nt', 'pwd', 'grp',
  'shutil', 'pathlib', 'tempfile', 'glob', 'fnmatch',
  '_posixsubprocess', '_winapi', 'winreg', 'winsound',
];

// Python snippet prepended to every user snippet: overrides builtins.__import__ so
// blocked modules are rejected even when already present in sys.modules.
// Uses a factory function so `blocked` and `orig` are captured by value in the
// factory's local scope — not as closures over deletable names (avoids NameError).
// Idempotent: skips reinstall when __sandbox__ guard attribute is already set.
const SANDBOX_PREAMBLE = `
import builtins as _b
if not getattr(_b.__import__, '__sandbox__', False):
    def _make_guard(orig, blocked):
        def _safe_import(name, *args, **kwargs):
            if name.split('.')[0] in blocked:
                raise ImportError("import '{}' is not allowed in this sandbox".format(name))
            return orig(name, *args, **kwargs)
        _safe_import.__sandbox__ = True
        return _safe_import
    _b.__import__ = _make_guard(_b.__import__, frozenset(${JSON.stringify(BLOCKED_MODULES)}))
    del _make_guard
del _b
`;

let pyodide = null;

/**
 * Int32Array over a SharedArrayBuffer, created and owned by the MAIN thread.
 *
 * It has to come from there, and that is the whole point of task 12.11. This
 * worker used to allocate the buffer itself and arm a `setTimeout` here to
 * write the interrupt — which can never fire: `pyodide.runPython` is
 * synchronous, so while user code runs (`while True: pass` being the case that
 * matters) this worker's event loop is blocked and no callback of its own will
 * ever execute. The writer must be a different thread. A SharedArrayBuffer is
 * precisely the mechanism for that, and it was being used to talk to nobody.
 *
 * Slot 0 is Pyodide's own interrupt signal (2 = SIGINT -> KeyboardInterrupt),
 * written by the main thread.
 * Slot 1 is ours: the main thread sets it to 1 just before signalling, so this
 * worker can tell "the deadline killed it" from "the user's own code raised
 * KeyboardInterrupt" and report `timedOut` honestly either way.
 */
let interruptBuffer = null;
const SLOT_SIGNAL = 0;
const SLOT_DEADLINE = 1;

(async () => {
  try {
    pyodide = await loadPyodide({
      indexURL: '/pyodide/',
    });

    // If the main thread already sent its buffer, wire it up now; if it has not
    // yet, the 'init' handler below does it. Either order works, because a
    // worker queues messages until its listeners are registered.
    applyInterruptBuffer();

    // Pre-import io/sys so first run doesn't pay the import cost.
    pyodide.runPython('import io, sys');
    self.postMessage({ type: 'ready' });
  } catch (err) {
    self.postMessage({ type: 'loadError', message: String(err) });
  }
})();

/**
 * Hands the main thread's buffer to Pyodide once both exist. Called from the
 * bootstrap and from the 'init' handler, whichever happens second.
 *
 * Cross-origin isolation (COOP + COEP) is what makes SharedArrayBuffer
 * available at all; without it the main thread sends nothing and this stays
 * null, which is a supported degradation, not a failure — the main thread then
 * falls back to terminating the worker. That path costs a full Pyodide reboot,
 * so it is the fallback rather than the design.
 */
function applyInterruptBuffer() {
  if (!pyodide || !interruptBuffer) return;
  try {
    pyodide.setInterruptBuffer(interruptBuffer);
  } catch {
    interruptBuffer = null;
  }
}

self.addEventListener('message', ({ data }) => {
  if (data.type === 'init') {
    interruptBuffer = data.interruptBuffer ?? null;
    applyInterruptBuffer();
    return;
  }
  if (data.type !== 'run') return;
  const { id, code } = data;

  if (!pyodide) {
    self.postMessage({ type: 'result', id, output: '', error: 'Engine not ready', timedOut: false });
    return;
  }

  let output = '';
  let error = null;
  let timedOut = false;

  // Clear both slots so a signal left over from a previous run cannot interrupt
  // this one. The deadline itself is armed by the main thread, not here.
  if (interruptBuffer) {
    Atomics.store(interruptBuffer, SLOT_SIGNAL, 0);
    Atomics.store(interruptBuffer, SLOT_DEADLINE, 0);
  }

  try {
    // Redirect stdout + stderr into a single buffer.
    pyodide.runPython(
      '_nbuf = __import__("io").StringIO()\n' +
      '__import__("sys").stdout = _nbuf\n' +
      '__import__("sys").stderr = _nbuf'
    );
    // Install import restrictions, then execute user code.
    pyodide.runPython(SANDBOX_PREAMBLE + '\n' + code);
    output = pyodide.runPython('_nbuf.getvalue()');
  } catch (err) {
    try { output = pyodide.runPython('_nbuf.getvalue()'); } catch { /* nothing captured yet */ }
    // The main thread flags the deadline before signalling, so a KeyboardInterrupt
    // raised by the user's own code is not misreported as a timeout.
    if (interruptBuffer && Atomics.load(interruptBuffer, SLOT_DEADLINE) === 1) {
      timedOut = true;
      error = `TimeoutError: code execution exceeded ${TIMEOUT_MS / 1000} seconds`;
    } else {
      // Pyodide wraps Python exceptions in a JS PythonError whose err.message may
      // be empty or just "PythonError".  The real traceback is often captured in
      // the redirected stderr (`output`).  Use the last non-empty output line when
      // it looks like a Python exception; otherwise fall back to String(err).
      const msg = (err instanceof Error && err.message) ? err.message : String(err);
      const msgLines = msg.split('\n').filter(Boolean);
      const lastMsgLine = msgLines[msgLines.length - 1] || msg;
      if (lastMsgLine === 'PythonError' || lastMsgLine === String(err)) {
        const outLines = output.trim().split('\n').filter(Boolean);
        const lastOutLine = outLines[outLines.length - 1] || '';
        error = /Error|Exception/.test(lastOutLine) ? lastOutLine : lastMsgLine;
      } else {
        error = lastMsgLine;
      }
    }
  } finally {
    if (interruptBuffer) {
      Atomics.store(interruptBuffer, SLOT_SIGNAL, 0);
      Atomics.store(interruptBuffer, SLOT_DEADLINE, 0);
    }
    try {
      pyodide.runPython(
        '__import__("sys").stdout = __import__("sys").__stdout__\n' +
        '__import__("sys").stderr = __import__("sys").__stderr__'
      );
    } catch { /* ignore cleanup errors */ }
  }

  self.postMessage({ type: 'result', id, output, error, timedOut });
});
