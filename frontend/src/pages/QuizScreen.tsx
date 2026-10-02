import { useState, useEffect, useCallback, useLayoutEffect, useRef, lazy, Suspense } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Player } from '@lottiefiles/react-lottie-player';
import { useAppStore } from '../stores/useAppStore';
import { quiz as quizApi, progress as progressApi, isQuotaError, type GlossaryTerm, type QuestionPublic, type QuizAnswerResponse, type QuizEndResponse, type SelectionReason, type SkillMasteryDetail, type AnswerEvidence } from '../services/api';
import { enqueue } from '../services/offlineQueue';
import { ProgressBar } from '../components/common/ProgressBar';
import { showToast } from '../components/common/Toast';
import { WhyButton } from '../components/quiz/WhyButton';
import { GlossaryText } from '../components/quiz/GlossaryText';
import { TermCard } from '../components/quiz/TermCard';
import { SourceLine } from '../components/quiz/SourceLine';
import { ReportQuestion } from '../components/quiz/ReportQuestion';
import { useRuntime, runtimeForQuestion } from '../hooks/useRuntime';
import { useGlossary } from '../hooks/useGlossary';
import { parseQuestion } from '../lib/question';
import styles from './QuizScreen.module.css';

// Monaco is ~2 MB — lazy-load so the initial bundle stays small.
const MonacoCodeEditor = lazy(() =>
  import('../components/quiz/MonacoCodeEditor').then((m) => ({ default: m.MonacoCodeEditor }))
);

const EXEC_TYPES = new Set<QuestionPublic['type']>(['fill_blank_exec', 'fix_bug', 'fill_blank', 'sql_exec', 'js_exec']);
const TARGET_QUESTIONS = 10;


/**
 * `code_es`/`code_en` carry the runnable template for question types like
 * `sql_exec` that don't embed a fenced ``` block in the prose (unlike
 * `fill_blank_exec`/`fix_bug`, which do). Prefer those explicit fields when
 * present, falling back to the fenced-block parse otherwise.
 */
function resolveCode(
  question: QuestionPublic,
  text: string,
  lang: 'es' | 'en'
): { prose: string; code: string | null } {
  const explicit = lang === 'es' ? question.code_es : question.code_en;
  if (explicit) return { prose: text, code: explicit };
  return parseQuestion(text);
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
  const aiExplanations = useAppStore((s) => s.aiExplanations);
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
  // Dominio de la skill que se esta practicando, tal y como lo devuelve el
  // motor BKT al corregir. Empieza en null a proposito: hasta la primera
  // respuesta no hay medicion, y una barra a medias inventada es peor que
  // ninguna barra.
  const [mastery, setMastery] = useState<number | null>(null);
  const [selectionReason, setSelectionReason] = useState<SelectionReason | null>(null);
  // Dominio de cada habilidad al empezar, para enseñar al final cuánto se movió
  // (antes → después). /quiz/end no lo devuelve; se lee de /progress/skills.
  const [skillsBefore, setSkillsBefore] = useState<Map<string, SkillMasteryDetail> | null>(null);
  const practiced = useRef<Set<string>>(new Set());
  const [confirmExit, setConfirmExit] = useState(false);

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
  const runtimeType = runtimeForQuestion(question?.type);
  const { status: runtimeStatus, runCode } = useRuntime(runtimeType);
  // Alias kept for backward-compat with remaining references in this file.
  const pyodideStatus = runtimeStatus;

  const isExecType = question != null && EXEC_TYPES.has(question.type);

  // ── Session start ──────────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    progressApi
      .skills()
      .then((list) => { if (!cancelled) setSkillsBefore(new Map(list.map((s) => [s.skill_id, s]))); })
      .catch(() => { /* sin «antes», el resumen enseña solo el «después» */ });
    quizApi
      .start(mode, trackId ?? undefined, skillId ?? undefined)
      .then((res) => {
        if (cancelled) return;
        setSessionId(res.session_id);
        setQuestion(res.question);
        setSelectionReason(res.selection_reason ?? null);
        questionStart.current = Date.now();
        setLoading(false);
        // `question: null` is a normal (non-error) outcome the `!question`
        // early return below already renders — it reads selection_reason to
        // tell "needs_lesson" from any other empty pool. Setting `error`
        // here used to short-circuit straight past that branch (the `error`
        // early return comes first), so a fresh account always saw the
        // generic "no questions" dead end instead of the lesson-gate CTA.
      })
      .catch((e) => {
        if (cancelled) return;
        // Free-tier daily quota (39.4/39.34): a friendly message with the reset
        // time, not the generic "HTTP 429" the request() layer used to collapse
        // this structured detail into.
        if (isQuotaError(e)) {
          setError(
            t('quiz.quotaReachedQuestions', {
              limit: e.detail.limit,
              time: new Date(e.detail.resets_at).toLocaleTimeString(),
            }),
          );
        } else {
          setError(e instanceof Error ? e.message : 'Error');
        }
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
    // Pausado mientras se decide si salir: el tiempo no corre contra una
    // pregunta que el alumno no está mirando.
    if (feedback || summary || loading || !question || isExecType || confirmExit) return;
    if (timer <= 0) { void submitAnswer(null); return; }
    const id = setTimeout(() => setTimer((v) => v - 1), 1000);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timer, feedback, summary, loading, question, isExecType, confirmExit]);

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
    async (selectedIndex: number | null, declaredUnknown = false, evidence: AnswerEvidence = {}) => {
      if (!sessionId || !question || feedback || submitting) return;
      setSubmitting(true);
      const rt = Date.now() - questionStart.current;
      try {
        // El servidor corrige con `evidence` (salida del código o texto escrito);
        // `selectedIndex` ya no basta para dar por buena una respuesta (2026-10-01).
        const res = await quizApi.answer(sessionId, question.id, selectedIndex, rt, declaredUnknown, undefined, evidence);
        setFeedback(res);
        practiced.current.add(question.skill_id);
        setMastery((prev) => res.skill_mastery[question.skill_id] ?? prev);
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
          showToast(`+${res.xp_earned} XP${res.combo >= 3 ? ` · ${t('quiz.comboLabel', { n: res.combo })}` : ''}`, 'success');
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
            ...evidence,
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
            next_selection_reason: null,
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

  // ── fill_blank: text comparison, no Pyodide ────────────────────────────
  const handleFillBlankSubmit = useCallback(async () => {
    if (!question || feedback || submitting) return;
    const expected = (
      (language === 'es' ? question.correct_answer_es : question.correct_answer_en) ?? ''
    ).trim();
    const isCorrect = userInput.trim().toLowerCase() === expected.toLowerCase();
    await submitAnswer(isCorrect ? 1 : 0, false, { answerText: userInput });
  }, [question, feedback, submitting, language, userInput, submitAnswer]);

  // ── Exec: run code in Pyodide ──────────────────────────────────────────
  const handleRun = useCallback(async () => {
    if (!question || runLoading || feedback) return;

    const qText = language === 'es' ? question.question_es : question.question_en;
    const { code } = resolveCode(question, qText, language);

    let codeToRun: string;
    if (question.type === 'fill_blank_exec' || question.type === 'sql_exec' || question.type === 'js_exec') {
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
      await submitAnswer(isCorrect ? 1 : 0, false, { execOutput: result.output });
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
    setVerifyOutput(result.timedOut ? t('quiz.timeout') : result.error ? `Error: ${result.error}` : result.output);
    setVerifyLoading(false);
  }, [question, verifyLoading, language, runCode, t]);

  // ── Next question ──────────────────────────────────────────────────────
  const handleNext = useCallback(async () => {
    if (!feedback || !sessionId) return;
    const next = feedback.next_question;
    if (next && index + 1 < TARGET_QUESTIONS) {
      setQuestion(next);
      setSelectionReason(feedback.next_selection_reason ?? null);
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

  // Salir a mitad: el servidor ya sumó el XP de lo respondido, así que el
  // usuario se refresca aquí también (antes solo al terminar, y Yo y la barra
  // superior se quedaban en el XP de antes hasta recargar).
  const handleClose = useCallback(() => {
    if (index > 0 || feedback) void hydrateFromApi();
    resetQuiz();
    setScreen('home');
  }, [index, feedback, hydrateFromApi, resetQuiz, setScreen]);

  // Cada respuesta ya está guardada en el servidor; la confirmación solo
  // aparece cuando hay algo respondido, para que salir no parezca perderlo.
  const requestClose = useCallback(() => {
    if (index > 0 || feedback) setConfirmExit(true);
    else handleClose();
  }, [index, feedback, handleClose]);

  // Teclado: 1–4 o A–D eligen opción; Enter pasa a la siguiente. Un solo
  // listener que llama siempre al manejador del último render (se actualiza en
  // un layout effect, antes de pintar): re-engancharlo en cada render dejaba un
  // hueco en el que un Enter justo tras responder veía el estado anterior.
  const onKeyRef = useRef<(e: KeyboardEvent) => void>(() => {});
  useLayoutEffect(() => {
    onKeyRef.current = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.target instanceof HTMLElement && e.target.closest('input, textarea, [contenteditable], .monaco-editor')) return;
      if (!question || summary) return;
      if (feedback) {
        if (e.key === 'Enter') { e.preventDefault(); void handleNext(); }
        return;
      }
      if (isExecType || submitting) return;
      const n = ((viewLang === 'es' ? question.options_es : question.options_en) ?? []).length;
      const k = e.key.toLowerCase();
      const i = /^[1-9]$/.test(k) ? Number(k) - 1 : /^[a-z]$/.test(k) ? k.charCodeAt(0) - 97 : -1;
      if (i >= 0 && i < n) { e.preventDefault(); void handleAnswer(i); }
    };
  });
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => onKeyRef.current(e);
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const handleUpgrade = useCallback(() => {
    setScreen('profile');
  }, [setScreen]);

  const handleGoToLesson = useCallback(() => {
    resetQuiz();
    setScreen('tracks');
  }, [resetQuiz, setScreen]);

  // ── Early returns ──────────────────────────────────────────────────────
  if (loading) return <QuizLoader />;
  if (error) return <QuizError message={error} onClose={handleClose} />;
  if (summary) {
    return (
      <SessionSummary
        summary={summary}
        before={skillsBefore}
        practiced={[...practiced.current]}
        lang={language}
        onClose={handleClose}
      />
    );
  }
  if (!question) {
    // 32.4 gates "study"/"review" on having viewed the skill's lesson first
    // (lesson_gate.py) and already tells the frontend why via
    // selection_reason.pool — but until now nothing here read it, so a
    // brand-new user hitting "ESTUDIAR AHORA" on Home (which starts a study
    // session with no skill pinned) landed on a dead-end "no questions"
    // screen instead of being pointed at a lesson.
    if (selectionReason?.pool === 'needs_lesson') {
      return (
        <QuizError
          title={t('quiz.needsLessonTitle')}
          message={t('quiz.needsLessonMessage')}
          onClose={handleClose}
          actionLabel={t('quiz.needsLessonAction')}
          onAction={handleGoToLesson}
        />
      );
    }
    return <QuizError message={t('quiz.noQuestions')} onClose={handleClose} />;
  }

  const qText = viewLang === 'es' ? question.question_es : question.question_en;
  const options = (viewLang === 'es' ? question.options_es : question.options_en) ?? [];
  const { prose, code } = resolveCode(question, qText, viewLang);
  const answered = feedback !== null;
  const otherLang: 'es' | 'en' = viewLang === 'es' ? 'en' : 'es';

  // Fichas de dificultad con los tokens *-text: texto pequeño sobre el fondo,
  // donde los tonos crudos no llegan a 4.5:1 (línea roja 6).
  const diffClass =
    question.difficulty_tier === 'hard' || question.difficulty_tier === 'expert'
      ? styles.diffHard
      : question.difficulty_tier === 'medium'
        ? styles.diffMedium
        : styles.diffEasy;

  // ── Shared header + stats bar ──────────────────────────────────────────
  const header = (
    <>
      <div className={styles.header}>
        <button type="button" className={styles.closeBtn} onClick={requestClose} aria-label={t('quiz.close')}>
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20" aria-hidden="true">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
          </svg>
        </button>
        <div className={styles.progressWrap}>
          <ProgressBar
            value={index + 1}
            max={TARGET_QUESTIONS}
            label={t('a11y.progressQuestion', { n: index + 1, total: TARGET_QUESTIONS })}
            color="var(--le-blue)"
            height={4}
          />
        </div>
        <span className={styles.progressLabel}>{index + 1} / {TARGET_QUESTIONS}</span>
        {!isExecType && (
          <span className={`${styles.timer} ${timer <= 5 ? styles.timerDanger : ''}`} aria-label={t('quiz.timeLeft', { s: timer })}>
            {timer}s
          </span>
        )}
      </div>
      {confirmExit && (
        <div className={styles.exitConfirm} role="alertdialog" aria-label={t('quiz.exitConfirm')}>
          <p>{t('quiz.exitConfirm')}</p>
          <div className={styles.exitActions}>
            <button type="button" className={styles.btnGhost} onClick={() => setConfirmExit(false)} autoFocus>
              {t('quiz.exitStay')}
            </button>
            <button type="button" className={styles.btnLeave} onClick={handleClose}>
              {t('quiz.exitLeave')}
            </button>
          </div>
        </div>
      )}
    </>
  );

  const statsBar = (
    <div className={styles.statsBar}>
      <span className={`${styles.diffBadge} ${diffClass}`}>{t(`quiz.diff.${question.difficulty_tier}`)}</span>
      {combo > 0 && <span className={styles.combo}>{t('quiz.comboLabel', { n: combo })}</span>}
      <span className={styles.xpBadge}><b>{xpEarned}</b> XP</span>
    </div>
  );

  const masteryBar = mastery === null ? null : (
    <div
      className={styles.masteryBar}
      role="progressbar"
      aria-valuenow={Math.round(mastery * 100)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={t('quiz.mastery')}
    >
      <span className={styles.masteryLabel}>{t('quiz.mastery')}</span>
      <div className={styles.masteryTrack}>
        <div className={styles.masteryFill} style={{ width: `${Math.round(mastery * 100)}%` }} />
      </div>
      <span className={styles.masteryValue}>{Math.round(mastery * 100)}%</span>
    </div>
  );

  const questionCard = (
    <div className={styles.questionCard}>
      <div className={styles.questionTop}>
        <span className={styles.topic}>
          {t(`quiz.mode.${mode}`) ?? mode}
          {selectionReason && (
            <span className={styles.selectionReason}>
              {' · '}{t(`quiz.reason.${selectionReason.pool}`)}
              {selectionReason.expected_p != null && (
                <> · {t('quiz.reason.expected', { val: Math.round(selectionReason.expected_p * 100) })}</>
              )}
            </span>
          )}
        </span>
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
    <motion.div
      className={`${styles.explanation} ${feedback.correct ? styles.explanationOk : ''}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
    >
      <p className={styles.explanationHeader}>
        {feedback.correct ? t('quiz.correct') : t('quiz.explanation')}
      </p>
      <p className={styles.explanationText}>
        <GlossaryText
          text={viewLang === 'es' ? feedback.explanation_es : feedback.explanation_en}
          terms={glossaryTerms}
          lang={viewLang}
          onPick={setPickedTerm}
        />
      </p>
      {feedback.source && <SourceLine source={feedback.source} />}

      {aiExplanations && <WhyButton questionId={question.id} isPremium={isPremium} onUpgrade={handleUpgrade} />}
      <ReportQuestion key={question.id} questionId={question.id} />

      <button type="button" className={styles.btnNext} onClick={handleNext}>
        {index + 1 >= TARGET_QUESTIONS || !feedback.next_question ? t('quiz.seeResults') : t('quiz.next')}
      </button>
    </motion.div>
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

    const engineLoadingLabel =
      runtimeType === 'sql' ? t('quiz.engineLoadingSql')
      : t('quiz.engineLoading');
    const engineLabel =
      runtimeStatus === 'loading'
        ? engineLoadingLabel
        : runtimeStatus === 'error'
          ? t('quiz.engineError')
          : null;

    return (
      <div className={styles.screen}>
        {header}
        {statsBar}
        {masteryBar}
        {questionCard}

        <div className={styles.execArea}>
          {question.type === 'fill_blank' && (
            <>
              {/* «¿Qué imprime?» con respuesta escrita: el código tiene que verse.
                  Antes no se pintaba y 11 preguntas pedían adivinar un código oculto. */}
              {code && <pre className={styles.codeBlock}><code>{code}</code></pre>}
              <input
                className={styles.blankInput}
                type="text"
                placeholder={t('quiz.fillBlankPlaceholder')}
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                disabled={answered}
                onKeyDown={(e) => { if (e.key === 'Enter' && !answered) void handleFillBlankSubmit(); }}
                autoFocus
              />
              {!answered && (
                <button
                  type="button"
                  className={styles.btnRun}
                  onClick={() => void handleFillBlankSubmit()}
                  disabled={answered || submitting || !userInput.trim()}
                >
                  {submitting ? t('quiz.submitting', 'Enviando...') : t('quiz.submit', 'Confirmar')}
                </button>
              )}
              {answered && feedback && (
                <div className={`${styles.outputBox} ${feedback.correct ? styles.outputCorrect : styles.outputWrong}`}>
                  <span className={styles.outputLabel}>
                    {feedback.correct ? t('quiz.correct') : t('quiz.outputWrong')}
                  </span>
                  {!feedback.correct && expected && (
                    <p className={styles.expectedHint}>
                      {t('quiz.expected')}: <code>{expected}</code>
                    </p>
                  )}
                </div>
              )}
            </>
          )}

          {(question.type === 'fill_blank_exec' || question.type === 'js_exec') && code && (
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

          {question.type === 'sql_exec' && code && (
            <>
              <pre className={styles.codeBlock}>
                <code>{code.replace('___', `[${t('quiz.yourAnswer')}]`)}</code>
              </pre>
              <label htmlFor="sql-exec-answer" className="visually-hidden">
                {t('quiz.fillBlankPlaceholder')}
              </label>
              <input
                id="sql-exec-answer"
                className={styles.blankInput}
                type="text"
                placeholder={t('quiz.fillBlankPlaceholder')}
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                disabled={answered}
                onKeyDown={(e) => { if (e.key === 'Enter' && !answered && !runLoading) void handleRun(); }}
                autoFocus
              />
            </>
          )}

          {question.type === 'fix_bug' && (
            <Suspense fallback={<div className={styles.codeEditor} style={{ minHeight: 88 }} />}>
              <MonacoCodeEditor
                value={userInput}
                onChange={answered ? undefined : setUserInput}
                language={runtimeType === 'sql' ? 'sql' : 'python'}
                disabled={answered}
                minLines={Math.max(4, (userInput.match(/\n/g) ?? []).length + 2)}
              />
            </Suspense>
          )}

          {question.type !== 'fill_blank' && !answered && (
            <button
              type="button"
              className={styles.btnRun}
              onClick={() => void handleRun()}
              disabled={runLoading || answered || pyodideStatus !== 'ready'}
            >
              {runLoading
                ? t('quiz.executing')
                : engineLabel ?? `▶ ${t('quiz.runCode')}${execAttempts > 0 ? ` (${attemptsLeft} ${t('quiz.attemptsLeft')})` : ''}`}
            </button>
          )}

          {runResult && (
            <div className={`${styles.outputBox} ${lastCorrect ? styles.outputCorrect : styles.outputWrong}`}>
              <span className={styles.outputLabel}>
                {lastCorrect
                  ? t('quiz.outputCorrect')
                  : runResult.timedOut
                    ? t('quiz.timeout')
                    : runResult.error
                      ? t('quiz.outputError')
                      : t('quiz.outputWrong')}
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
            <motion.button
              key={i}
              type="button"
              className={cls}
              onClick={() => handleAnswer(i)}
              disabled={answered || submitting}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05, duration: 0.15 }}
              whileTap={{ scale: answered ? 1 : 0.97 }}
            >
              <span className={styles.optionLetter}>{String.fromCharCode(65 + i)}</span>
              <span className={styles.optionText}>{opt}</span>
              {answered && feedback && i === feedback.correct_index && <span className={styles.optionIcon}>✓</span>}
              {answered && i === selected && feedback && i !== feedback.correct_index && <span className={styles.optionIcon}>✗</span>}
            </motion.button>
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
      {!answered && <p className={styles.keysHint}>{t('quiz.keysHint')}</p>}

      {answered && question.type === 'code_output' && code && (
        <div className={styles.verifyArea}>
          {verifyOutput != null ? (
            <div className={styles.outputBox}>
              <span className={styles.outputLabel}>{t('quiz.actualOutput')}</span>
              <pre className={styles.outputPre}>{verifyOutput}</pre>
            </div>
          ) : (
            <button
              type="button"
              className={styles.btnVerify}
              onClick={() => void handleVerify()}
              disabled={verifyLoading || pyodideStatus !== 'ready'}
            >
              {verifyLoading
                ? t('quiz.executing')
                : pyodideStatus === 'loading'
                  ? t('quiz.engineLoading')
                  : `▶ ${t('quiz.runToVerify')}`}
            </button>
          )}
        </div>
      )}

      {lottieSrc && (
        <div className={styles.lottie} aria-hidden="true">
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
    <div className={styles.summary} role="status">
      <span className={styles.loaderDot} aria-hidden="true" />
      <p className={styles.summaryAccuracy}>{t('loading')}</p>
    </div>
  );
}

function QuizError({
  title,
  message,
  onClose,
  actionLabel,
  onAction,
}: {
  title?: string;
  message: string;
  onClose: () => void;
  actionLabel?: string;
  onAction?: () => void;
}) {
  const { t } = useTranslation();
  return (
    <div className={styles.summary}>
      <h1 className={styles.summaryTitle}>{title ?? t('quiz.noQuestionsAvail')}</h1>
      <p className={styles.summaryAccuracy}>{message}</p>
      <div className={styles.summaryActions}>
        {actionLabel && onAction && (
          <button type="button" className={styles.btnPrimary} onClick={onAction}>{actionLabel}</button>
        )}
        <button type="button" className={styles.btnStudy} onClick={onClose}>{t('back')}</button>
      </div>
    </div>
  );
}

const pct = (x: number) => Math.round(x * 100);

function SessionSummary({
  summary, before, practiced, lang, onClose,
}: {
  summary: QuizEndResponse;
  before: Map<string, SkillMasteryDetail> | null;
  practiced: string[];
  lang: 'es' | 'en';
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const startLesson = useAppStore((s) => s.startLesson);
  const startQuiz = useAppStore((s) => s.startQuiz);
  const [after, setAfter] = useState<SkillMasteryDetail[] | null>(null);

  // El «después» se lee al terminar: es el mismo dato que el «antes», así que
  // la diferencia es la que el motor registró en esta sesión, no una estimación.
  useEffect(() => {
    let cancelled = false;
    progressApi.skills().then((list) => { if (!cancelled) setAfter(list); }).catch(() => setAfter([]));
    return () => { cancelled = true; };
  }, []);

  const accuracy = Math.round(summary.accuracy * 100);
  const grade = accuracy >= 90 ? 'S' : accuracy >= 80 ? 'A' : accuracy >= 70 ? 'B' : accuracy >= 60 ? 'C' : 'F';
  const moved = (after ?? [])
    .filter((s) => practiced.includes(s.skill_id))
    .sort((a, b) => a.p_known - b.p_known);
  const weakest = moved[0];

  return (
    <motion.div
      className={styles.summary}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
    >
      <div className={styles.summaryGrade} data-grade={grade} aria-hidden="true">{grade}</div>
      <h1 className={styles.summaryTitle}>{accuracy >= 80 ? t('quiz.excellent') : accuracy >= 60 ? t('quiz.goodJob') : t('quiz.keepGoing')}</h1>
      <p className={styles.summaryAccuracy}>{accuracy}% {t('quiz.accuracyLabel')}</p>
      <div className={styles.summaryStats}>
        <div className={styles.summaryStat}>
          <span className={styles.summaryStatVal}>{summary.correct}/{summary.total_questions}</span>
          <span className={styles.summaryStatLabel}>{t('quiz.correctLabel')}</span>
        </div>
        <div className={styles.summaryStat}>
          <span className={styles.summaryStatVal}>{summary.max_combo}</span>
          <span className={styles.summaryStatLabel}>{t('quiz.maxCombo')}</span>
        </div>
        <div className={styles.summaryStat}>
          <span className={styles.summaryStatVal}>{summary.xp_earned}</span>
          <span className={styles.summaryStatLabel}>{t('quiz.xpEarned')}</span>
        </div>
      </div>
      {(summary.credits_earned ?? 0) > 0 && (
        <p className={styles.summaryAccuracy}>{t('quiz.creditsEarned', { count: summary.credits_earned })}</p>
      )}

      {moved.length > 0 && (
        <section className={styles.moved} aria-label={t('quiz.skillsMoved')}>
          <h2 className={styles.movedTitle}>{t('quiz.skillsMoved')}</h2>
          <ul className={styles.movedList}>
            {moved.map((s) => {
              // Sin intentos previos no hay medida «antes»: es nueva, no un 0 %.
              const prev = before?.get(s.skill_id);
              const b = prev && prev.attempts > 0 ? prev.p_known : undefined;
              const name = lang === 'es' ? s.name_es : s.name_en;
              return (
                <li key={s.skill_id} className={styles.movedItem}>
                  <span className={styles.movedName}>{name}</span>
                  <span className={styles.movedBars} aria-hidden="true">
                    <span className={styles.movedBefore} style={{ width: `${pct(b ?? 0)}%` }} />
                    <span className={styles.movedAfter} style={{ width: `${pct(s.p_known)}%` }} />
                  </span>
                  <span className={styles.movedPct}>
                    {b === undefined ? t('quiz.skillNew') : `${pct(b)}%`} → {pct(s.p_known)}%
                  </span>
                </li>
              );
            })}
          </ul>
        </section>
      )}

      <div className={styles.summaryActions}>
        {weakest && weakest.p_known < 0.4 ? (
          <button type="button" className={styles.btnPrimary} onClick={() => startLesson(weakest.skill_id)}>
            {t('quiz.reviewLesson', { name: lang === 'es' ? weakest.name_es : weakest.name_en })}
          </button>
        ) : (
          <button type="button" className={styles.btnPrimary} onClick={() => startQuiz('study', 10)}>
            {t('quiz.anotherSession')}
          </button>
        )}
        <button type="button" className={styles.btnStudy} onClick={onClose}>{t('quiz.continue')}</button>
      </div>
    </motion.div>
  );
}
