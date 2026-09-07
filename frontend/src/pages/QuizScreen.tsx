import { useState, useEffect, useCallback, useRef } from 'react';
import { useAppStore } from '../stores/useAppStore';
import { quiz as quizApi, tutor as tutorApi, type QuestionPublic, type QuizAnswerResponse, type QuizEndResponse } from '../services/api';
import { ProgressBar } from '../components/common/ProgressBar';
import { showToast } from '../components/common/Toast';
import { usePyodide } from '../hooks/usePyodide';
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
  const [tutorText, setTutorText] = useState<string | null>(null);
  const [tutorLoading, setTutorLoading] = useState(false);

  // Exec-type state
  const [userInput, setUserInput] = useState('');
  const [runResult, setRunResult] = useState<{ output: string; error: string | null; timedOut: boolean } | null>(null);
  const [execAttempts, setExecAttempts] = useState(0);
  const [runLoading, setRunLoading] = useState(false);
  // For code_output: show actual Pyodide output after MCQ answer
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
        if (!res.question) setError(t(language).noQuestions);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Error');
        setLoading(false);
      });
    return () => { cancelled = true; };
  }, [mode, trackId, skillId, language]);

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
  }, [question?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Core answer submission (shared by MCQ and exec paths) ──────────────
  const submitAnswer = useCallback(
    async (selectedIndex: number | null) => {
      if (!sessionId || !question || feedback || submitting) return;
      setSubmitting(true);
      const rt = Date.now() - questionStart.current;
      try {
        const res = await quizApi.answer(sessionId, question.id, selectedIndex, rt);
        setFeedback(res);
        setCombo(res.combo);
        setXpEarned((x) => x + res.xp_earned);
        if (res.correct) {
          showToast(`+${res.xp_earned} XP${res.combo >= 3 ? ` · combo ${res.combo}🔥` : ''}`, 'success');
        } else {
          showToast(t(language).incorrect, 'error');
        }
      } catch (e) {
        showToast(e instanceof Error ? e.message : 'Error', 'error');
      } finally {
        setSubmitting(false);
      }
    },
    [sessionId, question, feedback, submitting, language]
  );

  // ── MCQ answer handler ─────────────────────────────────────────────────
  const handleAnswer = useCallback(
    (choice: number | null) => {
      setSelected(choice);
      return submitAnswer(choice);
    },
    [submitAnswer]
  );

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
      setTutorText(null);
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

  const handleTutor = useCallback(async () => {
    if (!question || tutorLoading) return;
    setTutorLoading(true);
    try {
      const res = await tutorApi.explain(question.id);
      setTutorText(res.explanation || t(language).tutorEmpty);
    } catch {
      setTutorText(t(language).tutorError);
    } finally {
      setTutorLoading(false);
    }
  }, [question, tutorLoading, language]);

  // ── Early returns ──────────────────────────────────────────────────────
  if (loading) return <QuizLoader />;
  if (error) return <QuizError message={error} onClose={handleClose} />;
  if (summary) return <SessionSummary summary={summary} onClose={handleClose} language={language} />;
  if (!question) return <QuizError message={t(language).noQuestions} onClose={handleClose} />;

  const qText = language === 'es' ? question.question_es : question.question_en;
  const options = (language === 'es' ? question.options_es : question.options_en) ?? [];
  const { prose, code } = parseQuestion(qText);
  const answered = feedback !== null;
  const L = t(language);

  const diffColor =
    question.difficulty_tier === 'hard' || question.difficulty_tier === 'expert'
      ? 'var(--le-red)'
      : question.difficulty_tier === 'medium'
        ? 'var(--le-orange)'
        : 'var(--le-green)';

  // ── Shared header + stats bar ──────────────────────────────────────────
  const header = (
    <div className={styles.header}>
      <button className={styles.closeBtn} onClick={handleClose} aria-label={L.close}>
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
        {L.diff[question.difficulty_tier]}
      </div>
    </div>
  );

  const questionCard = (
    <div className={styles.questionCard}>
      <span className={styles.topic}>{L.mode[mode] ?? mode}</span>
      <h2 className={styles.questionText}>{prose}</h2>
      {code && !isExecType && <pre className={styles.codeBlock}><code>{code}</code></pre>}
    </div>
  );

  const feedbackPanel = answered && feedback && (
    <div className={styles.explanation}>
      <div className={styles.explanationHeader}>
        {feedback.correct ? `🎯 ${L.correct}` : `💡 ${L.explanation}`}
      </div>
      <p className={styles.explanationText}>
        {language === 'es' ? feedback.explanation_es : feedback.explanation_en}
      </p>
      {feedback.source && (
        <p className={styles.sourceBadge}>📚 {L.source}: {feedback.source}</p>
      )}

      {tutorText ? (
        <div className={styles.tutorBox}>
          <span className={styles.tutorLabel}>🧠 {L.tutor}</span>
          <p className={styles.tutorText}>{tutorText}</p>
        </div>
      ) : (
        <button className={styles.btnTutor} onClick={handleTutor} disabled={tutorLoading}>
          {tutorLoading ? L.tutorLoading : `🧠 ${L.explainThis}`}
        </button>
      )}

      <button className={styles.btnNext} onClick={handleNext}>
        {index + 1 >= TARGET_QUESTIONS || !feedback.next_question ? L.seeResults : L.next}
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
        ? '⚙ Cargando motor Python…'
        : pyodideStatus === 'error'
          ? '⚠ Motor no disponible'
          : null;

    return (
      <div className={styles.screen}>
        {header}
        {statsBar}
        {questionCard}

        {/* Code editor area */}
        <div className={styles.execArea}>
          {question.type === 'fill_blank_exec' && code && (
            <>
              <pre className={styles.codeBlock}>
                <code>{code.replace('___', `[${L.yourAnswer}]`)}</code>
              </pre>
              <input
                className={styles.blankInput}
                type="text"
                placeholder={L.fillBlankPlaceholder}
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
                ? '⏳ Ejecutando…'
                : engineLabel ?? `▶ ${L.runCode}${execAttempts > 0 ? ` (${attemptsLeft} ${L.attemptsLeft})` : ''}`}
            </button>
          )}

          {runResult && (
            <div className={`${styles.outputBox} ${lastCorrect ? styles.outputCorrect : styles.outputWrong}`}>
              <span className={styles.outputLabel}>
                {lastCorrect ? `✅ ${L.outputCorrect}` : runResult.timedOut ? `⏱ ${L.timeout}` : runResult.error ? `❌ ${L.outputError}` : `❌ ${L.outputWrong}`}
              </span>
              <pre className={styles.outputPre}>
                {runResult.timedOut
                  ? L.timeoutMsg
                  : runResult.error
                    ? runResult.error
                    : runResult.output || '(sin salida)'}
              </pre>
              {!lastCorrect && !runResult.timedOut && !runResult.error && expected && (
                <p className={styles.expectedHint}>
                  {L.expected}: <code>{expected}</code>
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

      {/* code_output: "run it yourself" verification button after answering */}
      {answered && question.type === 'code_output' && code && (
        <div className={styles.verifyArea}>
          {verifyOutput != null ? (
            <div className={styles.outputBox}>
              <span className={styles.outputLabel}>▶ {L.actualOutput}</span>
              <pre className={styles.outputPre}>{verifyOutput}</pre>
            </div>
          ) : (
            <button
              className={styles.btnVerify}
              onClick={() => void handleVerify()}
              disabled={verifyLoading || pyodideStatus !== 'ready'}
            >
              {verifyLoading
                ? '⏳ Ejecutando…'
                : pyodideStatus === 'loading'
                  ? '⚙ Cargando motor…'
                  : `▶ ${L.runToVerify}`}
            </button>
          )}
        </div>
      )}

      {feedbackPanel}
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────

function QuizLoader() {
  return (
    <div className={styles.summary}>
      <div className={styles.summaryGrade} style={{ borderColor: 'var(--le-brand)', color: 'var(--le-brand)', animation: 'pulse 1.2s ease-in-out infinite' }}>◐</div>
      <p className={styles.summaryAccuracy}>Cargando…</p>
    </div>
  );
}

function QuizError({ message, onClose }: { message: string; onClose: () => void }) {
  return (
    <div className={styles.summary}>
      <span style={{ fontSize: '3rem' }}>🤔</span>
      <h1 className={styles.summaryTitle}>Sin preguntas disponibles</h1>
      <p className={styles.summaryAccuracy}>{message}</p>
      <button className={styles.btnStudy} onClick={onClose} style={{ marginTop: 'var(--le-space-xl)' }}>VOLVER</button>
    </div>
  );
}

function SessionSummary({ summary, onClose, language }: { summary: QuizEndResponse; onClose: () => void; language: 'es' | 'en' }) {
  const accuracy = Math.round(summary.accuracy * 100);
  const grade = accuracy >= 90 ? 'S' : accuracy >= 80 ? 'A' : accuracy >= 70 ? 'B' : accuracy >= 60 ? 'C' : 'F';
  const gradeColor = grade === 'S' ? 'var(--le-gold)' : grade === 'A' ? 'var(--le-green)' : grade === 'B' ? 'var(--le-brand)' : grade === 'C' ? 'var(--le-orange)' : 'var(--le-red)';
  const L = t(language);
  return (
    <div className={styles.summary}>
      <div className={styles.summaryGrade} style={{ color: gradeColor, borderColor: gradeColor }}>{grade}</div>
      <h1 className={styles.summaryTitle}>{accuracy >= 80 ? L.excellent : accuracy >= 60 ? L.goodJob : L.keepGoing}</h1>
      <p className={styles.summaryAccuracy}>{accuracy}% {L.accuracyLabel}</p>
      <div className={styles.summaryStats}>
        <div className={styles.summaryStat}>
          <span className={styles.summaryStatVal}>{summary.correct}/{summary.total_questions}</span>
          <span className={styles.summaryStatLabel}>{L.correctLabel}</span>
        </div>
        <div className={styles.summaryStat}>
          <span className={styles.summaryStatVal}>🔥 {summary.max_combo}</span>
          <span className={styles.summaryStatLabel}>{L.maxCombo}</span>
        </div>
        <div className={styles.summaryStat}>
          <span className={styles.summaryStatVal}>⚡ {summary.xp_earned}</span>
          <span className={styles.summaryStatLabel}>{L.xpEarned}</span>
        </div>
      </div>
      <button className={styles.btnStudy} onClick={onClose} style={{ marginTop: 'var(--le-space-xl)' }}>{L.continue}</button>
    </div>
  );
}

// ── i18n ───────────────────────────────────────────────────────────────────

function t(lang: 'es' | 'en') {
  const es = {
    close: 'Cerrar', incorrect: 'Incorrecto', correct: '¡Correcto!', explanation: 'Explicación',
    next: 'SIGUIENTE', seeResults: 'VER RESULTADOS', noQuestions: 'No hay preguntas para este modo todavía.',
    excellent: '¡Excelente!', goodJob: '¡Buen trabajo!', keepGoing: '¡Sigue practicando!',
    accuracyLabel: 'de precisión', correctLabel: 'Correctas', maxCombo: 'Max Combo', xpEarned: 'XP Ganados', continue: 'CONTINUAR',
    explainThis: 'Explícame esto', tutor: 'Tutor Whetzy', tutorLoading: 'Pensando…', source: 'Fuente',
    tutorEmpty: 'No pude generar una explicación esta vez.', tutorError: 'El tutor no está disponible ahora.',
    diff: { easy: 'Fácil', medium: 'Media', hard: 'Difícil', expert: 'Experto' } as Record<string, string>,
    mode: { study: 'Estudio', review: 'Repaso', placement: 'Nivelación', exam: 'Examen' } as Record<string, string>,
    // Exec types
    runCode: 'Ejecutar código',
    attemptsLeft: 'intentos restantes',
    yourAnswer: 'tu respuesta',
    fillBlankPlaceholder: 'Escribe tu respuesta aquí…',
    outputCorrect: '¡Correcto! Salida esperada',
    outputWrong: 'Salida incorrecta',
    outputError: 'Error de ejecución',
    timeout: 'Tiempo agotado',
    timeoutMsg: 'El código tardó más de 5 segundos.',
    expected: 'Esperado',
    actualOutput: 'Salida real',
    runToVerify: 'Ejecutar para verificar',
  };
  const en: typeof es = {
    close: 'Close', incorrect: 'Incorrect', correct: 'Correct!', explanation: 'Explanation',
    next: 'NEXT', seeResults: 'SEE RESULTS', noQuestions: 'No questions for this mode yet.',
    excellent: 'Excellent!', goodJob: 'Good job!', keepGoing: 'Keep practicing!',
    accuracyLabel: 'accuracy', correctLabel: 'Correct', maxCombo: 'Max Combo', xpEarned: 'XP Earned', continue: 'CONTINUE',
    explainThis: 'Explain this', tutor: 'Whetzy Tutor', tutorLoading: 'Thinking…', source: 'Source',
    tutorEmpty: "I couldn't generate an explanation this time.", tutorError: 'The tutor is unavailable right now.',
    diff: { easy: 'Easy', medium: 'Medium', hard: 'Hard', expert: 'Expert' } as Record<string, string>,
    mode: { study: 'Study', review: 'Review', placement: 'Placement', exam: 'Exam' } as Record<string, string>,
    // Exec types
    runCode: 'Run code',
    attemptsLeft: 'attempts left',
    yourAnswer: 'your answer',
    fillBlankPlaceholder: 'Type your answer here…',
    outputCorrect: 'Correct! Expected output',
    outputWrong: 'Wrong output',
    outputError: 'Runtime error',
    timeout: 'Timed out',
    timeoutMsg: 'Code took more than 5 seconds.',
    expected: 'Expected',
    actualOutput: 'Actual output',
    runToVerify: 'Run to verify',
  };
  return lang === 'es' ? es : en;
}
