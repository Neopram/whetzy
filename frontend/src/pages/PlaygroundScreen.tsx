import { useState, useCallback, useEffect, useRef, lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { Loading } from '../components/common/Loading';
import { motion } from 'framer-motion';
import { useRuntime, type RuntimeType } from '../hooks/useRuntime';
import { useAppStore } from '../stores/useAppStore';
import {
  savePlaygroundEntry,
  getPlaygroundHistory,
  clearPlaygroundHistory,
  getLatestForSkill,
  type PlaygroundEntry,
} from '../services/playgroundDb';
import styles from './PlaygroundScreen.module.css';

const MonacoCodeEditor = lazy(
  () => import('../components/quiz/MonacoCodeEditor').then((m) => ({ default: m.MonacoCodeEditor })),
);

const RUNTIMES: { key: RuntimeType; label: string; icon: string; defaultCode: string }[] = [
  {
    key: 'python',
    label: 'Python',
    icon: '🐍',
    defaultCode: '# Python 3 (Pyodide)\nprint("Hello, Whetzy!")\n',
  },
  {
    key: 'sql',
    label: 'SQL',
    icon: '🗃️',
    defaultCode: "-- SQLite (sql.js)\nSELECT 'Hello, Whetzy!' AS greeting;\n",
  },
  {
    key: 'js',
    label: 'JavaScript',
    icon: '⚡',
    defaultCode: '// JavaScript (sandboxed Worker)\nconsole.log("Hello, Whetzy!");\n',
  },
];

const MONACO_LANG: Record<RuntimeType, string> = {
  python: 'python',
  sql: 'sql',
  js: 'javascript',
};

export function PlaygroundScreen() {
  const { t } = useTranslation();
  const setScreen = useAppStore((s) => s.setScreen);
  const previousScreen = useAppStore((s) => s.previousScreen);
  // 43.7 (ADR-65 D9): abierto desde una lección, empieza en su ejemplo y su runtime.
  const seed = useAppStore((s) => s.playgroundSeed);

  const [activeRuntime, setActiveRuntime] = useState<RuntimeType>(seed?.runtime ?? 'python');
  const [codes, setCodes] = useState<Record<RuntimeType, string>>(() => ({
    python: RUNTIMES[0].defaultCode,
    sql: RUNTIMES[1].defaultCode,
    js: RUNTIMES[2].defaultCode,
    ...(seed ? { [seed.runtime]: seed.code } : {}),
  }));

  // Si el alumno ya probó algo para esta skill, reaparece su último fragmento.
  useEffect(() => {
    if (!seed) return;
    let alive = true;
    getLatestForSkill(seed.skillId)
      .then((entry) => {
        if (alive && entry && entry.runtime === seed.runtime) {
          setCodes((prev) => ({ ...prev, [seed.runtime]: entry.code }));
        }
      })
      .catch(() => { /* sin IndexedDB: se queda el ejemplo */ });
    return () => { alive = false; };
  }, [seed]);
  const [output, setOutput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [history, setHistory] = useState<PlaygroundEntry[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  const { status, runCode } = useRuntime(activeRuntime);
  const outputRef = useRef<HTMLDivElement>(null);

  const handleRun = useCallback(async () => {
    const code = codes[activeRuntime].trim();
    if (!code || isRunning) return;

    setIsRunning(true);
    setOutput('');
    setError(null);

    try {
      const result = await runCode(code, 10_000);

      if (result.timedOut) {
        setOutput(result.output);
        setError(t('playground.timedOut'));
      } else if (result.error) {
        setOutput(result.output);
        setError(result.error);
      } else {
        setOutput(result.output || t('playground.noOutput'));
        setError(null);
      }

      try {
        await savePlaygroundEntry({
          runtime: activeRuntime,
          code,
          output: result.output,
          error: result.error ?? (result.timedOut ? 'Timeout' : null),
          timestamp: new Date().toISOString(),
          ...(seed && activeRuntime === seed.runtime ? { skill_id: seed.skillId } : {}),
        });
      } catch {
        // IndexedDB not available — history won't persist
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsRunning(false);
      outputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [codes, activeRuntime, isRunning, runCode, t, seed]);

  const handleLoadHistory = useCallback(async () => {
    try {
      const entries = await getPlaygroundHistory(activeRuntime, 30);
      setHistory(entries);
      setShowHistory(true);
    } catch {
      setHistory([]);
      setShowHistory(true);
    }
  }, [activeRuntime]);

  const handleClearHistory = useCallback(async () => {
    try {
      await clearPlaygroundHistory();
      setHistory([]);
    } catch {
      // ignore
    }
  }, []);

  const handleRestoreEntry = useCallback(
    (entry: PlaygroundEntry) => {
      setCodes((prev) => ({ ...prev, [entry.runtime]: entry.code }));
      setActiveRuntime(entry.runtime);
      setOutput(entry.output);
      setError(entry.error);
      setShowHistory(false);
    },
    [],
  );

  const handleCodeChange = useCallback(
    (val: string) => {
      setCodes((prev) => ({ ...prev, [activeRuntime]: val }));
    },
    [activeRuntime],
  );

  const runtimeReady = activeRuntime === 'js' || status === 'ready';
  const runtimeLoading = status === 'loading';

  return (
    <motion.div
      className={styles.screen}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <header className={styles.header}>
        <button
          className={styles.backBtn}
          onClick={() => setScreen(previousScreen === 'playground' ? 'home' : previousScreen)}
          aria-label={t('common.back')}
        >
          <span aria-hidden="true">←</span>
        </button>
        <h1 className={styles.title}>{t('playground.title')}</h1>
      </header>

      {seed && (
        <div className={styles.seedBar}>
          <span>{t('playground.fromLesson')}</span>
          <button
            type="button"
            className={styles.historyBtn}
            onClick={() => {
              setCodes((prev) => ({ ...prev, [seed.runtime]: seed.code }));
              setActiveRuntime(seed.runtime);
            }}
          >
            {t('playground.restoreExample')}
          </button>
        </div>
      )}

      <div className={styles.runtimeTabs}>
        {RUNTIMES.map((rt) => (
          <button
            key={rt.key}
            className={`${styles.tab} ${activeRuntime === rt.key ? styles.tabActive : ''}`}
            onClick={() => setActiveRuntime(rt.key)}
          >
            <span className={styles.tabIcon}>{rt.icon}</span>
            <span className={styles.tabLabel}>{rt.label}</span>
          </button>
        ))}
      </div>

      <div className={styles.editorContainer}>
        <Suspense fallback={<div className={styles.editorLoading}><Loading label={t('playground.loadingEditor')} shape="line" /></div>}>
          <MonacoCodeEditor
            value={codes[activeRuntime]}
            onChange={handleCodeChange}
            language={MONACO_LANG[activeRuntime]}
            minLines={12}
          />
        </Suspense>
      </div>

      <div className={styles.controls}>
        <button
          className={styles.runBtn}
          onClick={handleRun}
          disabled={!runtimeReady || isRunning}
          aria-busy={isRunning}
        >
          {isRunning
            ? t('playground.running')
            : runtimeLoading
              ? t('playground.loadingRuntime')
              : `▶ ${t('playground.run')}`}
        </button>
        <button className={styles.historyBtn} onClick={handleLoadHistory}>
          {t('playground.history')}
        </button>
      </div>

      <div className={styles.outputPanel} ref={outputRef}>
        <div className={styles.outputHeader}>{t('playground.output')}</div>
        {error && <pre className={styles.errorOutput}>{error}</pre>}
        {output && <pre className={styles.stdOutput}>{output}</pre>}
        {!output && !error && !isRunning && (
          <p className={styles.placeholder}>{t('playground.runToSee')}</p>
        )}
      </div>

      {showHistory && (
        <div className={styles.historyPanel}>
          <div className={styles.historyHeader}>
            <h2>{t('playground.historyTitle')}</h2>
            <div className={styles.historyActions}>
              {history.length > 0 && (
                <button className={styles.clearBtn} onClick={handleClearHistory}>
                  {t('playground.clearHistory')}
                </button>
              )}
              <button className={styles.closeBtn} onClick={() => setShowHistory(false)} aria-label={t('common.close')}>
                <span aria-hidden="true">✕</span>
              </button>
            </div>
          </div>
          {history.length === 0 ? (
            <p className={styles.placeholder}>{t('playground.noHistory')}</p>
          ) : (
            <ul className={styles.historyList}>
              {history.map((entry) => (
                <li key={entry.id} className={styles.historyItem}>
                  <button className={styles.historyRestore} onClick={() => handleRestoreEntry(entry)}>
                    <span className={styles.historyRuntime}>
                      {RUNTIMES.find((r) => r.key === entry.runtime)?.icon ?? ''}
                    </span>
                    <span className={styles.historyCode}>
                      {entry.code.slice(0, 60)}{entry.code.length > 60 ? '…' : ''}
                    </span>
                    <span className={styles.historyTime}>
                      {new Date(entry.timestamp).toLocaleString()}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </motion.div>
  );
}
