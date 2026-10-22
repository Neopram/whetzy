import { useState, useCallback, useEffect, useRef, lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, useReducedMotion } from 'framer-motion';
import { DUR } from '../lib/motion';
import { emit as emitFx } from '../lib/feedbackFx';
import { useAppStore } from '../stores/useAppStore';
import { useApi } from '../hooks/useApi';
import { useRuntime, type RuntimeType } from '../hooks/useRuntime';
import {
  ApiError,
  projects as projectsApi,
  type ProjectStepRead,
  type ProjectSubmissionRead,
} from '../services/api';
import styles from './ProjectScreen.module.css';
import { GameIcon } from '../components/common/AppIcon';
import { Loading } from '../components/common/Loading';

const MonacoCodeEditor = lazy(
  () => import('../components/quiz/MonacoCodeEditor').then((m) => ({ default: m.MonacoCodeEditor }))
);

const MONACO_LANG: Record<RuntimeType, string> = {
  python: 'python',
  sql: 'sql',
  js: 'javascript',
};

export function ProjectScreen() {
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);

  if (selectedSlug) {
    return <ProjectRunner slug={selectedSlug} onBack={() => setSelectedSlug(null)} />;
  }

  return <ProjectList onSelect={setSelectedSlug} />;
}

function ProjectList({ onSelect }: { onSelect: (slug: string) => void }) {
  const { t } = useTranslation();
  const lang = useAppStore((s) => s.user.language);
  const setScreen = useAppStore((s) => s.setScreen);
  // 43.6: desde el detalle de una ruta, solo los de esa ruta.
  const trackId = useAppStore((s) => s.projectsTrackId);
  const listing = useApi(() => projectsApi.list(trackId ?? undefined), [trackId]);

  const runtimeClass: Record<string, string> = {
    python: styles.runtimePython,
    sql: styles.runtimeSql,
    js: styles.runtimeJs,
  };

  return (
    <div className={styles.listScreen}>
      <div className={styles.header} style={{ border: 'none', padding: 0 }}>
        <button className={styles.backBtn} onClick={() => setScreen('home')} aria-label={t('common.back')}><span aria-hidden="true">←</span></button>
        <h1 className={styles.title}>{t('project.title')}</h1>
      </div>

      {listing.loading && <Loading label={t('home.loading')} shape="line" />}

      {listing.data && listing.data.length === 0 && (
        <p className={styles.empty}>{t('project.noProjects')}</p>
      )}

      {listing.data?.map((p) => (
        <motion.div
          key={p.id}
          className={styles.projectCard}
          onClick={() => onSelect(p.slug)}
          whileTap={{ scale: 0.98 }}
        >
          <div className={styles.projectInfo}>
            <p className={styles.projectName}>
              {lang === 'es' ? p.name_es : p.name_en}
            </p>
            <p className={styles.projectMeta}>
              <span role="img" aria-label={`${p.difficulty}/3`}>
                {Array.from({ length: Math.min(Math.max(p.difficulty, 1), 3) }, (_, k) => (
                  <GameIcon key={k} name="estrella" size={14} />
                ))}
              </span>
              {' · '}
              {p.source_license}
            </p>
          </div>
          <span className={`${styles.runtimeBadge} ${runtimeClass[p.runtime] ?? ''}`}>
            {p.runtime.toUpperCase()}
          </span>
        </motion.div>
      ))}
    </div>
  );
}

function ProjectRunner({ slug, onBack }: { slug: string; onBack: () => void }) {
  const { t } = useTranslation();
  const lang = useAppStore((s) => s.user.language);

  const project = useApi(() => projectsApi.get(slug), [slug]);
  const [currentStep, setCurrentStep] = useState(0);
  const [codes, setCodes] = useState<Record<number, string>>({});
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [testResult, setTestResult] = useState<'pass' | 'fail' | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const reduce = useReducedMotion();
  // 43.6 (ADR-65 D8): el progreso es el del servidor. Antes vivía solo aquí y
  // se perdía al salir; el servidor nunca se enteraba.
  const [submission, setSubmission] = useState<ProjectSubmissionRead | null>(null);
  const [syncFailed, setSyncFailed] = useState(false);
  const positioned = useRef(false);
  const outputRef = useRef<HTMLDivElement>(null);

  const runtime: RuntimeType = project.data?.runtime ?? 'python';
  const { status: runtimeStatus, runCode } = useRuntime(runtime);

  const steps = project.data?.steps ?? [];
  const step: ProjectStepRead | undefined = steps[currentStep];
  const serverStep = submission?.current_step ?? 1;
  const projectCompleted = submission?.completed ?? false;
  const isDone = (s: ProjectStepRead) => projectCompleted || s.step_number < serverStep;
  const isOpen = (s: ProjectStepRead) => projectCompleted || s.step_number <= serverStep;

  useEffect(() => {
    let alive = true;
    projectsApi
      .progress(slug)
      .catch((e: unknown) => {
        if (!(e instanceof ApiError && e.status === 404)) throw e;
        // Si otra petición lo empezó a la vez (StrictMode, dos pestañas), 409:
        // el progreso ya existe y se lee.
        return projectsApi.start(slug).catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 409) return projectsApi.progress(slug);
          throw err;
        });
      })
      .then((sub) => { if (alive) setSubmission(sub); })
      .catch(() => { if (alive) setSyncFailed(true); });
    return () => { alive = false; };
  }, [slug]);

  // Se abre en el paso donde se dejó, una vez, cuando llegan los dos datos.
  useEffect(() => {
    if (positioned.current || !submission || steps.length === 0) return;
    positioned.current = true;
    const idx = steps.findIndex((s) => s.step_number === submission.current_step);
    setCurrentStep(submission.completed || idx < 0 ? steps.length - 1 : idx);
  }, [submission, steps]);

  const getCode = useCallback(
    (stepIdx: number) => {
      if (codes[stepIdx] !== undefined) return codes[stepIdx];
      const s = project.data?.steps[stepIdx];
      const saved = s ? submission?.step_code?.[String(s.step_number)] : undefined;
      return saved ?? s?.starter_code ?? '';
    },
    [codes, project.data, submission]
  );

  const handleRun = useCallback(async () => {
    if (!runCode || isRunning) return;
    setIsRunning(true);
    setOutput('');
    setError('');
    setTestResult(null);

    const code = getCode(currentStep);
    const result = await runCode(code, 10000);

    if (result.timedOut) {
      setError(t('playground.timedOut'));
    } else if (result.error) {
      setError(result.error);
      setOutput(result.output);
    } else {
      setOutput(result.output);
    }
    setIsRunning(false);
    outputRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [runCode, isRunning, getCode, currentStep, t]);

  const handleRunTests = useCallback(async () => {
    if (!runCode || isRunning || !step) return;
    setIsRunning(true);
    setOutput('');
    setError('');
    setTestResult(null);

    const userCode = getCode(currentStep);
    const testCode = step.test_code;
    const combined = `${userCode}\n\n${testCode}`;

    const result = await runCode(combined, 15000);
    const clientPassed = !result.timedOut && !result.error;

    if (result.timedOut) {
      setError(t('playground.timedOut'));
    } else if (result.error) {
      setError(result.error);
      setOutput(result.output);
    } else {
      setOutput(result.output);
    }

    if (submission && !submission.completed && step.step_number === submission.current_step) {
      // El paso actual cuenta solo si el servidor lo acepta: en SQL ejecuta él
      // los tests; en Python/JS guarda el código y el resultado del navegador.
      try {
        const res = await projectsApi.submitStep(slug, step.step_number, userCode, clientPassed);
        setSubmission(res);
        setSyncFailed(false);
        if (res.step_passed) {
          setTestResult('pass');
          // 46.15 B: el acierto lo da el servidor, nunca el navegador solo.
          emitFx({ type: 'correct' });
        } else {
          setTestResult('fail');
          if (res.timed_out) setError(t('playground.timedOut'));
          else if (res.error) setError(res.error);
          else if (clientPassed) {
            // En SQL el servidor ejecutó los tests; en Python/JS no los ejecuta y
            // solo rechaza el código de partida sin tocar.
            setError(t(runtime === 'sql' ? 'project.serverFailed' : 'project.starterUnchanged'));
          }
        }
      } catch {
        setSyncFailed(true);
        setTestResult(null);
      }
    } else {
      // Repasar un paso ya hecho: solo la comprobación del navegador.
      setTestResult(clientPassed ? 'pass' : 'fail');
    }
    setIsRunning(false);
    outputRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [runCode, isRunning, step, getCode, currentStep, t, submission, slug, runtime]);

  if (project.loading) {
    return (
      <div className={styles.screen}>
        <div className={styles.header}>
          <button className={styles.backBtn} onClick={onBack} aria-label={t('common.back')}><span aria-hidden="true">←</span></button>
        </div>
        <Loading label={t('home.loading')} shape="card" />
      </div>
    );
  }

  if (!project.data || !step) {
    return (
      <div className={styles.screen}>
        <div className={styles.header}>
          <button className={styles.backBtn} onClick={onBack} aria-label={t('common.back')}><span aria-hidden="true">←</span></button>
          <span className={styles.title}>{t('project.notFound')}</span>
        </div>
      </div>
    );
  }

  const totalSteps = project.data.steps.length;

  return (
    <div className={styles.screen}>
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={onBack} aria-label={t('common.back')}><span aria-hidden="true">←</span></button>
        <span className={styles.title}>
          {lang === 'es' ? project.data.name_es : project.data.name_en}
        </span>
        <span className={styles.badge}>
          {steps.filter(isDone).length}/{totalSteps}
        </span>
      </div>

      {projectCompleted && (
        <div className={styles.completedBanner}>
          {t('project.completed')} <GameIcon name="confeti" size={22} />
          {!submission?.verified && <p className={styles.note}>{t('project.unverified')}</p>}
        </div>
      )}
      {syncFailed && <p role="alert" className={styles.errorOutput}>{t('project.syncFailed')}</p>}
      {!projectCompleted && submission && <p className={styles.note}>{t('project.saved')}</p>}

      <div className={styles.stepTabs}>
        {project.data.steps.map((s, idx) => (
          <button
            key={s.id}
            className={`${styles.stepTab} ${idx === currentStep ? styles.active : ''} ${isDone(s) ? styles.completed : ''}`}
            disabled={!isOpen(s)}
            title={isOpen(s) ? undefined : t('project.lockedStep')}
            aria-label={isDone(s) ? `${idx + 1} ✓` : String(idx + 1)}
            onClick={() => {
              setCurrentStep(idx);
              setOutput('');
              setError('');
              setTestResult(null);
            }}
          >
            <span aria-hidden="true">{isDone(s) ? '✓' : idx + 1}</span>
          </button>
        ))}
      </div>

      <div className={styles.body}>
        <div className={styles.instructions}>
          <h2 className={styles.stepTitle}>
            {t('project.step')} {currentStep + 1}: {lang === 'es' ? step.title_es : step.title_en}
          </h2>
          <p className={styles.stepInstructions}>
            {lang === 'es' ? step.instructions_es : step.instructions_en}
          </p>
        </div>

        <div className={styles.editorArea}>
          <div className={styles.editorContainer}>
            <Suspense fallback={<div className={styles.loading}><Loading label={t('playground.loadingEditor')} shape="line" /></div>}>
              <MonacoCodeEditor
                value={getCode(currentStep)}
                onChange={(val) => setCodes((prev) => ({ ...prev, [currentStep]: val ?? '' }))}
                language={MONACO_LANG[runtime]}
              />
            </Suspense>
          </div>

          <div className={styles.controls}>
            <button
              className={styles.runBtn}
              onClick={handleRun}
              disabled={isRunning || runtimeStatus !== 'ready'}
              aria-busy={isRunning}
            >
              {isRunning ? t('playground.running') : t('playground.run')}
            </button>
            <button
              className={styles.testBtn}
              onClick={handleRunTests}
              disabled={isRunning || runtimeStatus !== 'ready'}
            >
              {t('project.runTests')}
            </button>
          </div>

          {(output || error || testResult) && (
            <div className={styles.outputPanel} ref={outputRef}>
              {testResult === 'pass' && (
                <motion.p
                  className={styles.passOutput}
                  data-fx={reduce ? undefined : 'pass'}
                  initial={reduce ? false : { opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: DUR.response / 2 }}
                >
                  {t('project.testsPassed')}
                </motion.p>
              )}
              {error && <pre className={styles.errorOutput}>{error}</pre>}
              {output && <pre className={styles.stdOutput}>{output}</pre>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
