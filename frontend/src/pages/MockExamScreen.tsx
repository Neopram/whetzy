import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, useReducedMotion } from 'framer-motion';
import { DUR } from '../lib/motion';
import { emit as emitFx } from '../lib/feedbackFx';
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
import { ExamSitting } from '../components/exam/ExamSitting';
import { CERTIFICATION_PRICE_USD } from '../lib/plans';
import { checkoutHref } from '../lib/paddle';
import { RetiredCertNotice } from '../components/common/RetiredCertNotice';
import { showToast } from '../components/common/Toast';
import { useBackGuard } from '../lib/screenHistory';
import styles from './MockExamScreen.module.css';
import { Loading } from '../components/common/Loading';

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

export function MockExamScreen({ trackId, questionCount, durationMinutes, onExit }: Props) {
  const { t, i18n } = useTranslation();
  const isSpanish = i18n.language.startsWith('es');

  const [phase, setPhase] = useState<Phase>('intro');
  const [exam, setExam] = useState<MockExamStartResponse | null>(null);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [report, setReport] = useState<MockExamReport | null>(null);
  // Con el examen en marcha «atrás» no sale (el reloj sigue en el servidor);
  // antes de empezar y con el resultado, sí.
  useBackGuard(() => {
    if (phase === 'running' || phase === 'grading') showToast(t('mockExam.backBlocked'), 'info');
    else onExit?.();
  });
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

  // 46.15 C: el resultado del servidor cierra la sesión (nivel 3), una vez.
  const reduce = useReducedMotion();
  useEffect(() => {
    if (phase === 'result' && report) emitFx({ type: 'session_end' });
  }, [phase, report]);

  if (phase === 'intro' || (phase === 'grading' && !exam)) {
    return (
      <div className={styles.screen}>
        <h1 className={styles.title}>{t('mockExam.title')}</h1>
        <RetiredCertNotice trackId={trackId} />
        <p className={styles.intro}>{t('mockExam.intro')}</p>
        <p className={styles.format}>
          {t('mockExam.format', { count: questionCount, minutes: durationMinutes })}
        </p>
        <p className={styles.intro}>{t('trackExam.unansweredCountsWrong')}</p>
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
            {!access.available && (
              <p className={styles.intro} role="note">{t('mockExam.certUnavailable')}</p>
            )}
            {access.available && !access.can_start && (
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
          <motion.p
            className={styles.note}
            role="status"
            data-testid="exam-verdict"
            data-fx={reduce ? undefined : 'reveal'}
            initial={reduce ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: DUR.response }}
          >
            <strong>{report.passed ? t('mockExam.certPassed') : t('mockExam.certFailed')}</strong>{' '}
            {isSpanish ? report.pass_note_es : report.pass_note_en}
          </motion.p>
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
    return <div className={styles.screen}><Loading label={t('loading')} shape="card" /></div>;
  }

  return (
    <div className={styles.screen}>
      <ExamSitting
        title={t('mockExam.title')}
        questions={questions}
        index={index}
        onGo={setIndex}
        answers={answers}
        onChoose={choose}
        secondsLeft={secondsLeft}
        grading={phase === 'grading'}
        error={error}
        onSubmit={() => void submit()}
      />
    </div>
  );
}
