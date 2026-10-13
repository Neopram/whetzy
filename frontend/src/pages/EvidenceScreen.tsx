import { useEffect } from 'react';
import { Trans, useTranslation } from 'react-i18next';
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
import { CATALOG_COURSES, CATALOG_QUESTIONS, CATALOG_TRACKS } from '../lib/catalog';
import { BrandMark } from '../components/common/BrandMark';

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

type CompetitorKey =
  | 'whetzyNow' | 'whetzyH11' | 'bootdev' | 'sololearn' | 'mimo' | 'exercism'
  | 'platzi' | 'kodekloud' | 'acloudguru' | 'leetcode' | 'freecodecamp';

interface CompetitorScore {
  key: CompetitorKey;
  url: string;
  engine: number;
  bilingual: number;
  runtime: number;
  algorithm: number;
  catalog: number;
  ui: number;
}

const COMPETITOR_SCORES: CompetitorScore[] = [
  { key: 'whetzyNow', url: 'https://whetzy.com', engine: 14, bilingual: 14, runtime: 13, algorithm: 13, catalog: 7, ui: 10 },
  { key: 'whetzyH11', url: 'https://whetzy.com', engine: 16, bilingual: 14, runtime: 14, algorithm: 14, catalog: 8, ui: 12 },
  { key: 'bootdev', url: 'https://boot.dev', engine: 8, bilingual: 2, runtime: 12, algorithm: 5, catalog: 15, ui: 13 },
  { key: 'sololearn', url: 'https://sololearn.com', engine: 5, bilingual: 6, runtime: 10, algorithm: 3, catalog: 14, ui: 11 },
  { key: 'mimo', url: 'https://getmimo.com', engine: 4, bilingual: 4, runtime: 8, algorithm: 2, catalog: 10, ui: 14 },
  { key: 'exercism', url: 'https://exercism.org', engine: 3, bilingual: 3, runtime: 13, algorithm: 2, catalog: 16, ui: 10 },
  { key: 'platzi', url: 'https://platzi.com', engine: 4, bilingual: 14, runtime: 5, algorithm: 2, catalog: 18, ui: 12 },
  { key: 'kodekloud', url: 'https://kodekloud.com', engine: 5, bilingual: 2, runtime: 14, algorithm: 3, catalog: 12, ui: 11 },
  { key: 'acloudguru', url: 'https://acloudguru.com', engine: 4, bilingual: 2, runtime: 6, algorithm: 2, catalog: 13, ui: 10 },
  { key: 'leetcode', url: 'https://leetcode.com', engine: 6, bilingual: 3, runtime: 14, algorithm: 4, catalog: 12, ui: 9 },
  { key: 'freecodecamp', url: 'https://freecodecamp.org', engine: 2, bilingual: 5, runtime: 11, algorithm: 1, catalog: 14, ui: 8 },
];

function score(c: CompetitorScore) {
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

const ENGINE_KEYS = ['bkt', 'fsrs', 'elo', 'bandit', 'dkt', 'irt'] as const;
const BKT_PARAM_KEYS = ['pl0', 'pt', 'pg', 'ps', 'masteryThreshold', 'idkPrior'] as const;
const BEHIND_KEYS = [
  'catalogBreadth', 'videoContent', 'community', 'mobileNative',
  'benchmarkSynthetic', 'assistmentsEdnet', 'perSkillCalibration',
] as const;
const DIM_KEYS = ['engine', 'bilingual', 'runtime', 'algorithm', 'catalog', 'ui'] as const;

function dimColor(val: number, max: number) {
  const pct = val / max;
  if (pct >= 0.75) return 'var(--le-green)';
  if (pct >= 0.5)  return 'var(--le-purple-dark)';
  if (pct >= 0.25) return 'var(--le-orange)';
  return 'var(--le-text-muted)';
}

export function EvidenceScreen() {
  const { t } = useTranslation();

  useEffect(() => {
    document.title = t('evidence.pageTitle');
  }, [t]);

  const sorted = [...COMPETITOR_SCORES].sort((a, b) => score(b) - score(a));

  return (
    <div className={styles.page}>
      <header className={styles.hero}>
        <div className={styles.heroInner}>
          <div className={styles.heroLogo}>
            <BrandMark height={32} />
            <span className={styles.heroLogoName}>Whetzy</span>
          </div>
          <h1 className={styles.heroTitle}>{t('evidence.heroTitle')}</h1>
          <p className={styles.heroSub}>{t('evidence.heroSub')}</p>
          <p className={styles.captureDate}>
            {t('evidence.capturedLabel')}: {CAPTURE_DATE}
          </p>
        </div>
      </header>

      <main className={styles.main}>

        {/* Section 1: Engine stack */}
        <section className={styles.section}>
          <h2 className={styles.h2}>{t('evidence.s1Title')}</h2>
          <p className={styles.lead}>
            {t('evidence.s1Lead')}{' '}
            <code className={styles.inlineCode}> backend/app/services/engine/</code>.
          </p>
          <div className={styles.engineGrid}>
            {ENGINE_KEYS.map((k) => (
              <div key={k} className={styles.engineCard}>
                <span className={styles.engineName}>{t(`evidence.engineStack.${k}.name`)}</span>
                <p className={styles.engineDesc}>{t(`evidence.engineStack.${k}.desc`)}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Section 2: BKT parameters */}
        <section className={styles.section}>
          <h2 className={styles.h2}>{t('evidence.s2Title')}</h2>
          <p className={styles.lead}>{t('evidence.s2Lead')}</p>
          <table className={styles.table}>
            <thead>
              <tr><th>{t('evidence.tableParameter')}</th><th>{t('evidence.tableValue')}</th><th>{t('evidence.tableMeaning')}</th></tr>
            </thead>
            <tbody>
              {BKT_PARAM_KEYS.map((k) => (
                <tr key={k}>
                  <td><code className={styles.inlineCode}>{t(`evidence.bktParams.${k}.param`)}</code></td>
                  <td className={styles.tdValue}>{BKT_PARAM_VALUES[k]}</td>
                  <td>{t(`evidence.bktParams.${k}.desc`)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className={styles.benchmarkNote}>
            <strong>{t('evidence.assistmentsNoteStrong')}</strong> {t('evidence.assistmentsNoteText')}
            <code className={styles.inlineCode}> docs/ml/kt-benchmark.json</code> {t('evidence.assistmentsNoteEnd')}
          </div>
        </section>

        {/* Section 3: Measured benchmark */}
        <section className={styles.section}>
          <h2 className={styles.h2}>{t('evidence.s3Title')}</h2>
          <p className={styles.lead}>
            <Trans i18nKey="evidence.s3Lead" components={{ 1: <strong />, 2: <em />, 3: <em /> }} />
          </p>

          <div className={styles.resultGrid}>
            <div className={styles.resultCard}>
              <span className={styles.resultLabel}>{t('evidence.bktAucLabel')}</span>
              <span className={styles.resultValue}>0.7983</span>
              <span className={styles.resultSub}>{t('evidence.bktAucSub')}</span>
            </div>
            <div className={`${styles.resultCard} ${styles.resultCardWin}`}>
              <span className={styles.resultLabel}>{t('evidence.dktAucLabel')}</span>
              <span className={styles.resultValue}>0.8294</span>
              <span className={styles.resultSub}>{t('evidence.dktAucSub')}</span>
            </div>
            <div className={styles.resultCard}>
              <span className={styles.resultLabel}>{t('evidence.marginLabel')}</span>
              <span className={styles.resultValue}>+0.031</span>
              <span className={styles.resultSub}>{t('evidence.marginSub')}</span>
            </div>
          </div>

          <div className={styles.benchmarkNote}>
            <strong>{t('evidence.readNoteStrong')}</strong>{' '}
            <Trans i18nKey="evidence.readNoteText" components={{ 1: <em /> }} />
          </div>

          <p className={styles.disclaimer}>
            <Trans i18nKey="evidence.s3Disclaimer" components={{ 1: <code className={styles.inlineCode} /> }} />
          </p>
        </section>

        {/* Section 4: Competitor teardown */}
        <section className={styles.section}>
          <h2 className={styles.h2}>{t('evidence.s4Title')}</h2>
          <p className={styles.lead}>{t('evidence.s4Lead', { max: MAX })}</p>

          <div className={styles.dimLegend}>
            {DIM_KEYS.map((k) => (
              <span key={k} className={styles.dimChip}>
                <strong>{t(`evidence.dims.${k}`)}</strong> /{WEIGHTS[k]}
              </span>
            ))}
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>{t('evidence.tablePlatform')}</th>
                  {DIM_KEYS.map((k) => <th key={k}>{t(`evidence.dims.${k}`)}</th>)}
                  <th>{t('evidence.tableTotal')} /{MAX}</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((c) => {
                  const total = score(c);
                  const isWhetzy = c.key === 'whetzyNow' || c.key === 'whetzyH11';
                  return (
                    <tr key={c.key} className={isWhetzy ? styles.rowHighlight : ''}>
                      <td>
                        <a href={c.url} target="_blank" rel="noopener noreferrer" className={styles.link}>
                          {t(`evidence.competitors.${c.key}.name`)}
                        </a>
                        <p className={styles.noteCell}>
                          {t(`evidence.competitors.${c.key}.notes`, { tracks: CATALOG_TRACKS, questions: CATALOG_QUESTIONS })}
                        </p>
                      </td>
                      {DIM_KEYS.map((dim) => (
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
            {t('evidence.s4Disclaimer', { date: CAPTURE_DATE, email: 'federicogalindez6@gmail.com' })}
          </p>
        </section>

        {/* Section 4: What we're not */}
        <section className={styles.section}>
          <h2 className={styles.h2}>{t('evidence.s5Title')}</h2>
          <ul className={styles.behindList}>
            {BEHIND_KEYS.map((k) => (
              <li key={k}>
                <strong>{t(`evidence.behind.${k}.label`)}</strong>{' '}
                {t(`evidence.behind.${k}.text`, { tracks: CATALOG_TRACKS, courses: CATALOG_COURSES })}
              </li>
            ))}
          </ul>
        </section>

      </main>

      <footer className={styles.footer}>
        <p>{t('evidence.footer')} · <a href="/" className={styles.link}>{t('evidence.backToApp')}</a> · {t('evidence.engineLicense')} · {t('evidence.contentPsf')}</p>
      </footer>
    </div>
  );
}

const BKT_PARAM_VALUES: Record<(typeof BKT_PARAM_KEYS)[number], string> = {
  pl0: '0.10',
  pt: '0.20',
  pg: '0.25',
  ps: '0.10',
  masteryThreshold: '0.95',
  idkPrior: '0.05/0.80',
};
