import { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Player } from '@lottiefiles/react-lottie-player';
import { useAppStore } from '../stores/useAppStore';
import { quiz as quizApi, type GlossaryTerm, type QuestionPublic, type QuizAnswerResponse, type QuizEndResponse } from '../services/api';
import { enqueue } from '../services/offlineQueue';
import { ProgressBar } from '../components/common/ProgressBar';
import { showToast } from '../components/common/Toast';
import { WhyButton } from '../components/quiz/WhyButton';
import { GlossaryText } from '../components/quiz/GlossaryText';
import { TermCard } from '../components/quiz/TermCard';
import { usePyodide } from '../hooks/usePyodide';
import { useGlossary } from '../hooks/useGlossary';
import styles from './QuizScreen.module.css';

const EXEC_TYPES = new Set<QuestionPublic['type']>(['fill_blank_exec', 'fix_bug']);
const TARGET_QUESTIONS = 10;

/** Splits an optional fenced ``` code block out of the question text. */
function parseQuestion(text: string): { prose: string; code: string | null } {
  const m = text.match(/```[a-zA-Z]*\n?([\s\S]*?)```/);
  if (m) {
    const code = m[1].replace(/\n$/, '');
    const prose = text.replace(m[0], '').trim();
    return { prose, code };
  }
  return { prose: text, code: null };
}

export function QuizScreen() {
  const mode = useAppStore((s) => s.quiz.mode);
  const trackId = useAppStore((s) => s.quiz.trackId);
  const skillId = useAppStore((s) => s.quiz.skillId);
  const language = useAppStore((s) => s.user.language);
  const setScreen = useAppStore((s) => s.setScreen);
  const resetQuiz = useAppStore((s) => s.resetQuiz);
  const hydrateFromApi = useAppStore((s) => s.hydrateFromApi);
  const isPremium = useAppStore((s) => s.user.isPremium);
  const { t } = useTranslation();

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState<QuestionPublic | null>(null);
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<QuizAnswerResponse | null>(null);
  const [combo, setCombo] = useState(0);
  const [xpEarned, setXpEarned] = useState(0);
  const [timer, setTimer] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<QuizEndResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [lottieSrc, setLottieSrc] = useState<string | null>(null);

  // Which language this question is *shown* in. Separate from the app language
  // on purpose: peeking at the English wording of one question should not
  // change the whole interface, and it must never touch grading — the answer
  // is an index, and the engine never sees this value.
  const [viewLang, setViewLang] = useState<'es' | 'en'>('es');
  const [pickedTerm, setPickedTerm] = useState<GlossaryTerm | null>(null);
  const glossaryTerms = useGlossary(question?.skill_id);

  // Exec-type state
  const [userInput, setUserInput] = useState('');
  const [runResult, setRunResult] = useState<{ output: string; error: string | null; timedOut: boolean } | null>(null);
  const [execAttempts, setExecAttempts] = useState(0);
  const [runLoading, setRunLoading] = useState(false);
  const [verifyOutput, setVerifyOutput] = useState<string | null>(null);
  const [verifyLoading, setVerifyLoading] = useState(false);

  const questionStart = useRef<number>(Date.now());
  const { status: pyodideStatus, runCode } = usePyodide();

  const isExecType = question != null && EXEC_TYPES.has(question.type);

  // ── Session start ──────────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    quizApi
      .start(mode, trackId ?? undefined, skillId ?? undefined)
      .then((res) => {
        if (cancelled) return;
        setSessionId(res.session_id);
        setQuestion(res.question);
        questionStart.current = Date.now();
        setLoading(false);
        if (!res.question) setError(t('quiz.noQuestions'));
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Error');
        setLoading(false);
      });
    return () => { cancelled = true; };
  }, [mode, trackId, skillId, t]);

  // ── Reset exec state when question changes ─────────────────────────────
  useEffect(() => {
    if (!question) return;
    setUserInput('');
    setRunResult(null);
    setExecAttempts(0);
    setVerifyOutput(null);
    if (question.type === 'fix_bug') {
      const qText = language === 'es' ? question.question_es : question.question_en;
      const { code } = parseQuestion(qText);
      setUserInput(code ?? '');
    }
  }, [question?.id, language]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── MCQ countdown (disabled for exec types) ────────────────────────────
  useEffect(() => {
    if (feedback || summary || loading || !question || isExecType) return;
    if (timer <= 0) { void submitAnswer(null); return; }
    const id = setTimeout(() => setTimer((v) => v - 1), 1000);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timer, feedback, summary, loading, question, isExecType]);

  // ── Reset timer when question changes ──────────────────────────────────
  useEffect(() => {
    setTimer(30);
    // Each question starts in the learner's own language; a peek at the English
    // wording is a decision taken per question, not a mode you fall into.
    setViewLang(language);
    setPickedTerm(null);
  }, [question?.id, language]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Core answer submission ─────────────────────────────────────────────
  const submitAnswer = useCallback(
    async (selectedIndex: number | null, declaredUnknown = false) => {
      if (!sessionId || !question || feedback || submitting) return;
      setSubmitting(true);
      const rt = Date.now() - questionStart.current;
      try {
        const res = await quizApi.answer(sessionId, question.id, selectedIndex, rt, declaredUnknown);
        setFeedback(res);
        setCombo(res.combo);
        setXpEarned((x) => x + res.xp_earned);
        // Admitting ignorance is not a failure, so it gets no failure animation.
        setLottieSrc(
          declaredUnknown
            ? null
            : res.combo >= 3
              ? '/lottie/streak.json'
              : res.correct
                ? '/lottie/correct.json'
                : '/lottie/incorrect.json'
        );
        setTimeout(() => setLottieSrc(null), 1400);
        if (declaredUnknown) {
          showToast(t('quiz.unknownAck'), 'info');
        } else if (res.correct) {
          showToast(`+${res.xp_earned} XP${res.combo >= 3 ? ` · combo ${res.combo}🔥` : ''}`, 'success');
        } else {
          showToast(t('quiz.incorrect'), 'error');
        }
      } catch (e) {
        const isNetworkError = !navigator.onLine || (e instanceof TypeError);
        if (isNetworkError && sessionId && question) {
          await enqueue({
            id: `${sessionId}_${question.id}_${Date.now()}`,
            sessionId,
            questionId: question.id,
            selectedIndex,
            responseTimeMs: rt,
            timestamp: Date.now(),
          });
          setFeedback({
            correct: false,
            correct_index: null,
            explanation_es: '(guardado sin conexión)',
            explanation_en: '(saved offline)',
            source: null,
            grade: 0,
            xp_earned: 0,
            combo,
            user_elo: 0,
            next_review: null,
            skill_mastery: {},
            session_accuracy: 0,
            next_question: null,
          });
          showToast(t('quiz.savedOffline'), 'info');
        } else {
          showToast(e instanceof Error ? e.message : 'Error', 'error');
        }
      } finally {
        setSubmitting(false);
      }
    },
    [sessionId, question, feedback, submitting, t, combo]
  );

  // ── MCQ answer handler ─────────────────────────────────────────────────
  const handleAnswer = useCallback(
    (choice: number | null) => {
      setSelected(choice);
      return submitAnswer(choice);
    },
    [submitAnswer]
  );

  // Saying "I don't know" is a real answer, not a skip: it tells the model
  // something a guess never could, so it goes through the same path and shows
  // the same explanation.
  const handleUnknown = useCallback(() => {
    setSelected(null);
    return submitAnswer(null, true);
  }, [submitAnswer]);

  // ── Exec: run code in Pyodide ──────────────────────────────────────────
  const handleRun = useCallback(async () => {
    if (!question || runLoading || feedback) return;

    const qText = language === 'es' ? question.question_es : question.question_en;
    const { code } = parseQuestion(qText);

    let codeToRun: string;
    if (question.type === 'fill_blank_exec') {
      codeToRun = (code ?? '').replace('___', userInput);
    } else {
      codeToRun = userInput;
    }

    setRunLoading(true);
    const result = await runCode(codeToRun, 5000);
    setRunResult(result);

    const expected = (
      (language === 'es' ? question.correct_answer_es : question.correct_answer_en) ?? ''
    ).trim();

    const isCorrect =
      !result.error && !result.timedOut && result.output.trim() === expected;

    const newAttempts = execAttempts + 1;
    setExecAttempts(newAttempts);

    if (isCorrect || newAttempts >= 3) {
      await submitAnswer(isCorrect ? 1 : 0);
    }

    setRunLoading(false);
  }, [question, runLoading, feedback, language, userInput, runCode, execAttempts, submitAnswer]);

  // ── code_output: verify with Pyodide after answering ──────────────────
  const handleVerify = useCallback(async () => {
    if (!question || verifyLoading) return;
    const qText = language === 'es' ? question.question_es : question.question_en;
    const { code } = parseQuestion(qText);
    if (!code) return;
    setVerifyLoading(true);
    const result = await runCode(code, 5000);
    setVerifyOutput(result.timedOut ? '⏱ Timeout' : result.error ? `Error: ${result.error}` : result.output);
    setVerifyLoading(false);
  }, [question, verifyLoading, language, runCode]);

  // ── Next question ──────────────────────────────────────────────────────
  const handleNext = useCallback(async () => {
    if (!feedback || !sessionId) return;
    const next = feedback.next_question;
    if (next && index + 1 < TARGET_QUESTIONS) {
      setQuestion(next);
      setIndex((i) => i + 1);
      setSelected(null);
      setFeedback(null);
      setTimer(30);
      questionStart.current = Date.now();
    } else {
      try {
        const end = await quizApi.end(sessionId);
        setSummary(end);
        void hydrateFromApi();
      } catch {
        setSummary({ total_questions: index + 1, correct: 0, accuracy: 0, max_combo: combo, xp_earned: xpEarned, duration_seconds: 0 });
      }
    }
  }, [feedback, sessionId, index, combo, xpEarned, hydrateFromApi]);

  const handleClose = useCallback(() => {
    resetQuiz();
    setScreen('home');
  }, [resetQuiz, setScreen]);

  const handleUpgrade = useCallback(() => {
    setScreen('profile');
  }, [setScreen]);

  // ── Early returns ──────────────────────────────────────────────────────
  if (loading) return <QuizLoader />;
  if (error) return <QuizError message={error} onClose={handleClose} />;
  if (summary) return <SessionSummary summary={summary} onClose={handleClose} />;
  if (!question) return <QuizError message={t('quiz.noQuestions')} onClose={handleClose} />;

  const qText = viewLang === 'es' ? question.question_es : question.question_en;
  const options = (viewLang === 'es' ? question.options_es : question.options_en) ?? [];
  const { prose, code } = parseQuestion(qText);
  const answered = feedback !== null;
  const otherLang: 'es' | 'en' = viewLang === 'es' ? 'en' : 'es';

  const diffColor =
    question.difficulty_tier === 'hard' || question.difficulty_tier === 'expert'
      ? 'var(--le-red)'
      : question.difficulty_tier === 'medium'
        ? 'var(--le-orange)'
        : 'var(--le-green)';

  // ── Shared header + stats bar ──────────────────────────────────────────
  const header = (
    <div className={styles.header}>
      <button className={styles.closeBtn} onClick={handleClose} aria-label={t('quiz.close')}>
        <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
        </svg>
      </button>
      <div className={styles.progressWrap}>
        <ProgressBar value={index + 1} max={TARGET_QUESTIONS} color="var(--le-brand)" height={10} />
        <span className={styles.progressLabel}>{index + 1}/{TARGET_QUESTIONS}</span>
      </div>
      {!isExecType && (
        <div className={styles.timerWrap}>
          <div className={`${styles.timer} ${timer <= 5 ? styles.timerDanger : ''}`}>{timer}</div>
        </div>
      )}
    </div>
  );

  const statsBar = (
    <div className={styles.statsBar}>
      <div className={styles.combo}>
        {combo > 0 && (<><span className={styles.comboFire}>🔥</span><span className={styles.comboCount}>{combo}</span></>)}
      </div>
      <div className={styles.xpBadge}>⚡ {xpEarned} XP</div>
      <div className={styles.diffBadge} style={{ color: diffColor, borderColor: diffColor }}>
        {t(`quiz.diff.${question.difficulty_tier}`)}
      </div>
    </div>
  );

  const questionCard = (
    <div className={styles.questionCard}>
      <div className={styles.questionTop}>
        <span className={styles.topic}>{t(`quiz.mode.${mode}`) ?? mode}</span>
        <button
          type="button"
          className={styles.langToggle}
          onClick={() => { setViewLang(otherLang); setPickedTerm(null); }}
          aria-label={t('quiz.showIn', { lang: t(`quiz.lang.${otherLang}`) })}
          title={t('quiz.showIn', { lang: t(`quiz.lang.${otherLang}`) })}
        >
          {otherLang.toUpperCase()}
        </button>
      </div>
      <h2 className={styles.questionText}>
        <GlossaryText text={prose} terms={glossaryTerms} lang={viewLang} onPick={setPickedTerm} />
      </h2>
      {code && !isExecType && <pre className={styles.codeBlock}><code>{code}</code></pre>}
      {pickedTerm && (
        <TermCard term={pickedTerm} lang={viewLang} onClose={() => setPickedTerm(null)} />
      )}
    </div>
  );

  const feedbackPanel = answered && feedback && (
    <div className={styles.explanation}>
      <div className={styles.explanationHeader}>
        {feedback.correct ? `🎯 ${t('quiz.correct')}` : `💡 ${t('quiz.explanation')}`}
      </div>
      <p className={styles.explanationText}>
        <GlossaryText
          text={viewLang === 'es' ? feedback.explanation_es : feedback.explanation_en}
          terms={glossaryTerms}
          lang={viewLang}
          onPick={setPickedTerm}
        />
      </p>
      {feedback.source && (
        <p className={styles.sourceBadge}>📚 {t('quiz.source')}: {feedback.source}</p>
      )}

      <WhyButton questionId={question.id} isPremium={isPremium} onUpgrade={handleUpgrade} />

      <button className={styles.btnNext} onClick={handleNext}>
        {index + 1 >= TARGET_QUESTIONS || !feedback.next_question ? t('quiz.seeResults') : t('quiz.next')}
      </button>
    </div>
  );

  // ── Exec question render ───────────────────────────────────────────────
  if (isExecType) {
    const expected = (
      (language === 'es' ? question.correct_answer_es : question.correct_answer_en) ?? ''
    ).trim();

    const attemptsLeft = 3 - execAttempts;
    const lastCorrect =
      runResult &&
      !runResult.error &&
      !runResult.timedOut &&
      runResult.output.trim() === expected;

    const engineLabel =
      pyodideStatus === 'loading'
        ? `⚙ ${t('quiz.engineLoading')}`
        : pyodideStatus === 'error'
          ? `⚠ ${t('quiz.engineError')}`
          : null;

    return (
      <div className={styles.screen}>
        {header}
        {statsBar}
        {questionCard}

        <div className={styles.execArea}>
          {question.type === 'fill_blank_exec' && code && (
            <>
              <pre className={styles.codeBlock}>
                <code>{code.replace('___', `[${t('quiz.yourAnswer')}]`)}</code>
              </pre>
              <input
                className={styles.blankInput}
                type="text"
                placeholder={t('quiz.fillBlankPlaceholder')}
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                disabled={answered}
                onKeyDown={(e) => { if (e.key === 'Enter' && !answered && !runLoading) void handleRun(); }}
              />
            </>
          )}

          {question.type === 'fix_bug' && (
            <textarea
              className={styles.codeEditor}
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              disabled={answered}
              spellCheck={false}
              rows={Math.max(4, (userInput.match(/\n/g) ?? []).length + 2)}
            />
          )}

          {!answered && (
            <button
              className={styles.btnRun}
              onClick={() => void handleRun()}
              disabled={runLoading || answered || pyodideStatus !== 'ready'}
            >
              {runLoading
                ? `⏳ ${t('quiz.executing')}`
                : engineLabel ?? `▶ ${t('quiz.runCode')}${execAttempts > 0 ? ` (${attemptsLeft} ${t('quiz.attemptsLeft')})` : ''}`}
            </button>
          )}

          {runResult && (
            <div className={`${styles.outputBox} ${lastCorrect ? styles.outputCorrect : styles.outputWrong}`}>
              <span className={styles.outputLabel}>
                {lastCorrect
                  ? `✅ ${t('quiz.outputCorrect')}`
                  : runResult.timedOut
                    ? `⏱ ${t('quiz.timeout')}`
                    : runResult.error
                      ? `❌ ${t('quiz.outputError')}`
                      : `❌ ${t('quiz.outputWrong')}`}
              </span>
              <pre className={styles.outputPre}>
                {runResult.timedOut
                  ? t('quiz.timeoutMsg')
                  : runResult.error
                    ? runResult.error
                    : runResult.output || t('quiz.noOutput')}
              </pre>
              {!lastCorrect && !runResult.timedOut && !runResult.error && expected && (
                <p className={styles.expectedHint}>
                  {t('quiz.expected')}: <code>{expected}</code>
                </p>
              )}
            </div>
          )}
        </div>

        {feedbackPanel}
      </div>
    );
  }

  // ── Standard MCQ render ────────────────────────────────────────────────
  return (
    <div className={styles.screen}>
      {header}
      {statsBar}
      {questionCard}

      <div className={styles.options}>
        {options.map((opt, i) => {
          let cls = styles.option;
          if (answered && feedback) {
            if (i === feedback.correct_index) cls += ` ${styles.correct}`;
            else if (i === selected) cls += ` ${styles.wrong}`;
            else cls += ` ${styles.dimmed}`;
          } else if (i === selected) {
            cls += ` ${styles.selected}`;
          }
          return (
            <button key={i} className={cls} onClick={() => handleAnswer(i)} disabled={answered || submitting}>
              <span className={styles.optionLetter}>{String.fromCharCode(65 + i)}</span>
              <span className={styles.optionText}>{opt}</span>
              {answered && feedback && i === feedback.correct_index && <span className={styles.optionIcon}>✓</span>}
              {answered && i === selected && feedback && i !== feedback.correct_index && <span className={styles.optionIcon}>✗</span>}
            </button>
          );
        })}
      </div>

      {!answered && (
        <button
          type="button"
          className={styles.unknownBtn}
          onClick={handleUnknown}
          disabled={submitting}
        >
          {t('quiz.dontKnow')}
        </button>
      )}

      {answered && question.type === 'code_output' && code && (
        <div className={styles.verifyArea}>
          {verifyOutput != null ? (
            <div className={styles.outputBox}>
              <span className={styles.outputLabel}>▶ {t('quiz.actualOutput')}</span>
              <pre className={styles.outputPre}>{verifyOutput}</pre>
            </div>
          ) : (
            <button
              className={styles.btnVerify}
              onClick={() => void handleVerify()}
              disabled={verifyLoading || pyodideStatus !== 'ready'}
            >
              {verifyLoading
                ? `⏳ ${t('quiz.executing')}`
                : pyodideStatus === 'loading'
                  ? `⚙ ${t('quiz.engineLoading')}`
                  : `▶ ${t('quiz.runToVerify')}`}
            </button>
          )}
        </div>
      )}

      {lottieSrc && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          pointerEvents: 'none', zIndex: 999,
        }}>
          <Player src={lottieSrc} autoplay loop={false} style={{ width: 160, height: 160 }} />
        </div>
      )}

      {feedbackPanel}
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────

function QuizLoader() {
  const { t } = useTranslation();
  return (
    <div className={styles.summary}>
      <div className={styles.summaryGrade} style={{ borderColor: 'var(--le-brand)', color: 'var(--le-brand)', animation: 'pulse 1.2s ease-in-out infinite' }}>◐</div>
      <p className={styles.summaryAccuracy}>{t('loading')}</p>
    </div>
  );
}

function QuizError({ message, onClose }: { message: string; onClose: () => void }) {
  const { t } = useTranslation();
  return (
    <div className={styles.summary}>
      <span style={{ fontSize: '3rem' }}>🤔</span>
      <h1 className={styles.summaryTitle}>{t('quiz.noQuestionsAvail')}</h1>
      <p className={styles.summaryAccuracy}>{message}</p>
      <button className={styles.btnStudy} onClick={onClose} style={{ marginTop: 'var(--le-space-xl)' }}>{t('back')}</button>
    </div>
  );
}

function SessionSummary({ summary, onClose }: { summary: QuizEndResponse; onClose: () => void }) {
  const { t } = useTranslation();
  const accuracy = Math.round(summary.accuracy * 100);
  const grade = accuracy >= 90 ? 'S' : accuracy >= 80 ? 'A' : accuracy >= 70 ? 'B' : accuracy >= 60 ? 'C' : 'F';
  const gradeColor = grade === 'S' ? 'var(--le-gold)' : grade === 'A' ? 'var(--le-green)' : grade === 'B' ? 'var(--le-brand)' : grade === 'C' ? 'var(--le-orange)' : 'var(--le-red)';
  return (
    <div className={styles.summary}>
      <div className={styles.summaryGrade} style={{ color: gradeColor, borderColor: gradeColor }}>{grade}</div>
      <h1 className={styles.summaryTitle}>{accuracy >= 80 ? t('quiz.excellent') : accuracy >= 60 ? t('quiz.goodJob') : t('quiz.keepGoing')}</h1>
      <p className={styles.summaryAccuracy}>{accuracy}% {t('quiz.accuracyLabel')}</p>
      <div className={styles.summaryStats}>
        <div className={styles.summaryStat}>
          <span className={styles.summaryStatVal}>{summary.correct}/{summary.total_questions}</span>
          <span className={styles.summaryStatLabel}>{t('quiz.correctLabel')}</span>
        </div>
        <div className={styles.summaryStat}>
          <span className={styles.summaryStatVal}>🔥 {summary.max_combo}</span>
          <span className={styles.summaryStatLabel}>{t('quiz.maxCombo')}</span>
        </div>
        <div className={styles.summaryStat}>
          <span className={styles.summaryStatVal}>⚡ {summary.xp_earned}</span>
          <span className={styles.summaryStatLabel}>{t('quiz.xpEarned')}</span>
        </div>
      </div>
      <button className={styles.btnStudy} onClick={onClose} style={{ marginTop: 'var(--le-space-xl)' }}>{t('quiz.continue')}</button>
    </div>
  );
}
