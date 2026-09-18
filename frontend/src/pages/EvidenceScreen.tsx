import { useEffect } from 'react';
import styles from './EvidenceScreen.module.css';

const CAPTURE_DATE = '2026-09-15';

// Catálogo real, y la única copia de estos números en esta página.
//
// Estaban escritos a mano dentro de dos cadenas y se quedaron en «8 tracks
// 3 419 Q» mientras el banco crecía a 11 tracks y 4.724 preguntas: la página
// que existe para publicar evidencia reproducible publicaba dos cifras falsas.
// `scripts/check_docs.py` (sección 4) los compara contra
// `content/curriculum/tracks.json` y `content/questions/` y FALLA si mienten,
// así que la próxima vez que el banco crezca el guardia avisa en vez de que
// nadie se entere. Si cambias uno a mano sin que el contenido lo respalde,
// CI se pone en rojo — que es la idea.
const CATALOG_TRACKS = 18;
const CATALOG_COURSES = 49;
const CATALOG_QUESTIONS = 6233;

// Competitor dimensions and weights (fixed — §7.1 of the master plan)
const WEIGHTS = {
  engine: 20,     // adaptive engine with public evidence
  bilingual: 15,  // native ES+EN (not translated)
  runtime: 15,    // in-browser multi-runtime code execution
  algorithm: 15,  // "I don't know" + FSRS + BKT + Elo + bandit
  catalog: 20,    // breadth of catalog (tracks × skills × questions)
  ui: 15,         // UI/UX quality and performance
};
const MAX = Object.values(WEIGHTS).reduce((a, b) => a + b, 0);

interface Competitor {
  name: string;
  url: string;
  engine: number;
  bilingual: number;
  runtime: number;
  algorithm: number;
  catalog: number;
  ui: number;
  notes: string;
}

const COMPETITORS: Competitor[] = [
  {
    name: 'Whetzy (actual)',
    url: 'https://whetzy.com',
    engine: 14, bilingual: 14, runtime: 13, algorithm: 13, catalog: 7, ui: 10,
    notes: `BKT+FSRS+Elo+bandit, "no lo sé", ${CATALOG_TRACKS} tracks ${CATALOG_QUESTIONS} Q, build obsoleto H.11`,
  },
  {
    name: 'Whetzy (H.11+H.10)',
    url: 'https://whetzy.com',
    engine: 16, bilingual: 14, runtime: 14, algorithm: 14, catalog: 8, ui: 12,
    notes: 'Con redespliegue y ≥30 beta users — techo alcanzable esta semana',
  },
  {
    name: 'Boot.dev',
    url: 'https://boot.dev',
    engine: 8, bilingual: 2, runtime: 12, algorithm: 5, catalog: 15, ui: 13,
    notes: 'EN solo, backend gamificado, Python/Go/JS server-side, sin motor BKT',
  },
  {
    name: 'Sololearn',
    url: 'https://sololearn.com',
    engine: 5, bilingual: 6, runtime: 10, algorithm: 3, catalog: 14, ui: 11,
    notes: 'Móvil-first, muchos idiomas pero sin adaptación real, ejecución básica',
  },
  {
    name: 'Mimo',
    url: 'https://getmimo.com',
    engine: 4, bilingual: 4, runtime: 8, algorithm: 2, catalog: 10, ui: 14,
    notes: 'UX bite-size excelente, casi sin adaptación, EN-first',
  },
  {
    name: 'Exercism',
    url: 'https://exercism.org',
    engine: 3, bilingual: 3, runtime: 13, algorithm: 2, catalog: 16, ui: 10,
    notes: 'Ejercicios reales con mentores, sin currículo adaptativo, EN-first',
  },
  {
    name: 'Platzi',
    url: 'https://platzi.com',
    engine: 4, bilingual: 14, runtime: 5, algorithm: 2, catalog: 18, ui: 12,
    notes: 'ES nativo + EN, enorme catálogo de video, sin motor BKT ni ejecución en navegador',
  },
  {
    name: 'KodeKloud',
    url: 'https://kodekloud.com',
    engine: 5, bilingual: 2, runtime: 14, algorithm: 3, catalog: 12, ui: 11,
    notes: 'Labs en navegador reales, cloud/DevOps, EN-first, sin adaptación',
  },
  {
    name: 'A Cloud Guru',
    url: 'https://acloudguru.com',
    engine: 4, bilingual: 2, runtime: 6, algorithm: 2, catalog: 13, ui: 10,
    notes: 'Video-first, certs AWS/GCP/Azure, EN-first, laboratorios básicos',
  },
  {
    name: 'LeetCode',
    url: 'https://leetcode.com',
    engine: 6, bilingual: 3, runtime: 14, algorithm: 4, catalog: 12, ui: 9,
    notes: 'Algoritmos excelente, ejecución real, sin currículo adaptativo ni bilingüe',
  },
  {
    name: 'freeCodeCamp',
    url: 'https://freecodecamp.org',
    engine: 2, bilingual: 5, runtime: 11, algorithm: 1, catalog: 14, ui: 8,
    notes: 'Gratuito, web/algoritmos, sin motor adaptativo',
  },
];

function score(c: Competitor) {
  return c.engine + c.bilingual + c.runtime + c.algorithm + c.catalog + c.ui;
}

function ScoreBar({ value, max, color }: { value: number; max: number; color: string }) {
  return (
    <div className={styles.barWrap}>
      <div className={styles.barFill} style={{ width: `${(value / max) * 100}%`, background: color }} />
      <span className={styles.barLabel}>{value}</span>
    </div>
  );
}

const BKT_PARAMS = [
  { param: 'P(L₀)', value: '0.10', desc: 'Prior probability of knowing a skill before any practice' },
  { param: 'P(T)', value: '0.20', desc: 'Probability of learning after one correct opportunity' },
  { param: 'P(G)', value: '0.25', desc: 'Probability of guessing correctly without knowing' },
  { param: 'P(S)', value: '0.10', desc: 'Probability of slipping (wrong despite knowing)' },
  { param: 'Mastery threshold', value: '0.95', desc: 'Minimum P(L) to unlock the next module' },
  { param: '"I don\'t know" prior', value: '0.05/0.80', desc: 'P(knows | says DK) / P(unknown | says DK) — stronger negative evidence than a wrong answer' },
];

const ENGINE_STACK = [
  { name: 'BKT', desc: 'HMM mastery estimation. Updates P(L) after every answer. 4-parameter model with explicit "I don\'t know" support.' },
  { name: 'FSRS', desc: 'Free Spaced Repetition Scheduler (SM-17 successor). Computes optimal review interval from stability and difficulty.' },
  { name: 'Elo', desc: 'Question difficulty calibration. Adjusts question ratings based on answer outcomes across all users.' },
  { name: 'Bandit (ε-greedy)', desc: 'Session-level question selection. Balances exploration (new skills) vs. exploitation (due reviews).' },
  { name: 'DKT (LSTM)', desc: 'Deep Knowledge Tracing. LSTM trained on answer sequences, used as a secondary signal for P(L) alongside BKT.' },
  { name: 'IRT (planned)', desc: 'Item Response Theory. 2-PL model for difficulty/discrimination. Pending ASSISTments calibration data.' },
];

function dimColor(val: number, max: number) {
  const pct = val / max;
  if (pct >= 0.75) return 'var(--ev-green)';
  if (pct >= 0.5)  return 'var(--ev-brand)';
  if (pct >= 0.25) return 'var(--ev-orange)';
  return 'var(--ev-muted)';
}

export function EvidenceScreen() {
  useEffect(() => {
    document.title = 'Whetzy — Evidence';
  }, []);

  const sorted = [...COMPETITORS].sort((a, b) => score(b) - score(a));

  return (
    <div className={styles.page}>
      <header className={styles.hero}>
        <div className={styles.heroInner}>
          <div className={styles.heroLogo}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" width="36" height="36">
              <path d="M12 12.5 12 4M12 12.5 5.5 19M12 12.5 18.5 19M12 4 5.5 19M5.5 19 18.5 19M18.5 19 12 4" opacity="0.5" />
              <circle cx="12" cy="12.5" r="2.8" fill="currentColor" stroke="none" />
              <circle cx="12" cy="4" r="2" fill="currentColor" stroke="none" />
              <circle cx="5.5" cy="19" r="2" fill="currentColor" stroke="none" />
              <circle cx="18.5" cy="19" r="2" fill="currentColor" stroke="none" />
            </svg>
            <span className={styles.heroLogoName}>Whetzy</span>
          </div>
          <h1 className={styles.heroTitle}>Evidence page</h1>
          <p className={styles.heroSub}>
            We claim to have the most transparent adaptive learning engine in
            coding education. This page is the proof — or the failure to provide it.
            Every number here is reproducible from our open source code.
          </p>
          <p className={styles.captureDate}>Captured: {CAPTURE_DATE} · <a href="https://github.com" className={styles.link}>source code</a></p>
        </div>
      </header>

      <main className={styles.main}>

        {/* Section 1: Engine stack */}
        <section className={styles.section}>
          <h2 className={styles.h2}>01 — Learning engine</h2>
          <p className={styles.lead}>
            Whetzy runs a six-component adaptive stack. Every component is unit-tested.
            None of it is vendor-locked — the full implementation lives in
            <code className={styles.inlineCode}> backend/app/services/engine/</code>.
          </p>
          <div className={styles.engineGrid}>
            {ENGINE_STACK.map((e) => (
              <div key={e.name} className={styles.engineCard}>
                <span className={styles.engineName}>{e.name}</span>
                <p className={styles.engineDesc}>{e.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Section 2: BKT parameters */}
        <section className={styles.section}>
          <h2 className={styles.h2}>02 — BKT parameters &amp; calibration</h2>
          <p className={styles.lead}>
            Default parameters from Wilson et al. (2016) and Corbett &amp; Anderson (1995).
            Per-skill overrides are planned for F23 once ≥30 beta users provide enough
            observations per skill to fit P(L₀) and P(T) via EM.
          </p>
          <table className={styles.table}>
            <thead>
              <tr><th>Parameter</th><th>Value</th><th>Meaning</th></tr>
            </thead>
            <tbody>
              {BKT_PARAMS.map((r) => (
                <tr key={r.param}>
                  <td><code className={styles.inlineCode}>{r.param}</code></td>
                  <td className={styles.tdValue}>{r.value}</td>
                  <td>{r.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className={styles.benchmarkNote}>
            <strong>ASSISTments 2009 (not included):</strong> the canonical distribution
            page returns HTTP 200 but exposes no scriptable download URL, and every
            commonly-cited GitHub mirror we checked 404'd. Recorded as a gap in
            <code className={styles.inlineCode}> docs/ml/kt-benchmark.json</code> rather
            than silently skipped or substituted with a look-alike dataset.
          </div>
        </section>

        {/* Section 3: Measured benchmark */}
        <section className={styles.section}>
          <h2 className={styles.h2}>03 — Measured benchmark: BKT vs DKT</h2>
          <p className={styles.lead}>
            Run on <strong>synthetic-5</strong> (Piech et al. 2015, <em>Deep Knowledge
            Tracing</em>) — a fixed, third-party, citable dataset, so the "adaptive engine"
            claim is not graded by our own homework. 4 000 students, 5 concepts,
            50 responses each. Temporal split by student (3 200 train / 800 test, no
            shuffling); within every sequence, predicting response <em>t</em> uses only
            responses 1…<em>t</em>−1 of that same student.
          </p>

          <div className={styles.resultGrid}>
            <div className={styles.resultCard}>
              <span className={styles.resultLabel}>BKT — test AUC</span>
              <span className={styles.resultValue}>0.7983</span>
              <span className={styles.resultSub}>acc 0.7281 · grid-fit on train only</span>
            </div>
            <div className={`${styles.resultCard} ${styles.resultCardWin}`}>
              <span className={styles.resultLabel}>DKT — test AUC</span>
              <span className={styles.resultValue}>0.8294</span>
              <span className={styles.resultSub}>acc 0.7563 · LSTM h=64, seed 42</span>
            </div>
            <div className={styles.resultCard}>
              <span className={styles.resultLabel}>DKT − BKT margin</span>
              <span className={styles.resultValue}>+0.031</span>
              <span className={styles.resultSub}>39 200 held-out predictions</span>
            </div>
          </div>

          <div className={styles.benchmarkNote}>
            <strong>Read this before quoting the numbers.</strong> Responses are keyed by
            <em> concept id</em> (0–4), not question id — the representation our production
            engine actually uses, but <em>not</em> the paper's setup. Handing the model
            ground-truth concept labels removes within-concept difficulty and makes the task
            strictly easier for <em>both</em> models, which is why both score above the
            paper's 0.75 / 0.62. These numbers must never be reported as beating Piech et al.
            The margin is what transfers, and ours (+0.031) is far smaller than the paper's
            (+0.13): a well-fit BKT is a strong baseline over only 5 concepts. The one
            defensible claim here is narrow — <em>on concept-level synthetic-5, our DKT beats
            our grid-fit BKT by about 0.03 AUC.</em> Nothing stronger.
          </div>

          <p className={styles.disclaimer}>
            BKT baseline uses <code className={styles.inlineCode}>app/services/engine/bkt.py</code> unchanged;
            parameters were grid-searched on the train split only (coarse grid, not full
            Baum-Welch — the production model has no EM). Full methodology, the exact fitted
            parameters, and the ASSISTments failure log live in
            <code className={styles.inlineCode}> docs/ml/kt-benchmark.json</code>.
            Reproduce with <code className={styles.inlineCode}>python -m app.ml.benchmark_kt</code>.
            Generated 2026-09-13.
          </p>
        </section>

        {/* Section 4: Competitor teardown */}
        <section className={styles.section}>
          <h2 className={styles.h2}>04 — Competitor teardown</h2>
          <p className={styles.lead}>
            Scored across six weighted dimensions (total {MAX} pts). Scores are our own
            judgement based on public feature lists and hands-on testing — not independently
            audited. URLs and dates are recorded so you can verify them yourself.
          </p>

          <div className={styles.dimLegend}>
            {Object.entries(WEIGHTS).map(([k, w]) => (
              <span key={k} className={styles.dimChip}>
                <strong>{k}</strong> /{w}
              </span>
            ))}
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Platform</th>
                  {Object.keys(WEIGHTS).map((k) => <th key={k}>{k}</th>)}
                  <th>Total /{MAX}</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((c) => {
                  const total = score(c);
                  const isWhetzy = c.name.startsWith('Whetzy');
                  return (
                    <tr key={c.name} className={isWhetzy ? styles.rowHighlight : ''}>
                      <td>
                        <a href={c.url} target="_blank" rel="noopener noreferrer" className={styles.link}>
                          {c.name}
                        </a>
                        <p className={styles.noteCell}>{c.notes}</p>
                      </td>
                      {(['engine','bilingual','runtime','algorithm','catalog','ui'] as const).map((dim) => (
                        <td key={dim} className={styles.tdScore}>
                          <ScoreBar value={c[dim]} max={WEIGHTS[dim]} color={dimColor(c[dim], WEIGHTS[dim])} />
                        </td>
                      ))}
                      <td className={styles.tdTotal}>
                        <strong style={{ color: dimColor(total, MAX) }}>{total}</strong>
                        <span className={styles.pct}>/{MAX}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className={styles.disclaimer}>
            Scores as of {CAPTURE_DATE}. Platforms improve; so do we.
            If you see an error, open an issue or email federicogalindez6@gmail.com.
          </p>
        </section>

        {/* Section 4: What we're not */}
        <section className={styles.section}>
          <h2 className={styles.h2}>05 — Where we're behind</h2>
          <ul className={styles.behindList}>
            <li><strong>Catalog breadth:</strong> {CATALOG_TRACKS} tracks / {CATALOG_COURSES} courses vs. Platzi&apos;s 500+ courses. Breadth is our weakest dimension and we are not claiming a delivery rate we cannot show.</li>
            <li><strong>Video content:</strong> We have none. We use code examples and worked examples instead.</li>
            <li><strong>Community:</strong> Zero users today (H.10). Forums, peer review, and leaderboards need people.</li>
            <li><strong>Mobile native:</strong> PWA only. No App Store / Play Store listing yet (H.2/H.3).</li>
            <li><strong>Benchmark is synthetic, not real learners:</strong> synthetic-5 is generated data. We have no AUC on a real classroom dataset, and none on our own users.</li>
            <li><strong>ASSISTments / EdNet:</strong> not integrated — ASSISTments 2009 has no scriptable download; the failure log is in the benchmark JSON.</li>
            <li><strong>Per-skill calibration:</strong> production BKT ships literature defaults with no EM fitting. The grid search exists only inside the benchmark script.</li>
          </ul>
        </section>

      </main>

      <footer className={styles.footer}>
        <p>Whetzy · <a href="/" className={styles.link}>Back to app</a> · MIT engine · PSF content</p>
      </footer>
    </div>
  );
}

