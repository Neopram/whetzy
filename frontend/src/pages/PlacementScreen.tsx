import { useState, useCallback } from 'react';
import { useAppStore } from '../stores/useAppStore';
import { ProgressBar } from '../components/common/ProgressBar';
import styles from './PlacementScreen.module.css';

interface PlacementQuestion {
  text: string;
  code?: string;
  options: string[];
  correctIndex: number;
  difficulty: number;
}

const PLACEMENT_POOL: PlacementQuestion[] = [
  { text: 'Que funcion se usa para imprimir en consola?', options: ['print()', 'echo()', 'log()', 'write()'], correctIndex: 0, difficulty: 0.1 },
  { text: 'Cual es el tipo de dato de True?', options: ['bool', 'int', 'str', 'bit'], correctIndex: 0, difficulty: 0.15 },
  { text: 'Como se declara una lista vacia?', options: ['[]', '{}', '()', 'list{}'], correctIndex: 0, difficulty: 0.2 },
  { text: 'Que retorna len("Python")?', options: ['6', '5', '7', 'Error'], correctIndex: 0, difficulty: 0.25 },
  { text: 'Cual operador se usa para exponenciacion?', options: ['**', '^', 'pow', '//'], correctIndex: 0, difficulty: 0.3 },
  { text: 'Que keyword inicia un loop definido?', options: ['for', 'loop', 'each', 'iterate'], correctIndex: 0, difficulty: 0.35 },
  { text: 'Que es self en una clase?', options: ['Referencia a la instancia', 'Variable global', 'Keyword reservado', 'Tipo de dato'], correctIndex: 0, difficulty: 0.5 },
  { text: 'Cual es la diferencia entre append() y extend()?', options: ['append agrega un elemento, extend agrega iterables', 'Son identicos', 'extend solo funciona con listas', 'append es mas rapido'], correctIndex: 0, difficulty: 0.55 },
  { text: 'Que patron implementa un context manager?', options: ['__enter__ y __exit__', 'open y close', 'start y stop', '__init__ y __del__'], correctIndex: 0, difficulty: 0.7 },
  { text: 'Que es un descriptor en Python?', options: ['Objeto con __get__, __set__, o __delete__', 'Una clase abstracta', 'Un tipo de variable', 'Un decorador especial'], correctIndex: 0, difficulty: 0.85 },
];

export function PlacementScreen() {
  const setScreen = useAppStore((s) => s.setScreen);
  const [phase, setPhase] = useState<'intro' | 'testing' | 'result'>('intro');
  const [qIndex, setQIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [answered, setAnswered] = useState(false);
  const [correct, setCorrect] = useState(0);
  const [total, setTotal] = useState(0);
  const [ability, setAbility] = useState(0.5);

  const question = PLACEMENT_POOL[qIndex % PLACEMENT_POOL.length];

  const handleAnswer = useCallback(
    (index: number) => {
      if (answered) return;
      setSelected(index);
      setAnswered(true);
      const isCorrect = index === question.correctIndex;
      if (isCorrect) setCorrect((c) => c + 1);
      setTotal((t) => t + 1);

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
        <h1 className={styles.introTitle}>Examen de Colocacion</h1>
        <p className={styles.introDesc}>
          Evaluaremos tu nivel actual de Python con preguntas adaptativas.
          Las preguntas se ajustan automaticamente a tu nivel.
        </p>
        <div className={styles.introFeatures}>
          <div className={styles.introFeature}>
            <span>🧠</span>
            <span>Algoritmo adaptativo (BanditCAT)</span>
          </div>
          <div className={styles.introFeature}>
            <span>⏱️</span>
            <span>~15 minutos estimados</span>
          </div>
          <div className={styles.introFeature}>
            <span>🎯</span>
            <span>70% para saltar modulos</span>
          </div>
        </div>
        <button className={styles.startBtn} onClick={() => setPhase('testing')}>
          COMENZAR EXAMEN
        </button>
        <button className={styles.skipBtn} onClick={() => setScreen('home')}>
          Volver al inicio
        </button>
      </div>
    );
  }

  if (phase === 'result') {
    const pct = total > 0 ? Math.round((correct / total) * 100) : 0;
    const level =
      pct >= 85 ? 'Avanzado' : pct >= 70 ? 'Intermedio-Alto' : pct >= 50 ? 'Intermedio' : pct >= 30 ? 'Basico' : 'Principiante';

    return (
      <div className={styles.result}>
        <span className={styles.resultIcon}>
          {pct >= 70 ? '🏆' : pct >= 50 ? '💪' : '📚'}
        </span>
        <h1 className={styles.resultTitle}>Nivel: {level}</h1>
        <p className={styles.resultPct}>{pct}% de precision ({correct}/{total})</p>
        <div className={styles.resultBar}>
          <ProgressBar value={pct} max={100} color="var(--le-green)" height={16} showLabel />
        </div>
        <p className={styles.resultDesc}>
          {pct >= 70
            ? 'Puedes saltar los modulos basicos e ir directo a contenido avanzado.'
            : 'Hemos personalizado tu ruta de aprendizaje basado en tus resultados.'}
        </p>
        <button className={styles.startBtn} onClick={() => setScreen('home')}>
          COMENZAR A APRENDER
        </button>
      </div>
    );
  }

  return (
    <div className={styles.screen}>
      <div className={styles.header}>
        <ProgressBar value={qIndex + 1} max={PLACEMENT_POOL.length} color="var(--le-purple)" height={8} />
        <span className={styles.headerLabel}>Pregunta {qIndex + 1} de {PLACEMENT_POOL.length}</span>
      </div>

      <div className={styles.abilityIndicator}>
        <span className={styles.abilityLabel}>Nivel estimado</span>
        <div className={styles.abilityBar}>
          <div className={styles.abilityFill} style={{ width: `${ability * 100}%` }} />
        </div>
      </div>

      <div className={styles.questionCard}>
        <h2 className={styles.questionText}>{question.text}</h2>
        {question.code && <pre className={styles.codeBlock}><code>{question.code}</code></pre>}
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
