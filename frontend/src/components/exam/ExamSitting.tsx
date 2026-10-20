/**
 * La vista de examen en curso, común al simulacro, al examen certificador y al
 * examen final de ruta (design/v2, brief-msg2 §F). Antes cada pantalla
 * repetía la suya, con la pregunta en texto plano: una pregunta con bloque de
 * código salía con los ``` a la vista.
 *
 * Añade lo que pedía el brief: cuadrícula para saltar a cualquier pregunta
 * (respondida / marcada / pendiente), «Marcar para revisar» y una
 * confirmación al entregar con preguntas en blanco, que cuentan como falladas.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, useReducedMotion } from 'framer-motion';
import { DUR } from '../../lib/motion';
import type { QuestionPublic } from '../../services/api';
import { parseQuestion } from '../../lib/question';
import { formatClock } from '../../hooks/useTimedExam';
import styles from './ExamSitting.module.css';

interface Props {
  title: string;
  questions: QuestionPublic[];
  index: number;
  onGo: (index: number) => void;
  answers: Record<string, number>;
  onChoose: (questionId: string, option: number) => void;
  secondsLeft: number | null;
  grading: boolean;
  error: string | null;
  onSubmit: () => void;
}

export function ExamSitting({
  title, questions, index, onGo, answers, onChoose, secondsLeft, grading, error, onSubmit,
}: Props) {
  const { t, i18n } = useTranslation();
  const isSpanish = i18n.language.startsWith('es');
  const [flagged, setFlagged] = useState<Set<string>>(new Set());
  const [confirming, setConfirming] = useState(false);
  const reduce = useReducedMotion();

  const current = questions[index];
  if (!current) return null;

  const options = (isSpanish ? current.options_es : current.options_en) ?? [];
  const { prose, code } = parseQuestion(isSpanish ? current.question_es : current.question_en);
  const unanswered = questions.filter((q) => answers[q.id] === undefined).length;
  const isLast = index === questions.length - 1;
  const isFlagged = flagged.has(current.id);
  const timeUp = secondsLeft !== null && secondsLeft <= 0;
  // Bajo cinco minutos el reloj cambia de color y además de texto: el aviso
  // no depende solo del color (línea roja 6).
  const urgent = secondsLeft !== null && secondsLeft <= 300;

  const toggleFlag = () =>
    setFlagged((prev) => {
      const next = new Set(prev);
      if (next.has(current.id)) next.delete(current.id);
      else next.add(current.id);
      return next;
    });

  const requestSubmit = () => {
    if (unanswered > 0) setConfirming(true);
    else onSubmit();
  };

  return (
    <div className={styles.sitting}>
      <div className={styles.bar}>
        <span className={styles.counter}>
          {t('mockExam.question', { current: index + 1, total: questions.length })}
        </span>
        {/* 46.15 C: al entrar en los 5 últimos minutos el reloj late una vez (la
            `key` lo remonta solo en ese cambio). Sin sonido: avisa, no asusta. */}
        <motion.span
          key={urgent ? 'urgent' : 'calm'}
          className={urgent ? styles.clockUrgent : styles.clock}
          role="timer"
          aria-live="off"
          aria-label={t('mockExam.timeLeft')}
          data-fx={urgent && !reduce ? 'urgent' : undefined}
          animate={urgent && !reduce ? { scale: [1, 1.15, 1] } : undefined}
          transition={{ duration: DUR.response }}
        >
          {timeUp ? t('mockExam.timeUp') : formatClock(secondsLeft ?? 0)}
        </motion.span>
      </div>

      <div className={styles.question}>
        <p className={styles.prose}>{prose}</p>
        {code && <pre className={styles.code}><code>{code}</code></pre>}
      </div>

      <div className={styles.options} role="radiogroup" aria-label={title}>
        {options.map((option, i) => {
          const selected = answers[current.id] === i;
          return (
            <button
              key={`${current.id}-${i}`}
              type="button"
              role="radio"
              aria-checked={selected}
              className={`${styles.option} ${selected ? styles.optionSelected : ''}`}
              onClick={() => onChoose(current.id, i)}
            >
              <span className={styles.letter} aria-hidden="true">{String.fromCharCode(65 + i)}</span>
              <span>{option}</span>
            </button>
          );
        })}
      </div>

      <button type="button" className={styles.flag} aria-pressed={isFlagged} onClick={toggleFlag}>
        {isFlagged ? t('mockExam.flagged') : t('mockExam.flag')}
      </button>

      {error && <p className={styles.error} role="alert">{error}</p>}

      <div className={styles.nav}>
        <button type="button" className={styles.secondary} onClick={() => onGo(Math.max(0, index - 1))} disabled={index === 0}>
          {t('mockExam.previous')}
        </button>
        {!isLast ? (
          <button type="button" className={styles.primary} onClick={() => onGo(index + 1)}>
            {t('mockExam.next')}
          </button>
        ) : (
          <button type="button" className={styles.primary} onClick={requestSubmit} disabled={grading}>
            {grading ? t('mockExam.finishing') : t('mockExam.finish')}
          </button>
        )}
      </div>

      {confirming && (
        <div className={styles.confirm} role="alertdialog" aria-label={t('mockExam.confirmTitle')}>
          <p>{t('mockExam.unansweredWarning', { count: unanswered })}</p>
          <div className={styles.nav}>
            <button type="button" className={styles.secondary} onClick={() => setConfirming(false)} autoFocus>
              {t('mockExam.keepAnswering')}
            </button>
            <button type="button" className={styles.primary} onClick={() => { setConfirming(false); onSubmit(); }}>
              {t('mockExam.submitAnyway')}
            </button>
          </div>
        </div>
      )}

      <details className={styles.navigator}>
        <summary className={styles.summary}>
          {t('mockExam.overview', { answered: questions.length - unanswered, total: questions.length, flagged: flagged.size })}
        </summary>
        <ol className={styles.grid}>
          {questions.map((q, i) => {
            const state = flagged.has(q.id) ? 'flagged' : answers[q.id] !== undefined ? 'answered' : 'pending';
            return (
              <li key={q.id}>
                <button
                  type="button"
                  className={`${styles.cell} ${styles[state]} ${i === index ? styles.cellCurrent : ''}`}
                  aria-current={i === index ? 'step' : undefined}
                  aria-label={t('mockExam.cellLabel', { n: i + 1, state: t(`mockExam.state_${state}`) })}
                  onClick={() => onGo(i)}
                >
                  {i + 1}
                </button>
              </li>
            );
          })}
        </ol>
      </details>

      {unanswered > 0 && !confirming && (
        <p className={styles.unanswered}>{t('mockExam.unansweredWarning', { count: unanswered })}</p>
      )}
    </div>
  );
}
