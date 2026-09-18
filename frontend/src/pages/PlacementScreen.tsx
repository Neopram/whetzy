import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { ProgressBar } from '../components/common/ProgressBar';
import styles from './PlacementScreen.module.css';

interface PlacementQuestion {
  /** i18n key under `placement.questions`; the text and options live there. */
  id: string;
  correctIndex: number;
  difficulty: number;
}

// The pool holds only what is language-independent: which option is right and
// how hard the question is. Stems and options come from `placement.questions.*`
// so the test exists in both languages - it used to be hardcoded Spanish, which
// meant an English learner sat a Spanish placement test (red line 3).
//
// `correctIndex` is spread across the four positions on purpose. All ten used to
// be 0, so anyone who pressed the first button ten times scored 100 % and was
// placed at the top level, skipping the whole curriculum. That is red line 1:
// the placement estimate has to measure knowledge, not a guessing habit. The
// option order in `es/common.json` and `en/common.json` is the same, so one
// index is correct for both.
export const PLACEMENT_POOL: PlacementQuestion[] = [
  { id: 'print', correctIndex: 0, difficulty: 0.1 },
  { id: 'boolType', correctIndex: 2, difficulty: 0.15 },
  { id: 'emptyList', correctIndex: 1, difficulty: 0.2 },
  { id: 'lenPython', correctIndex: 3, difficulty: 0.25 },
  { id: 'power', correctIndex: 1, difficulty: 0.3 },
  { id: 'loopKeyword', correctIndex: 2, difficulty: 0.35 },
  { id: 'self', correctIndex: 3, difficulty: 0.5 },
  { id: 'appendExtend', correctIndex: 0, difficulty: 0.55 },
  { id: 'contextManager', correctIndex: 2, difficulty: 0.7 },
  { id: 'descriptor', correctIndex: 1, difficulty: 0.85 },
];

/** 0-100 accuracy -> the i18n key naming that level. */
function levelKey(pct: number): string {
  if (pct >= 85) return 'advanced';
  if (pct >= 70) return 'upperIntermediate';
  if (pct >= 50) return 'intermediate';
  if (pct >= 30) return 'basic';
  return 'beginner';
}

export function PlacementScreen() {
  const setScreen = useAppStore((s) => s.setScreen);
  const { t } = useTranslation();
  const [phase, setPhase] = useState<'intro' | 'testing' | 'result'>('intro');
  const [qIndex, setQIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [answered, setAnswered] = useState(false);
  const [correct, setCorrect] = useState(0);
  const [total, setTotal] = useState(0);
  const [ability, setAbility] = useState(0.5);

  const entry = PLACEMENT_POOL[qIndex % PLACEMENT_POOL.length];
  const question = {
    ...entry,
    text: t(`placement.questions.${entry.id}.text`),
    options: t(`placement.questions.${entry.id}.options`, {
      returnObjects: true,
    }) as string[],
  };

  const handleAnswer = useCallback(
    (index: number) => {
      if (answered) return;
      setSelected(index);
      setAnswered(true);
      const isCorrect = index === question.correctIndex;
      if (isCorrect) setCorrect((c) => c + 1);
      setTotal((tot) => tot + 1);

      const newAbility = ability + (isCorrect ? 0.05 : -0.03);
      setAbility(Math.max(0, Math.min(1, newAbility)));

      setTimeout(() => {
        if (qIndex + 1 >= PLACEMENT_POOL.length) {
          setPhase('result');
        } else {
          setQIndex((i) => i + 1);
          setSelected(null);
          setAnswered(false);
        }
      }, 800);
    },
    [answered, question, qIndex, ability]
  );

  if (phase === 'intro') {
    return (
      <div className={styles.intro}>
        <span className={styles.introIcon}>🎓</span>
        <h1 className={styles.introTitle}>{t('placement.title')}</h1>
        <p className={styles.introDesc}>{t('placement.introDesc')}</p>
        <div className={styles.introFeatures}>
          <div className={styles.introFeature}>
            <span>🧠</span>
            <span>{t('placement.algorithm')}</span>
          </div>
          <div className={styles.introFeature}>
            <span>⏱️</span>
            <span>{t('placement.timeEst')}</span>
          </div>
          <div className={styles.introFeature}>
            <span>🎯</span>
            <span>{t('placement.skipModules')}</span>
          </div>
        </div>
        <button className={styles.startBtn} onClick={() => setPhase('testing')}>
          {t('placement.start')}
        </button>
        <button className={styles.skipBtn} onClick={() => setScreen('home')}>
          {t('placement.skip')}
        </button>
      </div>
    );
  }

  if (phase === 'result') {
    const pct = total > 0 ? Math.round((correct / total) * 100) : 0;
    const level = t(`placement.levels.${levelKey(pct)}`);

    return (
      <div className={styles.result}>
        <span className={styles.resultIcon}>
          {pct >= 70 ? '🏆' : pct >= 50 ? '💪' : '📚'}
        </span>
        <h1 className={styles.resultTitle}>{t('placement.levelResult', { level })}</h1>
        <p className={styles.resultPct}>{t('placement.pctAccuracy', { pct, correct, total })}</p>
        <div className={styles.resultBar}>
          <ProgressBar value={pct} max={100} label={t('a11y.progressScore', { pct })} color="var(--le-green)" height={16} showLabel />
        </div>
        <p className={styles.resultDesc}>
          {pct >= 70 ? t('placement.descHigh') : t('placement.descLow')}
        </p>
        <button className={styles.startBtn} onClick={() => setScreen('home')}>
          {t('placement.startLearning')}
        </button>
      </div>
    );
  }

  return (
    <div className={styles.screen}>
      <div className={styles.header}>
        <ProgressBar
          value={qIndex + 1}
          max={PLACEMENT_POOL.length}
          label={t('a11y.progressQuestion', { n: qIndex + 1, total: PLACEMENT_POOL.length })}
          color="var(--le-purple)"
          height={8}
        />
        <span className={styles.headerLabel}>{t('placement.questionOf', { n: qIndex + 1, total: PLACEMENT_POOL.length })}</span>
      </div>

      <div className={styles.abilityIndicator}>
        <span className={styles.abilityLabel}>{t('placement.estimatedLevel')}</span>
        <div className={styles.abilityBar}>
          <div className={styles.abilityFill} style={{ width: `${ability * 100}%` }} />
        </div>
      </div>

      <div className={styles.questionCard}>
        <h2 className={styles.questionText}>{question.text}</h2>
      </div>

      <div className={styles.options}>
        {question.options.map((opt, i) => {
          let cls = styles.option;
          if (answered) {
            if (i === question.correctIndex) cls += ` ${styles.correct}`;
            else if (i === selected) cls += ` ${styles.wrong}`;
          }
          return (
            <button key={i} className={cls} onClick={() => handleAnswer(i)} disabled={answered}>
              <span className={styles.optLetter}>{String.fromCharCode(65 + i)}</span>
              <span>{opt}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
