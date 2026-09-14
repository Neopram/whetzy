#!/usr/bin/env node
/**
 * Third-party-origin check for the built frontend (task 12.7).
 *
 * Red line 5 is "real GDPR: no third-party trackers without explicit
 * consent". Task 11.7 claimed to have verified it with a grep and wrote
 * "0 trackers, 0 external fonts, 0 new libraries" into the ledger — but that
 * grep only looked at the TSX sources, so it never saw the
 * `@import url(https://fonts.googleapis.com/...)` sitting at the top of
 * src/styles/global.css since the beginning. Every visitor's IP went to Google
 * before any consent, for months, while the ledger said the opposite.
 *
 * A one-off grep by whoever happens to remember cannot hold that line. This
 * runs over the *built* output — the actual bytes a browser receives, whichever
 * source file or transitive dependency put them there — so the next `@import`
 * cannot slip in through a file nobody thought to grep.
 *
 * It is deliberately a denylist of known third-party hosts rather than an
 * allowlist of everything URL-shaped: dist/ is full of legitimate absolute URLs
 * (schema.org metadata, the site's own canonical links, license headers) and an
 * allowlist would be widened into uselessness by the first false positive. Add
 * a host here when a new one becomes a risk.
 *
 * Run after a build:  node scripts/check-no-third-party.mjs
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, resolve, sep } from 'node:path';

const DIST = resolve(process.cwd(), 'dist');

/** Hosts that must never appear in shipped bytes, with why they are banned. */
const BANNED = [
  ['fonts.googleapis.com', 'Google Fonts CSS — leaks the visitor IP to Google (task 12.7)'],
  ['fonts.gstatic.com', 'Google Fonts files — leaks the visitor IP to Google (task 12.7)'],
  ['google-analytics.com', 'analytics tracker'],
  ['googletagmanager.com', 'tag manager / tracker'],
  ['connect.facebook.net', 'Meta pixel'],
  ['cdn.jsdelivr.net', 'third-party CDN — bundle it, so its outage or compromise is not ours'],
  ['unpkg.com', 'third-party CDN — bundle it'],
  ['cdnjs.cloudflare.com', 'third-party CDN — bundle it'],
];

/**
 * Violations that exist today and are tracked, rather than silently tolerated.
 *
 * An exception is scoped to ONE file and ONE host on purpose: the reference
 * stays visible on every run, and the check still fails the moment that host
 * appears anywhere else. Removing an entry must mean the violation is gone —
 * never that it became inconvenient. Each entry names the task that ends it.
 */
const KNOWN_EXCEPTIONS = [
  {
    file: 'pyodide-worker.js',
    host: 'cdn.jsdelivr.net',
    task: '12.9',
    note:
      'The Pyodide runtime (~10 MB of wasm + stdlib) is fetched from jsDelivr the first time ' +
      'a learner opens an exec question. Found by this check on the very run that added it, ' +
      'not by anyone who already knew. Self-hosting it has real size and licensing questions, ' +
      'so it is tracked as 12.9 instead of being quietly dropped from BANNED.',
  },
];

const isKnownException = (file, host) =>
  KNOWN_EXCEPTIONS.some((e) => e.file === file && e.host === host);

/** Text-ish files are the only ones that can carry a URL worth checking. */
const TEXT_EXT = /\.(html|css|js|mjs|cjs|json|map|webmanifest|txt|xml|svg)$/i;

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) yield* walk(full);
    else yield full;
  }
}

let files;
try {
  files = [...walk(DIST)].filter((f) => TEXT_EXT.test(f));
} catch {
  console.error('[third-party] dist/ not found — run "npx vite build" first');
  process.exit(1);
}

const hits = [];
const excused = [];
for (const file of files) {
  const text = readFileSync(file, 'utf-8');
  const rel = relative(DIST, file).split(sep).join('/'); // POSIX-style, so exceptions read the same on Windows and in CI
  for (const [host, why] of BANNED) {
    if (!text.includes(host)) continue;
    if (isKnownException(rel, host)) excused.push({ file: rel, host });
    else hits.push({ file: rel, host, why });
  }
}

console.log(`\n[third-party] scanned ${files.length} built files for ${BANNED.length} banned hosts\n`);

for (const { file, host } of excused) {
  const { task } = KNOWN_EXCEPTIONS.find((e) => e.file === file && e.host === host);
  console.log(`  KNOWN  ${file}  ->  ${host}  (open, tracked as ${task})`);
}

if (hits.length > 0) {
  for (const { file, host, why } of hits) {
    console.error(`  FAIL   ${file}  ->  ${host}\n         ${why}`);
  }
  console.error(
    `\n[third-party] FAIL — ${hits.length} third-party reference(s) in the build.\n` +
      'Red line 5: no third parties without explicit consent. Self-host the asset, or — if\n' +
      'the reference is genuinely consented-to — add a scoped entry to KNOWN_EXCEPTIONS\n' +
      'naming the task that will remove it.\n',
  );
  process.exit(1);
}

console.log(
  excused.length === 0
    ? '[third-party] PASS — no banned third-party host in the built output\n'
    : `[third-party] PASS — no new third-party host; ${excused.length} known exception(s) still open\n`,
);
