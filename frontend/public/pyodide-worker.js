// Pyodide WebWorker — hardened sandbox with import blocking and 5-second timeout.
// Messages IN:  { type: 'run', id: string, code: string }
// Messages OUT: { type: 'ready' }
//               { type: 'result', id, output, error, timedOut }
//               { type: 'loadError', message }

importScripts('https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.js');

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
let interruptBuffer = null;  // Int32Array on SharedArrayBuffer, or null

(async () => {
  try {
    pyodide = await loadPyodide({
      indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.2/full/',
    });

    // SharedArrayBuffer-based interrupt requires COOP + COEP headers.
    try {
      if (typeof SharedArrayBuffer !== 'undefined') {
        interruptBuffer = new Int32Array(new SharedArrayBuffer(4));
        pyodide.setInterruptBuffer(interruptBuffer);
      }
    } catch {
      interruptBuffer = null;
    }

    // Pre-import io/sys so first run doesn't pay the import cost.
    pyodide.runPython('import io, sys');
    self.postMessage({ type: 'ready' });
  } catch (err) {
    self.postMessage({ type: 'loadError', message: String(err) });
  }
})();

self.addEventListener('message', ({ data }) => {
  if (data.type !== 'run') return;
  const { id, code } = data;

  if (!pyodide) {
    self.postMessage({ type: 'result', id, output: '', error: 'Engine not ready', timedOut: false });
    return;
  }

  let output = '';
  let error = null;
  let timedOut = false;

  // Arm the interrupt timer (only effective when interruptBuffer is set).
  let timeoutHandle = null;
  if (interruptBuffer) {
    interruptBuffer[0] = 0;
    timeoutHandle = setTimeout(() => {
      timedOut = true;
      Atomics.store(interruptBuffer, 0, 2);  // SIGINT → KeyboardInterrupt in Python
    }, TIMEOUT_MS);
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
    if (timedOut) {
      error = 'TimeoutError: code execution exceeded 5 seconds';
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
    if (timeoutHandle !== null) {
      clearTimeout(timeoutHandle);
      timeoutHandle = null;
    }
    if (interruptBuffer) interruptBuffer[0] = 0;
    try {
      pyodide.runPython(
        '__import__("sys").stdout = __import__("sys").__stdout__\n' +
        '__import__("sys").stderr = __import__("sys").__stderr__'
      );
    } catch { /* ignore cleanup errors */ }
  }

  self.postMessage({ type: 'result', id, output, error, timedOut });
});
