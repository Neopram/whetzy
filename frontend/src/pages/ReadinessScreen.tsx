import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { exams, type CertificationReadiness } from '../services/api';
import styles from './ReadinessScreen.module.css';

interface Props {
  trackId: string;
  onExit: () => void;
}

const READY_THRESHOLD = 0.75;

function DomainBar({ pKnown, weight }: { pKnown: number; weight: number }) {
  const pct = Math.round(pKnown * 100);
  const ready = pKnown >= READY_THRESHOLD;
  return (
    <div className={styles.barTrack} aria-label={`${pct}%`}>
      <div
        className={`${styles.barFill} ${ready ? styles.barReady : ''}`}
        style={{ width: `${pct}%` }}
      />
      <span className={styles.barWeight}>{weight}%</span>
    </div>
  );
}

export function ReadinessScreen({ trackId, onExit }: Props) {
  const { t } = useTranslation();
  const lang = useAppStore((s) => s.user.language);
  const startMockExam = useAppStore((s) => s.startMockExam);

  const [data, setData] = useState<CertificationReadiness | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
        <p className={styles.muted}>⏳ {t('loading')}</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={styles.screen}>
        <p className={styles.muted}>{error ?? t('readiness.errorLoading')}</p>
        <button className={styles.btnBack} onClick={onExit}>
          {t('back')}
        </button>
      </div>
    );
  }

  const overallPct = Math.round(data.overall_p_known * 100);
  const overallReady = data.overall_p_known >= READY_THRESHOLD;
  const domainsReady = data.domains.filter((d) => d.ready).length;

  return (
    <div className={styles.screen}>
      <header className={styles.header}>
        <button className={styles.btnClose} onClick={onExit} aria-label={t('back')}>
          ←
        </button>
        <h1 className={styles.title}>{t('readiness.title')}</h1>
      </header>

      {/* Overall gauge */}
      <div className={`${styles.gaugeCard} ${overallReady ? styles.gaugeCardReady : ''}`}>
        <div className={styles.gaugeRow}>
          <span className={styles.gaugePct}>{overallPct}%</span>
          <span className={`${styles.gaugeBadge} ${overallReady ? styles.gaugeBadgeReady : ''}`}>
            {overallReady ? t('readiness.ready') : t('readiness.notReady')}
          </span>
        </div>
        <p className={styles.gaugeSub}>
          {t('readiness.domainsReady', { done: domainsReady, total: data.domains.length })}
        </p>
        <div className={styles.overallBar}>
          <div
            className={`${styles.overallFill} ${overallReady ? styles.overallFillReady : ''}`}
            style={{ width: `${overallPct}%` }}
          />
        </div>
        <p className={styles.gaugeThreshold}>
          {t('readiness.threshold', { pct: Math.round(READY_THRESHOLD * 100) })}
        </p>
      </div>

      {/* Per-domain breakdown */}
      <div className={styles.domainList}>
        {data.domains.map((d) => {
          const name = lang === 'en' ? d.name_en : d.name_es;
          const pct = Math.round(d.p_known_mean * 100);
          return (
            <div key={d.domain_id} className={`${styles.domainCard} ${d.ready ? styles.domainCardReady : ''}`}>
              <div className={styles.domainTop}>
                <span className={styles.domainName}>{name}</span>
                <span className={`${styles.domainChip} ${d.ready ? styles.domainChipReady : ''}`}>
                  {d.ready ? '✓' : `${pct}%`}
                </span>
              </div>
              <DomainBar pKnown={d.p_known_mean} weight={d.weight_pct} />
              <p className={styles.domainMeta}>
                {t('readiness.skillsAssessed', {
                  assessed: d.skills_assessed,
                  total: d.skills_total,
                })}
              </p>
            </div>
          );
        })}
      </div>

      {/* CTA: start mock exam */}
      <button
        className={styles.ctaBtn}
        onClick={() => {
          onExit();
          startMockExam(trackId);
        }}
      >
        {t('readiness.startMock')}
      </button>

      <p className={styles.explainer}>{t('readiness.explainer')}</p>
    </div>
  );
}
