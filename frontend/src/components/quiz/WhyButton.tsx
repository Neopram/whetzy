import { useEffect, useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ApiError, tutor as tutorApi, type ExplainResponse } from '../../services/api';
import { TUTOR_DAILY_LIMIT_PRO } from '../../lib/plans';
import styles from './WhyButton.module.css';

type Status = 'idle' | 'upsell' | 'loading' | 'result' | 'error' | 'limit';

interface WhyButtonProps {
  /** The current question's id — the panel resets whenever this changes. */
  questionId: string;
  /** Whether the signed-in user is entitled to AI tutor explanations (Plus/Pro). */
  isPremium: boolean;
  /** Called when a free user taps the upsell CTA — navigate to the upgrade screen. */
  onUpgrade: () => void;
}

/**
 * "¿Por qué? / Why?" — the visible entry point into the AI tutor.
 *
 * Free users see the button and an honest upsell (no network call, no fake
 * loading state — GAP-5 / red line 7: never dress up a paywall as a working
 * feature). Plus/Pro users get a real explanation from the tutor endpoint,
 * always labeled with whether it was grounded in course content (red line 2).
 */
export function WhyButton({ questionId, isPremium, onUpgrade }: WhyButtonProps) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<Status>('idle');
  const [result, setResult] = useState<ExplainResponse | null>(null);
  const panelId = useId();

  // A new question means a clean slate — never show a stale explanation.
  useEffect(() => {
    setStatus('idle');
    setResult(null);
  }, [questionId]);

  const expanded = status !== 'idle';

  async function fetchExplanation() {
    setStatus('loading');
    try {
      const res = await tutorApi.explain(questionId);
      setResult(res);
      setStatus('result');
    } catch (err) {
      setResult(null);
      // Pro's daily cap (38.6): not an outage, so no "try again" — it resets tomorrow.
      setStatus(err instanceof ApiError && err.status === 429 && err.message === 'tutor_daily_limit' ? 'limit' : 'error');
    }
  }

  function handleToggle() {
    if (status === 'idle') {
      if (!isPremium) {
        setStatus('upsell');
      } else {
        void fetchExplanation();
      }
    } else {
      setStatus('idle');
    }
  }

  return (
    <div className={styles.wrap} data-testid="why-button">
      <button
        type="button"
        className={styles.toggleBtn}
        onClick={handleToggle}
        aria-expanded={expanded}
        aria-controls={panelId}
      >
        <span aria-hidden="true">🧠</span> {t('quiz.why.button')}
      </button>

      {expanded && (
        <div
          id={panelId}
          className={styles.panel}
          role="region"
          aria-label={t('quiz.why.title')}
          aria-live="polite"
        >
          <button
            type="button"
            className={styles.closeBtn}
            onClick={() => setStatus('idle')}
            aria-label={t('quiz.why.close')}
          >
            <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16" aria-hidden="true">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
            </svg>
          </button>

          {status === 'upsell' && (
            <div className={styles.upsell}>
              <span className={styles.upsellBadge}>👑 {t('quiz.why.upsellBadge')}</span>
              <p className={styles.upsellTitle}>{t('quiz.why.upsellTitle')}</p>
              <p className={styles.upsellBody}>{t('quiz.why.upsellBody')}</p>
              <button type="button" className={styles.upsellCta} onClick={onUpgrade}>
                {t('quiz.why.upsellCta')}
              </button>
            </div>
          )}

          {status === 'limit' && (
            <div className={styles.upsell} role="status">
              <p className={styles.upsellTitle}>{t('quiz.why.limitTitle')}</p>
              <p className={styles.upsellBody}>{t('quiz.why.limitBody', { limit: TUTOR_DAILY_LIMIT_PRO })}</p>
              <button type="button" className={styles.upsellCta} onClick={onUpgrade}>
                {t('quiz.why.limitCta')}
              </button>
            </div>
          )}

          {status === 'loading' && (
            <div className={styles.skeleton} aria-busy="true">
              <span className="visually-hidden">{t('quiz.why.loadingSr')}</span>
              <div className={styles.skeletonLine} />
              <div className={styles.skeletonLine} />
              <div className={`${styles.skeletonLine} ${styles.skeletonShort}`} />
            </div>
          )}

          {status === 'error' && (
            <div className={styles.errorBox} role="alert">
              <p className={styles.errorText}>{t('quiz.why.error')}</p>
              <button type="button" className={styles.retryBtn} onClick={() => void fetchExplanation()}>
                {t('quiz.why.retry')}
              </button>
            </div>
          )}

          {status === 'result' && result && (
            <div className={styles.result}>
              <p className={styles.resultText}>{result.explanation || t('quiz.why.empty')}</p>
              <span
                className={`${styles.sourceBadge} ${result.grounded ? styles.sourceGrounded : styles.sourceGeneral}`}
              >
                {result.grounded
                  ? `📚 ${t('quiz.why.sourceGrounded')}`
                  : `ℹ ${t('quiz.why.sourceGeneral')}`}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
