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
import { CATALOG_COURSES, CATALOG_TRACKS } from '../lib/catalog';
import { COMPARISON_CHECKED_ON, COMPARISON_ROWS } from '../lib/comparison';
import { BrandMark } from '../components/common/BrandMark';

const ENGINE_KEYS = ['bkt', 'fsrs', 'elo', 'bandit', 'dkt', 'irt'] as const;
const BKT_PARAM_KEYS = ['pl0', 'pt', 'pg', 'ps', 'masteryThreshold', 'idkPrior'] as const;
const BEHIND_KEYS = [
  'catalogBreadth', 'videoContent', 'community', 'mobileNative',
  'benchmarkSynthetic', 'assistmentsEdnet', 'perSkillCalibration',
] as const;

export function EvidenceScreen() {
  const { t } = useTranslation();

  useEffect(() => {
    document.title = t('evidence.pageTitle');
  }, [t]);

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

        {/* Section 4: comparativa. Aquí estaba una tabla con notas propias a nueve
            plataformas con nombre (auditoría de pantallas, 2026-10-15): era
            nuestro juicio, sin auditar. La única comparativa pública es la de
            la portada, con lo comprobado en la web de cada una y su fecha. */}
        {COMPARISON_ROWS.length > 0 && (
          <section className={styles.section}>
            <h2 className={styles.h2}>{t('evidence.s4Title')}</h2>
            <p className={styles.lead}>
              {t('evidence.s4Lead', { date: COMPARISON_CHECKED_ON })}{' '}
              <a href="/landing#compare" className={styles.link}>{t('evidence.s4Link')}</a>
            </p>
          </section>
        )}

        {/* Section 5: What we're not */}
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
