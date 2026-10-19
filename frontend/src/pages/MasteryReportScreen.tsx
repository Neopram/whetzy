/**
 * Informe de dominio público (ECONOMIA §2.3), en `/report/<código>`.
 *
 * Como el certificado, lo abre alguien sin cuenta (un empleador): sin muro de
 * registro. Es una instantánea con fecha; «Guardar como PDF» usa la impresión
 * del navegador, con una hoja de estilos de impresión propia.
 */
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { masteryReports, type MasteryReport } from '../services/api';
import styles from './MasteryReportScreen.module.css';
import { TrackIcon } from '../components/common/AppIcon';

type State = { status: 'loading' } | { status: 'found'; report: MasteryReport } | { status: 'missing' };

const pct = (x: number) => Math.round(x * 100);

export function MasteryReportScreen({ code }: { code: string }) {
  const { t, i18n } = useTranslation();
  const [state, setState] = useState<State>({ status: 'loading' });
  const es = i18n.language.startsWith('es');

  useEffect(() => {
    let cancelled = false;
    masteryReports
      .get(code)
      .then((report) => { if (!cancelled) setState({ status: 'found', report }); })
      // Cualquier fallo se lee como «no existe», igual que el certificado:
      // distinguir 404 de 500 le diría a quien prueba códigos cuáles existen.
      .catch(() => { if (!cancelled) setState({ status: 'missing' }); });
    return () => { cancelled = true; };
  }, [code]);

  if (state.status === 'loading') {
    return <div className={styles.screen}><p className={styles.muted}>{t('loading')}</p></div>;
  }
  if (state.status === 'missing') {
    return (
      <div className={styles.screen}>
        <h1 className={styles.title}>{t('report.title')}</h1>
        <p className={styles.muted} role="alert">{t('report.notFound')}</p>
      </div>
    );
  }

  const s = state.report.snapshot;
  const date = new Date(s.generated_at).toLocaleDateString(es ? 'es-ES' : 'en-GB', {
    day: 'numeric', month: 'long', year: 'numeric',
  });

  return (
    <div className={styles.screen}>
      <header className={styles.header}>
        <p className={styles.brand}>Whetzy</p>
        <h1 className={styles.title}>{t('report.title')}</h1>
        <p className={styles.who}>{s.display_name} · @{s.username}</p>
        <p className={styles.muted}>{t('report.generatedOn', { date })}</p>
      </header>

      <dl className={styles.stats}>
        <div><dt>{t('report.questions')}</dt><dd>{s.total_questions_answered}</dd></div>
        <div><dt>{t('report.accuracy')}</dt><dd>{pct(s.overall_accuracy)} %</dd></div>
        <div><dt>{t('report.maxStreak')}</dt><dd>{s.max_streak}</dd></div>
      </dl>

      {s.tracks.length === 0 ? (
        <p className={styles.muted}>{t('report.noTracks')}</p>
      ) : (
        <ul className={styles.tracks}>
          {s.tracks.map((tr) => (
            <li key={tr.track_id} className={styles.track}>
              <h2 className={styles.trackName}>
                <span aria-hidden="true"><TrackIcon trackId={tr.track_id} fallback={tr.icon} size={24} /> </span>
                {es ? tr.name_es : tr.name_en}
              </h2>
              <p className={styles.trackMeta}>
                {t('report.trackMeta', { mastered: tr.skills_mastered, total: tr.total_skills })}
              </p>
              {tr.mastered_skills.length > 0 && (
                <ul className={styles.skills} aria-label={t('report.masteredSkills')}>
                  {tr.mastered_skills.map((sk) => (
                    <li key={sk.name_en}>{es ? sk.name_es : sk.name_en}</li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      )}

      <p className={styles.note}>{t('report.method')}</p>
      <button type="button" className={styles.print} onClick={() => window.print()}>{t('report.print')}</button>
    </div>
  );
}
