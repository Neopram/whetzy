import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { lessonsApi, type LessonRead } from '../services/api';
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
      .catch(() => setError(t('lesson.errorLoading', 'No se pudo cargar la lección.')))
      .finally(() => setLoading(false));
  }, [skillId, t]);

  if (loading) {
    return (
      <div className={styles.screen}>
        <p className={styles.loadingMsg}>⏳ {t('lesson.loading', 'Cargando lección…')}</p>
      </div>
    );
  }

  if (error || lessons.length === 0) {
    return (
      <div className={styles.screen}>
        <p className={styles.errorMsg}>{error ?? t('lesson.noContent', 'No hay lecciones para esta habilidad todavía.')}</p>
        <button className={styles.btnBack} onClick={onExit}>
          {t('lesson.back', '← Volver')}
        </button>
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
