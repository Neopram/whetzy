import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { useApi } from '../hooks/useApi';
import { bandForDomain, examBand, MIN_EVIDENCE_ANSWERS } from '../lib/evidenceBand';
import { content as contentApi, exams, type CertificationReadiness, type DomainReadiness, type TrackRead } from '../services/api';
import { RetiredCertNotice } from '../components/common/RetiredCertNotice';
import styles from './ReadinessScreen.module.css';

interface Props {
  trackId: string;
  onExit: () => void;
}

// El mismo umbral que usa el backend para marcar un dominio «listo»
// (exams.py, READY_THRESHOLD). Solo ordena la palanca: no se enseña (ADR-60).
const READY_THRESHOLD = 0.75;

/** El dominio que más acerca al aprobado: peso × lo que le falta hasta el
 *  umbral. Un dominio pesado a medias gana a uno ligero a cero. */
function biggestLever(domains: DomainReadiness[]): DomainReadiness | undefined {
  return [...domains]
    .filter((d) => !d.ready)
    .sort((a, b) => b.weight_pct * (READY_THRESHOLD - (b.p_known_mean ?? 0)) - a.weight_pct * (READY_THRESHOLD - (a.p_known_mean ?? 0)))[0];
}

export function ReadinessScreen({ trackId, onExit }: Props) {
  const { t } = useTranslation();
  const lang = useAppStore((s) => s.user.language);
  const startMockExam = useAppStore((s) => s.startMockExam);
  const startQuiz = useAppStore((s) => s.startQuiz);

  const [data, setData] = useState<CertificationReadiness | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // El formato del simulacro sale de la ruta: sin él, startMockExam caía en
  // 65 preguntas / 90 min también en PCEP (30 / 40).
  const { data: tracks } = useApi<TrackRead[]>(() => contentApi.tracks(), []);
  const track = tracks?.find((tr) => tr.id === trackId);

  useEffect(() => {
    setLoading(true);
    setError(null);
    exams
      .certificationReadiness(trackId)
      .then(setData)
      .catch(() => setError(t('readiness.errorLoading')))
      .finally(() => setLoading(false));
  }, [trackId, t]);

  if (loading) {
    return (
      <div className={styles.screen}>
        <p className={styles.muted} role="status">{t('loading')}</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={styles.screen}>
        <p className={styles.muted}>{error ?? t('readiness.errorLoading')}</p>
        <button type="button" className={styles.btnSecondary} onClick={onExit}>{t('back')}</button>
      </div>
    );
  }

  // ADR-60 / D-16: estado con su evidencia, no porcentaje del modelo.
  const band = examBand(data.domains.map(bandForDomain));
  const answers = data.domains.reduce((sum, d) => sum + (d.answers ?? 0), 0);
  const correct = data.domains.reduce((sum, d) => sum + (d.correct ?? 0), 0);
  const domainsReady = data.domains.filter((d) => d.ready).length;
  const domains = [...data.domains].sort((a, b) => b.weight_pct - a.weight_pct);
  const lever = biggestLever(data.domains);
  const name = (d: DomainReadiness) => (lang === 'en' ? d.name_en : d.name_es);

  return (
    <div className={styles.screen}>
      <header className={styles.header}>
        <button type="button" className={styles.btnClose} onClick={onExit} aria-label={t('back')}>←</button>
        <div>
          <p className={styles.eyebrow}>{track ? (lang === 'en' ? track.name_en : track.name_es) : ''}</p>
          <h1 className={styles.title}>{t('readiness.title')}</h1>
        </div>
      </header>

      <RetiredCertNotice trackId={trackId} />

      <section className={styles.hero} aria-label={t('readiness.title')}>
        <p className={styles.eyebrow}>{t('readiness.gaugeLabel')}</p>
        <p className={`${styles.bandName} ${band === 'strong' ? styles.bandStrong : ''}`} data-testid="readiness-band">
          {t(`bands.${band}`)}
        </p>
        <p className={styles.gaugeMeta}>
          {t('bands.evidence', { answers, correct })} ·{' '}
          <strong>{domainsReady} / {data.domains.length}</strong> {t('readiness.domainsReadyShort')}
        </p>
        <p className={styles.threshold}>
          {band === 'insufficient'
            ? t('readiness.whyInsufficient', { n: MIN_EVIDENCE_ANSWERS })
            : t(`bands.why.${band}`)}
        </p>
      </section>

      {lever && (
        <section className={styles.lever} aria-label={t('readiness.lever')}>
          <p className={styles.leverLabel}>{t('readiness.lever')}</p>
          <p className={styles.leverBody}>
            {t('readiness.leverBody', { name: name(lever), weight: lever.weight_pct, band: t(`bands.${bandForDomain(lever)}`) })}
          </p>
          <button type="button" className={styles.btnPrimary} onClick={() => startQuiz('study', 10, { trackId })}>
            {t('readiness.practice')}
          </button>
          <p className={styles.hint}>{t('readiness.practiceHint')}</p>
        </section>
      )}

      <ul className={styles.domainList}>
        {domains.map((d) => (
          <li key={d.domain_id} className={styles.domain}>
            <div className={styles.domainTop}>
              <span className={styles.domainName}>{name(d)}</span>
              <span className={`${styles.badge} ${bandForDomain(d) === 'strong' ? styles.badgeReady : ''}`}>
                {t(`bands.${bandForDomain(d)}`)}
              </span>
            </div>
            <p className={styles.domainMeta}>
              <span>{t('readiness.weightOf', { n: d.weight_pct })}</span>
              <span>{t('readiness.skillsAssessed', { assessed: d.skills_assessed, total: d.skills_total })}</span>
              <b>{(d.answers ?? 0) > 0 ? t('bands.evidence', { answers: d.answers, correct: d.correct }) : t('readiness.notPractised')}</b>
            </p>
          </li>
        ))}
      </ul>

      <button
        type="button"
        className={styles.btnSecondary}
        onClick={() => {
          onExit();
          startMockExam(trackId, track?.exam_question_count ?? undefined, track?.exam_duration_minutes ?? undefined);
        }}
      >
        {t('readiness.startMock')}
        {track?.exam_question_count && track.exam_duration_minutes && (
          <span className={styles.btnMeta}>
            {t('mockExam.format', { count: track.exam_question_count, minutes: track.exam_duration_minutes })}
          </span>
        )}
      </button>

      <p className={styles.explainer}>{t('readiness.explainer')}</p>
    </div>
  );
}
