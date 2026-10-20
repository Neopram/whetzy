/**
 * Track final exam and module test-out (17.2).
 *
 * The sitting itself — clock, navigation, auto-submit on the deadline — comes
 * from `useTimedExam`, which is the same machinery `MockExamScreen` runs. What
 * this screen owns is the part that genuinely differs: a verdict (pass or not),
 * a per-skill breakdown instead of per-domain, and, for a passed final, the
 * certificate.
 *
 * Styles are borrowed from `MockExamScreen.module.css` on purpose: an exam that
 * looks like a different product depending on which exam it is would be the
 * kind of inconsistency the design standard exists to prevent.
 */
import { useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, useReducedMotion } from 'framer-motion';
import { DUR } from '../lib/motion';
import { emit as emitFx } from '../lib/feedbackFx';

import {
  exams,
  type QuestionPublic,
  type TrackExamStartResponse,
  type TrackExamSubmitResponse,
} from '../services/api';
import { CertificateCard } from '../components/certificate/CertificateCard';
import { ExamSitting } from '../components/exam/ExamSitting';
import { useTimedExam } from '../hooks/useTimedExam';
import { showToast } from '../components/common/Toast';
import { useBackGuard } from '../lib/screenHistory';
import styles from './MockExamScreen.module.css';
import own from './TrackExamScreen.module.css';
import { Loading } from '../components/common/Loading';

interface Props {
  /** A track final ('track_final') or a module test-out ('test_out'). */
  kind: 'track_final' | 'test_out';
  /** Track id for a final, module id for a test-out. */
  targetId: string;
  /** Blueprint figures shown before committing. The server decides once it starts. */
  questionCount: number;
  durationMinutes: number;
  passPct: number;
  onExit?: () => void;
}

export function TrackExamScreen({
  kind,
  targetId,
  questionCount,
  durationMinutes,
  passPct,
  onExit,
}: Props) {
  const { t, i18n } = useTranslation();
  const isSpanish = i18n.language.startsWith('es');
  // One namespace per exam kind, so every string differs where the two
  // experiences differ — skipping a module and finishing a course should not
  // read the same.
  const ns = kind === 'test_out' ? 'testOut' : 'trackExam';

  const start = useCallback(
    () =>
      kind === 'test_out'
        ? exams.startTestOut(targetId)
        : exams.startTrackExam(targetId),
    [kind, targetId],
  );

  // The hook carries the *whole* submit response, not just `report`: the
  // certificate and the mastery the sitting moved are part of the result a
  // learner is shown, and threading them separately would mean two sources of
  // truth for one submission.
  const submit = useCallback(async (attemptId: string, answers: Record<string, number>) => {
    const res = await exams.submitTrackExam(attemptId, answers);
    return { report: res, expired: res.expired };
  }, []);

  const exam = useTimedExam<QuestionPublic, TrackExamStartResponse, TrackExamSubmitResponse>({
    start,
    submit,
    errorMessage: t('mockExam.errorGeneric'),
  });

  const current = exam.current;

  // Con el examen en marcha «atrás» no sale (el reloj sigue en el servidor);
  // antes de empezar y con el resultado, sí.
  useBackGuard(() => {
    if (exam.phase === 'running' || exam.phase === 'grading') showToast(t('mockExam.backBlocked'), 'info');
    else onExit?.();
  });

  // ── Intro ─────────────────────────────────────────────────────────────────

  // 46.15 C: el resultado del servidor cierra la sesión (nivel 3), una vez.
  const reduce = useReducedMotion();
  useEffect(() => {
    if (exam.phase === 'result' && exam.report) emitFx({ type: 'session_end' });
  }, [exam.phase, exam.report]);

  if (exam.phase === 'intro' || (exam.phase === 'grading' && !exam.sitting)) {
    return (
      <div className={styles.screen}>
        <h1 className={styles.title}>{t(`${ns}.title`)}</h1>
        <p className={styles.intro}>{t(`${ns}.intro`)}</p>
        <p className={styles.format}>
          {t(`${ns}.format`, {
            count: questionCount,
            minutes: durationMinutes,
            pass: passPct,
          })}
        </p>
        <p className={own.honesty}>
          {kind === 'test_out' ? t('testOut.honesty') : t('trackExam.coverage')}
        </p>
        <p className={own.honesty}>{t('trackExam.unansweredCountsWrong')}</p>
        {exam.error && (
          <p className={styles.error} role="alert">
            {exam.error}
          </p>
        )}
        <button
          className={styles.primary}
          onClick={() => void exam.start()}
          disabled={exam.phase === 'grading'}
        >
          {exam.phase === 'grading' ? t(`${ns}.starting`) : t(`${ns}.start`)}
        </button>
        {onExit && (
          <button className={styles.secondary} onClick={onExit}>
            {t('back')}
          </button>
        )}
      </div>
    );
  }

  // ── Result ────────────────────────────────────────────────────────────────

  if (exam.phase === 'result' && exam.report) {
    const result = exam.report;
    const report = result.report;
    const elapsedMinutes = Math.round(report.elapsed_seconds / 60);
    const masteryCount = Object.keys(result.mastery_updated).length;
    const certificate = result.certificate;

    return (
      <div className={styles.screen}>
        {/* The verdict is a heading, not a colour: pass/fail must survive both
            a screen reader and colour-blindness (red line 6). */}
        <motion.h1
          className={report.passed ? own.verdictPass : own.verdictFail}
          data-fx={reduce ? undefined : 'reveal'}
          initial={reduce ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: DUR.response }}
        >
          {report.passed ? t(`${ns}.passed`) : t(`${ns}.failed`)}
        </motion.h1>

        <p className={styles.score}>
          {t('trackExam.yourScore', { score: report.raw_pct })}
          <span className={own.passMark}>{t('trackExam.passMark', { pass: report.pass_pct })}</span>
        </p>

        {exam.expired && (
          <p className={styles.expired} role="status">
            {t('trackExam.expired')}
          </p>
        )}

        {!report.passed && kind === 'test_out' && (
          <p className={own.honesty}>{t('testOut.failedHelp')}</p>
        )}

        {certificate && <CertificateCard certificate={certificate} />}

        <p className={styles.note}>
          {isSpanish ? report.scoring_note_es : report.scoring_note_en}
        </p>

        <h2 className={styles.subtitle}>{t('trackExam.perSkill')}</h2>
        <p className={styles.caveat}>{t('trackExam.perSkillCaveat')}</p>

        <ul className={styles.domains}>
          {report.per_skill.map(skill => (
            <li key={skill.skill_id} className={styles.domain}>
              <div className={styles.domainHead}>
                <span className={styles.domainName}>
                  {isSpanish ? skill.name_es : skill.name_en}
                </span>
                <span className={styles.domainScore}>
                  {t('mockExam.domainScore', { correct: skill.correct, total: skill.total })}
                </span>
              </div>
              <div
                className={styles.bar}
                role="progressbar"
                aria-valuenow={skill.pct ?? 0}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={isSpanish ? skill.name_es : skill.name_en}
              >
                <div className={styles.barFill} style={{ width: `${skill.pct ?? 0}%` }} />
              </div>
            </li>
          ))}
        </ul>

        {masteryCount > 0 && (
          <p className={own.honesty}>{t('testOut.masteryMoved', { count: masteryCount })}</p>
        )}
        {kind === 'test_out' && report.passed && (
          <p className={own.honesty}>{t('testOut.noCertificate')}</p>
        )}

        <p className={styles.elapsed}>{t('mockExam.elapsed', { minutes: elapsedMinutes })}</p>
        <button className={styles.primary} onClick={() => void exam.start()}>
          {t('trackExam.retry')}
        </button>
        {onExit && (
          <button className={styles.secondary} onClick={onExit}>
            {t('back')}
          </button>
        )}
      </div>
    );
  }

  // ── Running ───────────────────────────────────────────────────────────────

  if (!current) {
    return (
      <div className={styles.screen}>
        <Loading label={t('loading')} shape="card" />
      </div>
    );
  }

  return (
    <div className={styles.screen}>
      <ExamSitting
        title={t(`${ns}.title`)}
        questions={exam.questions}
        index={exam.index}
        onGo={exam.goTo}
        answers={exam.answers}
        onChoose={exam.choose}
        secondsLeft={exam.secondsLeft}
        grading={exam.phase === 'grading'}
        error={exam.error}
        onSubmit={() => void exam.submit()}
      />
    </div>
  );
}
