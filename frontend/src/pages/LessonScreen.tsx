import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { AnimatePresence, motion } from 'framer-motion';
import { useAppStore } from '../stores/useAppStore';
import { lessonsApi, isQuotaError, type LessonRead } from '../services/api';
import { lessonSteps, parseSource } from '../lib/lessonSteps';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorState } from '../components/common/ErrorState';
import styles from './LessonScreen.module.css';

interface Props {
  skillId: string;
  onExit: () => void;
  onStartQuiz?: () => void;
}

export function LessonScreen({ skillId, onExit, onStartQuiz }: Props) {
  const { t } = useTranslation();
  const language = useAppStore((s) => s.user.language);

  const [lessons, setLessons] = useState<LessonRead[]>([]);
  const [step, setStep] = useState(0);
  const [showOutput, setShowOutput] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setStep(0);
    lessonsApi
      .forSkill(skillId)
      .then((data) => setLessons(data))
      .catch((e) => {
        // Free-tier daily quota (39.4/39.34): a friendly message with the
        // reset time instead of the generic load-error copy.
        if (isQuotaError(e)) {
          setError(
            t('lesson.quotaReachedLessons', {
              limit: e.detail.limit,
              time: new Date(e.detail.resets_at).toLocaleTimeString(),
            }),
          );
        } else {
          setError(t('lesson.errorLoading', 'No se pudo cargar la lección.'));
        }
      })
      .finally(() => setLoading(false));
  }, [skillId, t]);

  const steps = useMemo(() => lessonSteps(lessons, language), [lessons, language]);
  const isLast = step === steps.length - 1;
  const finish = onStartQuiz ?? onExit;

  // ← / → recorren los pasos, como los botones del pie. Con actualización
  // funcional el listener no depende de `step`: dos flechas seguidas no leen un
  // paso viejo entre que React pinta y re-engancha el listener.
  useEffect(() => {
    const last = steps.length - 1;
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLElement && e.target.closest('input, textarea')) return;
      if (e.key === 'ArrowRight') setStep((s) => Math.min(s + 1, Math.max(last, 0)));
      if (e.key === 'ArrowLeft') setStep((s) => Math.max(s - 1, 0));
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [steps.length]);

  useEffect(() => { setShowOutput(false); }, [step]);

  if (loading) {
    return (
      <div className={styles.screen}>
        <LoadingState message={t('lesson.loading', 'Cargando lección…')} fullScreen />
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.screen}>
        <ErrorState
          message={error}
          retryLabel={t('lesson.back', '← Volver')}
          onRetry={onExit}
        />
      </div>
    );
  }

  if (steps.length === 0) {
    return (
      <div className={styles.screen}>
        <EmptyState
          icon="📚"
          title={t('lesson.noContentTitle', 'Sin contenido disponible')}
          description={t('lesson.noContent', 'No hay lecciones para esta habilidad todavía.')}
          actionLabel={t('lesson.back', '← Volver')}
          onAction={onExit}
        />
      </div>
    );
  }

  const current = steps[step];
  const lesson = lessons[current.lesson];
  const title = language === 'en' ? lesson.title_en : lesson.title_es;
  const source = parseSource(lesson.source);

  return (
    <div className={styles.screen}>
      <header className={styles.header}>
        <button type="button" className={styles.btnClose} onClick={onExit} aria-label={t('lesson.close', 'Cerrar')}>
          ✕
        </button>
        <div
          className={styles.progress}
          role="progressbar"
          aria-label={t('lesson.stepOf', { current: step + 1, total: steps.length })}
          aria-valuenow={step + 1}
          aria-valuemin={1}
          aria-valuemax={steps.length}
        >
          {steps.map((_, i) => (
            <span key={i} className={`${styles.seg} ${i <= step ? styles.segDone : ''}`} />
          ))}
        </div>
        <span className={styles.counter} aria-hidden="true">
          {step + 1} / {steps.length}
        </span>
      </header>

      <main className={styles.main}>
        <p className={styles.eyebrow}>
          <span aria-hidden="true">{current.kind === 'example' ? '🧪' : '💡'}</span>
          {current.kind === 'example' ? t('lesson.example') : t('lesson.concept')}
        </p>
        <h1 className={styles.title}>{title}</h1>

        <AnimatePresence mode="wait">
          <motion.section
            key={step}
            className={styles.card}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
            transition={{ duration: 0.16 }}
            aria-live="polite"
          >
            {current.kind === 'text' ? (
              <p className={styles.body}>{current.text}</p>
            ) : (
              <>
                <pre className={styles.code}><code>{lesson.example_code}</code></pre>
                {lesson.example_output && (
                  showOutput ? (
                    <div className={styles.output}>
                      <span className={styles.outputLabel}>
                        <span aria-hidden="true">📤</span>
                        {t('lesson.output')}
                      </span>
                      <pre className={styles.outputPre}>{lesson.example_output}</pre>
                    </div>
                  ) : (
                    <div className={styles.predict}>
                      <p>{t('lesson.predict')}</p>
                      <button type="button" className={styles.btnGhost} onClick={() => setShowOutput(true)}>
                        {t('lesson.showOutput')}
                      </button>
                    </div>
                  )
                )}
              </>
            )}
          </motion.section>
        </AnimatePresence>

        <p className={styles.source}>
          <span aria-hidden="true">🔗</span>
          <span>
            {t('lesson.source')}:{' '}
            {source.url ? (
              <a href={source.url} target="_blank" rel="noopener noreferrer">{source.label}</a>
            ) : (
              source.label
            )}
          </span>
        </p>
      </main>

      <footer className={styles.footer}>
        <button
          type="button"
          className={styles.btnGhost}
          onClick={() => setStep((s) => s - 1)}
          disabled={step === 0}
        >
          ← {t('lesson.prev')}
        </button>
        {!isLast ? (
          <button type="button" className={styles.btnPrimary} onClick={() => setStep((s) => s + 1)}>
            {t('lesson.next')} →
          </button>
        ) : (
          <button type="button" className={styles.btnPrimary} onClick={finish}>
            {onStartQuiz ? t('lesson.startPractice') : t('lesson.done')}
          </button>
        )}
      </footer>
    </div>
  );
}
