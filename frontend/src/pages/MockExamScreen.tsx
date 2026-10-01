import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ApiError,
  exams,
  type CertificatePublic,
  type CertificationAccess,
  type MockExamReport,
  type MockExamStartResponse,
  type QuestionPublic,
} from '../services/api';
import { CertificateCard } from '../components/certificate/CertificateCard';
import { CERTIFICATION_PRICE_USD } from '../lib/plans';
import { checkoutHref } from '../lib/paddle';
import styles from './MockExamScreen.module.css';

type Phase = 'intro' | 'running' | 'grading' | 'result';
/** `mock` rehearses the real exam; `certifying` is the paid sitting that can earn a certificate (38.7). */
type Mode = 'mock' | 'certifying';

interface Props {
  trackId: string;
  /** Blueprint figures shown before starting, so the learner knows what they
   *  are committing to. The server is the authority once the exam begins. */
  questionCount: number;
  durationMinutes: number;
  onExit?: () => void;
}

function formatClock(totalSeconds: number): string {
  const safe = Math.max(0, totalSeconds);
  const minutes = Math.floor(safe / 60);
  const seconds = safe % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

export function MockExamScreen({ trackId, questionCount, durationMinutes, onExit }: Props) {
  const { t, i18n } = useTranslation();
  const isSpanish = i18n.language.startsWith('es');

  const [phase, setPhase] = useState<Phase>('intro');
  const [exam, setExam] = useState<MockExamStartResponse | null>(null);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [report, setReport] = useState<MockExamReport | null>(null);
  const [expired, setExpired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);
  const [mode, setMode] = useState<Mode>('mock');
  const [access, setAccess] = useState<CertificationAccess | null>(null);
  const [certificate, setCertificate] = useState<CertificatePublic | null>(null);

  useEffect(() => {
    let alive = true;
    exams
      .certificationAccess(trackId)
      .then((res) => alive && setAccess(res))
      // No access info means no certifying option shown — the mock still works.
      .catch(() => alive && setAccess(null));
    return () => {
      alive = false;
    };
  }, [trackId]);

  // Guards the auto-submit so a re-render at the deadline cannot fire it twice.
  const submittingRef = useRef(false);

  const questions: QuestionPublic[] = exam?.questions ?? [];
  const current = questions[index];
  const unanswered = questions.length - Object.keys(answers).length;

  const submit = useCallback(async () => {
    if (!exam || submittingRef.current) return;
    submittingRef.current = true;
    setPhase('grading');
    try {
      const res = await exams.submitMock(exam.attempt_id, answers);
      setReport(res.report);
      setExpired(res.expired);
      setCertificate(res.certificate ?? null);
      setPhase('result');
    } catch {
      // Put them back in the exam rather than losing the answers.
      submittingRef.current = false;
      setPhase('running');
      setError(t('mockExam.errorGeneric'));
    }
  }, [exam, answers, t]);

  // The countdown is derived from the server's deadline on every tick rather
  // than decremented locally: a background tab throttles timers, and a clock
  // that drifts would show time the learner does not actually have.
  useEffect(() => {
    if (phase !== 'running' || !exam) return;
    const deadline = new Date(exam.expires_at).getTime();
    const tick = () => {
      const left = Math.round((deadline - Date.now()) / 1000);
      setSecondsLeft(left);
      if (left <= 0) void submit();
    };
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [phase, exam, submit]);

  const start = useCallback(
    async (next: Mode = mode) => {
      setError(null);
      setMode(next);
      setCertificate(null);
      setExam(null);
      setPhase('grading');
      try {
        const res = next === 'certifying' ? await exams.startCertifying(trackId) : await exams.startMock(trackId);
        setExam(res);
        setAnswers({});
        setIndex(0);
        submittingRef.current = false;
        setPhase('running');
      } catch (err) {
        setPhase('intro');
        setError(
          err instanceof ApiError && err.status === 402
            ? t('mockExam.certPurchaseRequired')
            : t('mockExam.errorGeneric'),
        );
      }
    },
    [mode, trackId, t],
  );

  const choose = useCallback(
    (questionId: string, option: number) => {
      setAnswers((prev) => ({ ...prev, [questionId]: option }));
    },
    [],
  );

  const options = useMemo(
    () => (current ? (isSpanish ? current.options_es : current.options_en) ?? [] : []),
    [current, isSpanish],
  );

  if (phase === 'intro' || (phase === 'grading' && !exam)) {
    return (
      <div className={styles.screen}>
        <h1 className={styles.title}>{t('mockExam.title')}</h1>
        <p className={styles.intro}>{t('mockExam.intro')}</p>
        <p className={styles.format}>
          {t('mockExam.format', { count: questionCount, minutes: durationMinutes })}
        </p>
        {error && <p className={styles.error} role="alert">{error}</p>}
        <button className={styles.primary} onClick={() => void start('mock')} disabled={phase === 'grading'}>
          {phase === 'grading' ? t('mockExam.starting') : t('mockExam.start')}
        </button>

        {access && (
          <section className={styles.certifying} aria-labelledby="certifying-title" data-testid="certifying">
            <h2 id="certifying-title" className={styles.subtitle}>{t('mockExam.certTitle')}</h2>
            <p className={styles.intro}>{t('mockExam.certIntro')}</p>
            <p className={styles.format}>
              {t('mockExam.certPrice', { price: isSpanish ? String(CERTIFICATION_PRICE_USD).replace('.', ',') : CERTIFICATION_PRICE_USD })}
            </p>
            {!access.can_start && (
              <a className={styles.primary} href={checkoutHref('certification', trackId)}>
                {t('mockExam.certBuy')}
              </a>
            )}
            <button
              className={styles.secondary}
              onClick={() => void start('certifying')}
              disabled={phase === 'grading' || !access.can_start}
            >
              {t('mockExam.certStart')}
            </button>
          </section>
        )}
      </div>
    );
  }

  if (phase === 'result' && report) {
    const elapsedMinutes = Math.round(report.elapsed_seconds / 60);
    return (
      <div className={styles.screen}>
        <h1 className={styles.title}>{mode === 'certifying' ? t('mockExam.certResults') : t('mockExam.results')}</h1>

        <p className={styles.score}>
          {t('mockExam.rawScore', { correct: report.correct, total: report.questions })}
          <span className={styles.pct}>{report.raw_pct}%</span>
        </p>

        {report.passed != null && (
          <p className={styles.note} role="status">
            <strong>{report.passed ? t('mockExam.certPassed') : t('mockExam.certFailed')}</strong>{' '}
            {isSpanish ? report.pass_note_es : report.pass_note_en}
          </p>
        )}
        {certificate && <CertificateCard certificate={certificate} />}

        {expired && (
          <p className={styles.expired} role="status">
            <strong>{t('mockExam.expired')}</strong> {t('mockExam.expiredNote')}
          </p>
        )}

        {/* The engine never converts a raw percentage into the exam's scaled
            score. The note says why, in the learner's language. */}
        <p className={styles.note}>
          {isSpanish ? report.scoring_note_es : report.scoring_note_en}
        </p>

        <h2 className={styles.subtitle}>{t('mockExam.byDomain')}</h2>
        <p className={styles.caveat}>
          {isSpanish ? report.per_domain_caveat_es : report.per_domain_caveat_en}
        </p>

        <ul className={styles.domains}>
          {report.per_domain.map((domain) => (
            <li key={domain.domain_id} className={styles.domain}>
              <div className={styles.domainHead}>
                <span className={styles.domainName}>
                  {isSpanish ? domain.name_es : domain.name_en}
                </span>
                <span className={styles.domainScore}>
                  {t('mockExam.domainScore', { correct: domain.correct, total: domain.total })}
                </span>
              </div>
              <div
                className={styles.bar}
                role="progressbar"
                aria-valuenow={domain.pct ?? 0}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={isSpanish ? domain.name_es : domain.name_en}
              >
                <div className={styles.barFill} style={{ width: `${domain.pct ?? 0}%` }} />
              </div>
              <div className={styles.domainMeta}>
                <span>{t('mockExam.domainWeight', { weight: domain.weight_pct })}</span>
                {!domain.enough_questions_to_judge && (
                  <span className={styles.tooFew}>{t('mockExam.tooFewToJudge')}</span>
                )}
              </div>
            </li>
          ))}
        </ul>

        <p className={styles.elapsed}>{t('mockExam.elapsed', { minutes: elapsedMinutes })}</p>
        <button className={styles.primary} onClick={() => void start()}>
          {mode === 'certifying' ? t('mockExam.certRetry') : t('mockExam.retry')}
        </button>
        {onExit && (
          <button className={styles.secondary} onClick={onExit}>
            {t('back')}
          </button>
        )}
      </div>
    );
  }

  if (!current) {
    return <div className={styles.screen}><p className={styles.intro}>{t('loading')}</p></div>;
  }

  const timeUp = secondsLeft !== null && secondsLeft <= 0;
  // Under five minutes the clock changes colour AND gains a text label, so the
  // warning does not depend on colour alone.
  const urgent = secondsLeft !== null && secondsLeft <= 300;

  return (
    <div className={styles.screen}>
      <div className={styles.examBar}>
        <span className={styles.counter}>
          {t('mockExam.question', { current: index + 1, total: questions.length })}
        </span>
        <span
          className={urgent ? styles.clockUrgent : styles.clock}
          role="timer"
          aria-live="off"
          aria-label={t('mockExam.timeLeft')}
        >
          {timeUp ? t('mockExam.timeUp') : formatClock(secondsLeft ?? 0)}
        </span>
      </div>

      <p className={styles.question}>{isSpanish ? current.question_es : current.question_en}</p>

      <div className={styles.options} role="radiogroup" aria-label={t('mockExam.title')}>
        {options.map((option, optionIndex) => {
          const selected = answers[current.id] === optionIndex;
          return (
            <button
              key={option}
              role="radio"
              aria-checked={selected}
              className={selected ? styles.optionSelected : styles.option}
              onClick={() => choose(current.id, optionIndex)}
            >
              {option}
            </button>
          );
        })}
      </div>

      {error && <p className={styles.error} role="alert">{error}</p>}

      <div className={styles.nav}>
        <button
          className={styles.secondary}
          onClick={() => setIndex((i) => Math.max(0, i - 1))}
          disabled={index === 0}
        >
          {t('mockExam.previous')}
        </button>
        {index < questions.length - 1 ? (
          <button className={styles.primary} onClick={() => setIndex((i) => i + 1)}>
            {t('mockExam.next')}
          </button>
        ) : (
          <button className={styles.primary} onClick={() => void submit()}>
            {phase === 'grading' ? t('mockExam.finishing') : t('mockExam.finish')}
          </button>
        )}
      </div>

      {unanswered > 0 && (
        <p className={styles.unanswered}>
          {t('mockExam.unansweredWarning', { count: unanswered })}
        </p>
      )}
    </div>
  );
}
