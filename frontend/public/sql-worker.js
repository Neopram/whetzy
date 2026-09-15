// SQL WebWorker — sandboxed sql.js (SQLite-in-WASM) runtime.
// Messages IN:  { type: 'run', id: string, code: string }  (code = SQL statement(s))
// Messages OUT: { type: 'ready' }
//               { type: 'result', id, output, error, timedOut }
//               { type: 'loadError', message }
//
// Each 'run' creates a fresh in-memory database so questions are isolated.
// sql.js files are self-hosted under /sql-js/ (copied from the sql.js npm
// package at build time — red line 5: no third-party CDN in prod).

importScripts('/sql-js/sql-wasm-browser.js');

let SQL = null;

initSqlJs({ locateFile: () => '/sql-js/sql-wasm-browser.wasm' })
  .then((sql) => {
    SQL = sql;
    self.postMessage({ type: 'ready' });
  })
  .catch((err) => {
    self.postMessage({ type: 'loadError', message: String(err) });
  });

self.onmessage = function (e) {
  const { type, id, code } = e.data;
  if (type !== 'run' || !SQL) return;

  let output = '';
  let error = null;

  try {
    const db = new SQL.Database();
    try {
      const results = db.exec(code);
      if (results.length === 0) {
        output = '(no rows)';
      } else {
        // Format each result set as a text table.
        output = results
          .map((res) => {
            const cols = res.columns;
            const rows = res.values;
            const lines = [cols.join(' | ')];
            lines.push(cols.map((c) => '-'.repeat(c.length)).join('-+-'));
            for (const row of rows) {
              lines.push(row.map(String).join(' | '));
            }
            return lines.join('\n');
          })
          .join('\n\n');
      }
    } finally {
      db.close();
    }
  } catch (err) {
    error = String(err);
  }

  self.postMessage({ type: 'result', id, output, error, timedOut: false });
};
