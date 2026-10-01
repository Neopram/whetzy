import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { lessonsApi, isQuotaError, type LessonRead } from '../services/api';
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

  if (lessons.length === 0) {
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

  const lesson = lessons[step];
  const title = language === 'en' ? lesson.title_en : lesson.title_es;
  const body = language === 'en' ? lesson.body_en : lesson.body_es;
  const isLast = step === lessons.length - 1;

  return (
    <div className={styles.screen}>
      <header className={styles.header}>
        <button className={styles.btnClose} onClick={onExit} aria-label={t('lesson.close', 'Cerrar')}>
          ✕
        </button>
        <div className={styles.progress}>
          {lessons.map((_, i) => (
            <span
              key={i}
              className={`${styles.dot} ${i <= step ? styles.dotActive : ''}`}
            />
          ))}
        </div>
      </header>

      <main className={styles.main}>
        <h1 className={styles.title}>{title}</h1>

        <div className={styles.body}>
          {body.split('\n').filter(Boolean).map((para, i) => (
            <p key={i}>{para}</p>
          ))}
        </div>

        {lesson.example_code && (
          <div className={styles.exampleBlock}>
            <span className={styles.exampleLabel}>{t('lesson.example', 'Ejemplo')}</span>
            <pre className={styles.codeBlock}>
              <code>{lesson.example_code}</code>
            </pre>
            {lesson.example_output && (
              <div className={styles.outputBlock}>
                <span className={styles.outputLabel}>→</span>
                <pre className={styles.outputPre}>{lesson.example_output}</pre>
              </div>
            )}
          </div>
        )}

        <div className={styles.sourceRow}>
          <span className={styles.sourceIcon}>📖</span>
          <span className={styles.sourceText}>{lesson.source}</span>
        </div>
      </main>

      <footer className={styles.footer}>
        {step > 0 && (
          <button className={styles.btnSecondary} onClick={() => setStep((s) => s - 1)}>
            {t('lesson.prev', '← Anterior')}
          </button>
        )}

        {!isLast ? (
          <button className={styles.btnPrimary} onClick={() => setStep((s) => s + 1)}>
            {t('lesson.next', 'Siguiente →')}
          </button>
        ) : (
          <button
            className={styles.btnPrimary}
            onClick={onStartQuiz ?? onExit}
          >
            {onStartQuiz
              ? t('lesson.startPractice', '▶ Practicar ahora')
              : t('lesson.done', '✓ Listo')}
          </button>
        )}
      </footer>
    </div>
  );
}
