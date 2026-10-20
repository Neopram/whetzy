import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, useReducedMotion } from 'framer-motion';
import { listItemVariants, listVariants } from '../lib/motion';
import { useAppStore } from '../stores/useAppStore';
import { useApi } from '../hooks/useApi';
import { bandForDomain, examBand, MIN_EVIDENCE_ANSWERS } from '../lib/evidenceBand';
import { content as contentApi, exams, type CertificationReadiness, type DomainReadiness, type TrackRead } from '../services/api';
import { RetiredCertNotice } from '../components/common/RetiredCertNotice';
import { LeverCard } from '../components/readiness/LeverCard';
import { biggestLever } from '../lib/readinessLever';
import styles from './ReadinessScreen.module.css';

interface Props {
  trackId: string;
  onExit: () => void;
}

export function ReadinessScreen({ trackId, onExit }: Props) {
  const { t } = useTranslation();
  const reduce = useReducedMotion();
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

      {lever && <LeverCard lever={lever} name={name(lever)} onPractice={() => startQuiz('study', 10, { trackId })} />}

      {/* 46.13: los dominios entran escalonados (plan §6.2). */}
      <motion.ul
        className={styles.domainList}
        {...(reduce ? {} : { 'data-enter': 'stagger', variants: listVariants, initial: 'initial', animate: 'animate' })}
      >
        {domains.map((d) => (
          <motion.li key={d.domain_id} className={styles.domain} variants={listItemVariants}>
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
          </motion.li>
        ))}
      </motion.ul>

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
