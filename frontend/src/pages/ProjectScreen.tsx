import { useState, useCallback, useRef, lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { useAppStore } from '../stores/useAppStore';
import { useApi } from '../hooks/useApi';
import { useRuntime, type RuntimeType } from '../hooks/useRuntime';
import {
  projects as projectsApi,
  type ProjectDetail,
  type ProjectStepRead,
} from '../services/api';
import styles from './ProjectScreen.module.css';

const MonacoCodeEditor = lazy(
  () => import('../components/quiz/MonacoCodeEditor').then((m) => ({ default: m.MonacoCodeEditor }))
);

const MONACO_LANG: Record<RuntimeType, string> = {
  python: 'python',
  sql: 'sql',
  js: 'javascript',
};

export function ProjectScreen() {
  const { t } = useTranslation();
  const lang = useAppStore((s) => s.user.language);
  const setScreen = useAppStore((s) => s.setScreen);
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
  const listing = useApi(() => projectsApi.list(), []);

  const runtimeClass: Record<string, string> = {
    python: styles.runtimePython,
    sql: styles.runtimeSql,
    js: styles.runtimeJs,
  };

  return (
    <div className={styles.listScreen}>
      <div className={styles.header} style={{ border: 'none', padding: 0 }}>
        <button className={styles.backBtn} onClick={() => setScreen('home')}>←</button>
        <h1 className={styles.title}>{t('project.title')}</h1>
      </div>

      {listing.loading && <p className={styles.loading}>{t('home.loading')}</p>}

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
              {p.difficulty === 1 ? '⭐' : p.difficulty === 2 ? '⭐⭐' : '⭐⭐⭐'}
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
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [projectCompleted, setProjectCompleted] = useState(false);
  const outputRef = useRef<HTMLDivElement>(null);

  const runtime: RuntimeType = project.data?.runtime ?? 'python';
  const { status: runtimeStatus, runCode } = useRuntime(runtime);

  const step: ProjectStepRead | undefined = project.data?.steps[currentStep];

  const getCode = useCallback(
    (stepIdx: number) => {
      if (codes[stepIdx] !== undefined) return codes[stepIdx];
      const s = project.data?.steps[stepIdx];
      return s?.starter_code ?? '';
    },
    [codes, project.data]
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

    if (result.timedOut) {
      setError(t('playground.timedOut'));
      setTestResult('fail');
    } else if (result.error) {
      setError(result.error);
      setOutput(result.output);
      setTestResult('fail');
    } else {
      setOutput(result.output);
      setTestResult('pass');
      setCompletedSteps((prev) => new Set(prev).add(currentStep));
      if (project.data && currentStep === project.data.steps.length - 1) {
        setProjectCompleted(true);
      }
    }
    setIsRunning(false);
    outputRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [runCode, isRunning, step, getCode, currentStep, t, project.data]);

  if (project.loading) {
    return (
      <div className={styles.screen}>
        <div className={styles.header}>
          <button className={styles.backBtn} onClick={onBack}>←</button>
          <span className={styles.title}>{t('home.loading')}</span>
        </div>
      </div>
    );
  }

  if (!project.data || !step) {
    return (
      <div className={styles.screen}>
        <div className={styles.header}>
          <button className={styles.backBtn} onClick={onBack}>←</button>
          <span className={styles.title}>{t('project.notFound')}</span>
        </div>
      </div>
    );
  }

  const totalSteps = project.data.steps.length;

  return (
    <div className={styles.screen}>
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={onBack}>←</button>
        <span className={styles.title}>
          {lang === 'es' ? project.data.name_es : project.data.name_en}
        </span>
        <span className={styles.badge}>
          {completedSteps.size}/{totalSteps}
        </span>
      </div>

      {projectCompleted && (
        <div className={styles.completedBanner}>
          {t('project.completed')} 🎉
        </div>
      )}

      <div className={styles.stepTabs}>
        {project.data.steps.map((s, idx) => (
          <button
            key={s.id}
            className={`${styles.stepTab} ${idx === currentStep ? styles.active : ''} ${completedSteps.has(idx) ? styles.completed : ''}`}
            onClick={() => {
              setCurrentStep(idx);
              setOutput('');
              setError('');
              setTestResult(null);
            }}
          >
            {completedSteps.has(idx) ? '✓' : idx + 1}
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
            <Suspense fallback={<p className={styles.loading}>{t('playground.loadingEditor')}</p>}>
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
                <p className={styles.passOutput}>{t('project.testsPassed')}</p>
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
