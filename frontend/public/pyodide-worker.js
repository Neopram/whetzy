// Pyodide WebWorker — loads Python runtime once, executes code on demand.
// Messages IN:  { type: 'run', id: string, code: string }
// Messages OUT: { type: 'ready' }
//               { type: 'result', id, output, error, timedOut }
//               { type: 'loadError', message }

importScripts('https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.js');

let pyodide = null;

(async () => {
  try {
    pyodide = await loadPyodide({
      indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.2/full/',
    });
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

  try {
    // Redirect stdout + stderr into a single buffer.
    pyodide.runPython(
      '_nbuf = __import__("io").StringIO()\n' +
      '__import__("sys").stdout = _nbuf\n' +
      '__import__("sys").stderr = _nbuf'
    );
    pyodide.runPython(code);
    output = pyodide.runPython('_nbuf.getvalue()');
  } catch (err) {
    try { output = pyodide.runPython('_nbuf.getvalue()'); } catch (_) { /* nothing captured yet */ }
    // Surface only the last meaningful line (strip Pyodide's internal traceback prefix).
    const lines = String(err).split('\n').filter(Boolean);
    error = lines[lines.length - 1] || String(err);
  } finally {
    try {
      pyodide.runPython(
        '__import__("sys").stdout = __import__("sys").__stdout__\n' +
        '__import__("sys").stderr = __import__("sys").__stderr__'
      );
    } catch (_) { /* ignore cleanup errors */ }
  }

  self.postMessage({ type: 'result', id, output, error, timedOut: false });
});
