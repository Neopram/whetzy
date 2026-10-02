#!/usr/bin/env node
/**
 * Every executable Python exercise must be solvable in the learner's browser.
 *
 * `backend/tests/content/test_exec_questions.py` runs each reference solution
 * in CPython. That proves the answer key is right, not that the learner can
 * reach it: the quiz runs code in Pyodide, inside `public/pyodide-worker.js`,
 * with a sandbox that blocks `os`, `threading`, `socket`, `tempfile`,
 * `multiprocessing`, `pathlib`… and without the packages Pyodide unvendors
 * (`sqlite3`, OpenSSL for `hashlib.pbkdf2_hmac`). On 2026-10-02, 24 exercises
 * passed in CPython and could never be answered in the browser: threads,
 * `asyncio.run` (Pyodide's loop is already running), `sqlite3`, temp files.
 * Graded on the server since #70, they counted as wrong for everyone.
 *
 * This runs the same reference programs in the Pyodide the build ships
 * (node_modules/pyodide), behind the sandbox preamble read from the worker
 * itself, and compares stdout+stderr (the worker captures both) with
 * `correct_answer_es` / `correct_answer_en`, trimmed like the quiz does.
 * Measured against Chromium running the real worker on the same 1038
 * programs: the same 48 failures, no more and no fewer.
 *
 *   node scripts/check-exec-pyodide.mjs        (from frontend/)
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';

const FRONTEND = resolve(process.cwd());
const ROOT = resolve(FRONTEND, '..');
const QUESTIONS_DIR = join(ROOT, 'content', 'questions');
const SOLUTIONS = join(ROOT, 'backend', 'tests', 'content', 'exec_reference_solutions.json');
const WORKER = join(FRONTEND, 'public', 'pyodide-worker.js');
const PYTHON_TYPES = new Set(['fill_blank_exec', 'fix_bug']);

/** The preamble the worker prepends to every snippet, taken from the worker file. */
function sandboxPreamble() {
  const worker = readFileSync(WORKER, 'utf8');
  const blocked = worker.match(/const BLOCKED_MODULES = (\[[\s\S]*?\]);/);
  const preamble = worker.match(/const SANDBOX_PREAMBLE = `([\s\S]*?)`;/);
  if (!blocked || !preamble) {
    console.error('[exec-pyodide] FAIL — could not find BLOCKED_MODULES / SANDBOX_PREAMBLE in public/pyodide-worker.js');
    process.exit(1);
  }
  const modules = JSON.parse(blocked[1].replace(/'/g, '"').replace(/,\s*\]/, ']'));
  return preamble[1].replace('${JSON.stringify(BLOCKED_MODULES)}', JSON.stringify(modules));
}

function* questionFiles(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) yield* questionFiles(path);
    else if (name.endsWith('.json')) yield path;
  }
}

/** Mirrors `_build_code_to_run` in test_exec_questions.py (and QuizScreen's codeToRun). */
function codeToRun(question, reference, lang) {
  if (question.type === 'fix_bug') {
    return lang === 'es' ? reference.fixed : (reference.fixed_en ?? reference.fixed);
  }
  const text = question[`question_${lang}`] ?? '';
  const fence = text.match(/```[a-zA-Z]*\n?([\s\S]*?)```/);
  if (!fence) return null;
  const fill = lang === 'es' ? reference.fill : (reference.fill_en ?? reference.fill);
  return fence[1].replace(/\n$/, '').replace('___', fill);
}

const solutions = JSON.parse(readFileSync(SOLUTIONS, 'utf8'));
const programs = [];
for (const file of questionFiles(QUESTIONS_DIR)) {
  const data = JSON.parse(readFileSync(file, 'utf8'));
  for (const q of Array.isArray(data) ? data : data.questions ?? []) {
    if (!PYTHON_TYPES.has(q.type)) continue;
    const reference = solutions[q.id];
    if (!reference) continue; // missing references are test_exec_questions.py's job
    for (const lang of ['es', 'en']) {
      programs.push({
        key: `${q.id} [${lang}]`,
        code: codeToRun(q, reference, lang),
        expected: (q[`correct_answer_${lang}`] ?? '').trim(),
      });
    }
  }
}

const require = createRequire(join(FRONTEND, 'package.json'));
const pyodideDir = dirname(require.resolve('pyodide/package.json'));
const { loadPyodide } = require(join(pyodideDir, 'pyodide.js'));
const pyodide = await loadPyodide({ indexURL: `${pyodideDir}/` });
const preamble = sandboxPreamble();

const failures = [];
for (const p of programs) {
  if (p.code == null) {
    failures.push(`${p.key}: no fenced code block to run`);
    continue;
  }
  // A fresh namespace per program, as the worker's would be on first run, with
  // `__name__` set like its module globals: an empty dict falls back to the
  // builtins module's name and `__name__ == "__main__"` prints False.
  const globals = pyodide.globals.get('dict')();
  globals.set('__name__', '__main__');
  let output = '';
  let error = null;
  try {
    pyodide.runPython(
      '_nbuf = __import__("io").StringIO()\n__import__("sys").stdout = _nbuf\n__import__("sys").stderr = _nbuf',
      { globals },
    );
    pyodide.runPython(`${preamble}\n${p.code}`, { globals });
  } catch (err) {
    const lines = String(err?.message ?? err).split('\n').filter((l) => /Error|Exception/.test(l));
    error = lines[lines.length - 1] ?? String(err);
  } finally {
    try { output = pyodide.runPython('_nbuf.getvalue()', { globals }); } catch { /* nothing captured */ }
    pyodide.runPython('__import__("sys").stdout = __import__("sys").__stdout__\n__import__("sys").stderr = __import__("sys").__stderr__');
    globals.destroy();
  }
  // As in the worker: Pyodide's JS error is often just "PythonError" and the
  // traceback went to the captured stderr, whose last error line says why.
  if (error && !/:/.test(error)) {
    const lines = output.trim().split('\n').filter((l) => /Error|Exception/.test(l));
    error = lines[lines.length - 1] ?? error;
  }
  if (error) failures.push(`${p.key}: ${error}`);
  else if (output.trim() !== p.expected) failures.push(`${p.key}: printed ${JSON.stringify(output.trim())}, answer is ${JSON.stringify(p.expected)}`);
}

if (failures.length) {
  console.error(`\n[exec-pyodide] FAIL — ${failures.length} of ${programs.length} exercise/language pairs cannot be solved in the browser:`);
  for (const f of failures) console.error(`  ${f}`);
  console.error('\n  Rewrite them to run in the sandbox, or make them non-executable (mcq, fill_blank, sql_exec).\n');
  process.exit(1);
}
console.log(`[exec-pyodide] PASS — ${programs.length} exercise/language pairs solvable in Pyodide ${pyodide.version} behind the worker's sandbox`);
