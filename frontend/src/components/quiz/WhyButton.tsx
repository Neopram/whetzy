import { useEffect, useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ApiError, reports, tutor as tutorApi, type ExplainResponse, type TutorMode } from '../../services/api';
import { useAppStore } from '../../stores/useAppStore';
import { TUTOR_DAILY_LIMIT_PRO } from '../../lib/plans';
import styles from './WhyButton.module.css';

type Status = 'idle' | 'upsell' | 'deepUpsell' | 'loading' | 'result' | 'error' | 'limit';

const MODES: TutorMode[] = ['why', 'how', 'deep'];

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
  const [aiReport, setAiReport] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [mode, setMode] = useState<TutorMode>('why');
  const deepAccess = useAppStore((s) => s.user.tutorDeepAccess);
  const panelId = useId();

  // A new question means a clean slate — never show a stale explanation.
  useEffect(() => {
    setStatus('idle');
    setResult(null);
    setAiReport('idle');
    setMode('why');
  }, [questionId]);

  // Reportar la explicación (AI Act art. 50 y la «revisión humana» de la nota de
  // IA): el texto se genera al vuelo y no se guarda, así que viaja en la nota.
  async function reportExplanation() {
    if (!result) return;
    setAiReport('sending');
    try {
      await reports.question(questionId, 'ai_explanation', result.explanation.slice(0, 3900));
      setAiReport('sent');
    } catch {
      setAiReport('error');
    }
  }

  const expanded = status !== 'idle';

  async function fetchExplanation(next: TutorMode = mode) {
    setStatus('loading');
    setAiReport('idle');
    try {
      const res = await tutorApi.explain(questionId, next);
      setResult(res);
      setStatus('result');
    } catch (err) {
      setResult(null);
      // Pro's daily cap (38.6): not an outage, so no "try again" — it resets tomorrow.
      setStatus(err instanceof ApiError && err.status === 429 && err.message === 'tutor_daily_limit' ? 'limit' : 'error');
    }
  }

  // Ola 2: «A fondo» es de Pro Max. Sin acceso se explica, sin llamar al servidor.
  function chooseMode(next: TutorMode) {
    setMode(next);
    if (next === 'deep' && !deepAccess) {
      setResult(null);
      setStatus('deepUpsell');
      return;
    }
    void fetchExplanation(next);
  }

  function handleToggle() {
    if (status === 'idle') {
      if (!isPremium) {
        setStatus('upsell');
      } else {
        setMode('why');
        void fetchExplanation('why');
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
        {t('quiz.why.button')}
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

          {isPremium && status !== 'upsell' && (
            <div className={styles.modes} role="group" aria-label={t('quiz.why.modesLabel')}>
              {MODES.map((m) => (
                <button
                  key={m}
                  type="button"
                  className={styles.modeBtn}
                  aria-pressed={mode === m}
                  disabled={status === 'loading'}
                  onClick={() => chooseMode(m)}
                >
                  {t(`quiz.why.modes.${m}`)}
                  {m === 'deep' && !deepAccess && <span className={styles.modeTag}>{t('quiz.why.proMaxTag')}</span>}
                </button>
              ))}
            </div>
          )}

          {status === 'deepUpsell' && (
            <div className={styles.upsell}>
              <span className={styles.upsellBadge}>{t('quiz.why.proMaxTag')}</span>
              <p className={styles.upsellTitle}>{t('quiz.why.deepUpsellTitle')}</p>
              <p className={styles.upsellBody}>{t('quiz.why.deepUpsellBody')}</p>
              <button type="button" className={styles.upsellCta} onClick={onUpgrade}>
                {t('quiz.why.limitCta')}
              </button>
            </div>
          )}

          {status === 'upsell' && (
            <div className={styles.upsell}>
              <span className={styles.upsellBadge}>{t('quiz.why.upsellBadge')}</span>
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
              <button type="button" className={styles.retryBtn} onClick={() => void fetchExplanation(mode)}>
                {t('quiz.why.retry')}
              </button>
            </div>
          )}

          {status === 'result' && result && (
            <div className={styles.result}>
              <p className={styles.aiLabel}>{t('quiz.why.aiLabel')}</p>
              <p className={styles.resultText}>{result.explanation || t('quiz.why.empty')}</p>
              <span
                className={`${styles.sourceBadge} ${result.grounded ? styles.sourceGrounded : styles.sourceGeneral}`}
              >
                {result.grounded
                  ? t('quiz.why.sourceGrounded')
                  : t('quiz.why.sourceGeneral')}
              </span>
              {result.explanation && (aiReport === 'sent' ? (
                <p className={styles.aiReported} role="status">{t('quiz.why.reportedAi')}</p>
              ) : (
                <button
                  type="button"
                  className={styles.reportAi}
                  onClick={() => void reportExplanation()}
                  disabled={aiReport === 'sending'}
                >
                  {aiReport === 'error' ? t('quiz.why.reportAiRetry') : t('quiz.why.reportAi')}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
