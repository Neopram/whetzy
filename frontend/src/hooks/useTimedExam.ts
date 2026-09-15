/**
 * useTimedExam — the machinery a timed sitting needs, independent of which
 * exam it is (17.2).
 *
 * `MockExamScreen` (10.3) already got all of this right, and the temptation was
 * to copy it into the track-exam screen. Two copies of a countdown that
 * auto-submits is two places for the deadline to drift apart, and the clock is
 * the one part of an exam that cannot be a bit wrong.
 *
 * What it does NOT do is render anything, because that is where the two exams
 * genuinely differ: a certification mock reports per domain and refuses to
 * declare a pass, a track final reports per skill and issues a certificate.
 *
 * `MockExamScreen` is deliberately left untouched for now. Rewiring a working,
 * unbroken screen belongs with a test net and a look at it in a browser, and
 * the session that wrote this could do neither (see the ledger). The tests that
 * come with this hook are what will make that swap safe later.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

export type ExamPhase = 'intro' | 'running' | 'grading' | 'result';

/** The shape any exam's start response has to provide to drive a sitting. */
export interface TimedExamSitting<TQuestion> {
  attempt_id: string;
  expires_at: string;
  questions: TQuestion[];
}

export interface TimedExamSubmission<TReport> {
  report: TReport;
  expired: boolean;
}

interface Options<TQuestion, TSitting extends TimedExamSitting<TQuestion>, TReport> {
  start: () => Promise<TSitting>;
  submit: (attemptId: string, answers: Record<string, number>) => Promise<TimedExamSubmission<TReport>>;
  /** Shown when either call fails. The caller owns the wording and the language. */
  errorMessage: string;
}

export function useTimedExam<TQuestion extends { id: string }, TSitting extends TimedExamSitting<TQuestion>, TReport>(
  { start: startFn, submit: submitFn, errorMessage }: Options<TQuestion, TSitting, TReport>,
) {
  const [phase, setPhase] = useState<ExamPhase>('intro');
  const [sitting, setSitting] = useState<TSitting | null>(null);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [report, setReport] = useState<TReport | null>(null);
  const [expired, setExpired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);

  // Guards the auto-submit so a re-render at the deadline cannot fire it twice.
  const submittingRef = useRef(false);
  // The countdown effect closes over `answers`; without a ref, the interval
  // captured at mount would submit the answer set as it was a minute ago.
  const answersRef = useRef(answers);
  answersRef.current = answers;

  const questions = useMemo(() => sitting?.questions ?? [], [sitting]);
  const current = questions[index];
  const unanswered = questions.length - Object.keys(answers).length;

  const submit = useCallback(async () => {
    if (!sitting || submittingRef.current) return;
    submittingRef.current = true;
    setPhase('grading');
    try {
      const res = await submitFn(sitting.attempt_id, answersRef.current);
      setReport(res.report);
      setExpired(res.expired);
      setPhase('result');
    } catch {
      // Put them back in the exam rather than losing the answers.
      submittingRef.current = false;
      setPhase('running');
      setError(errorMessage);
    }
  }, [sitting, submitFn, errorMessage]);

  // The countdown is derived from the server's deadline on every tick rather
  // than decremented locally: a background tab throttles timers, and a clock
  // that drifts would show time the learner does not actually have.
  useEffect(() => {
    if (phase !== 'running' || !sitting) return;
    const deadline = new Date(sitting.expires_at).getTime();
    const tick = () => {
      const left = Math.round((deadline - Date.now()) / 1000);
      setSecondsLeft(left);
      if (left <= 0) void submit();
    };
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [phase, sitting, submit]);

  const start = useCallback(async () => {
    setError(null);
    setPhase('grading');
    try {
      const res = await startFn();
      setSitting(res);
      setReport(null);
      setExpired(false);
      setAnswers({});
      setIndex(0);
      submittingRef.current = false;
      setPhase('running');
    } catch {
      setPhase('intro');
      setError(errorMessage);
    }
  }, [startFn, errorMessage]);

  const choose = useCallback((questionId: string, option: number) => {
    setAnswers(prev => ({ ...prev, [questionId]: option }));
  }, []);

  const goPrevious = useCallback(() => setIndex(i => Math.max(0, i - 1)), []);
  const goNext = useCallback(() => setIndex(i => i + 1), []);

  return {
    phase,
    sitting,
    questions,
    current,
    index,
    answers,
    unanswered,
    report,
    expired,
    error,
    secondsLeft,
    start,
    submit,
    choose,
    goPrevious,
    goNext,
    isLast: index >= questions.length - 1,
  };
}

/** mm:ss, never negative — a clock that reads -00:03 is worse than one at zero. */
export function formatClock(totalSeconds: number): string {
  const safe = Math.max(0, totalSeconds);
  const minutes = Math.floor(safe / 60);
  const seconds = safe % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}
