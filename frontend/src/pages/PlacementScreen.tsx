import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { ProgressBar } from '../components/common/ProgressBar';
import {
  placement as placementApi,
  type PlacementResult,
  type QuestionPublic,
} from '../services/api';
import { parseQuestion, splitInlineCode } from '../lib/question';
import styles from './PlacementScreen.module.css';

/**
 * Prueba de nivel adaptativa.
 *
 * Antes esta pantalla llevaba diez preguntas escritas en los ficheros de idioma
 * y calculaba el nivel ella sola con `ability + (acierto ? 0.05 : -0.03)`: un
 * numero inventado que no media nada y que no llegaba al servidor. El motor CAT
 * con IRT existia desde el principio en `app/services/engine/placement.py`,
 * elige cada pregunta segun lo que ya sabe del alumno, para cuando la
 * estimacion se estabiliza y dice **que modulos puede saltarse**. Nada de eso
 * se estaba usando.
 *
 * Ahora la pantalla no calcula: pregunta, muestra y se aparta.
 */

/** El motor devuelve theta en logits (~-3..3); la barra necesita 0..1. */
function thetaAPorcentaje(theta: number): number {
  return Math.round(Math.max(0, Math.min(1, (theta + 3) / 6)) * 100);
}

interface Props {
  trackId: string;
}

export function PlacementScreen({ trackId }: Props) {
  const setScreen = useAppStore((s) => s.setScreen);
  const lang = useAppStore((s) => s.user.language);
  const { t } = useTranslation();

  const [fase, setFase] = useState<'intro' | 'cargando' | 'test' | 'resultado' | 'error'>('intro');
  const [fallo, setFallo] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [pregunta, setPregunta] = useState<QuestionPublic | null>(null);
  const [respondidas, setRespondidas] = useState(0);
  const [theta, setTheta] = useState(0);
  const [seleccion, setSeleccion] = useState<number | null>(null);
  const [acierto, setAcierto] = useState<boolean | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [resultado, setResultado] = useState<PlacementResult | null>(null);

  // El motor guarda el tiempo de respuesta con cada item, asi que se mide desde
  // que la pregunta aparece, no desde que arranca la sesion.
  const mostradaEn = useRef<number>(Date.now());
  useEffect(() => { mostradaEn.current = Date.now(); }, [pregunta?.id]);

  // Muchas preguntas del banco traen el codigo dentro del texto, cercado
  // con ```. Sin separarlo se ven las comillas y el nombre del lenguaje, y
  // el codigo queda en una sola linea sin monoespaciada.
  const { prose: enunciado, code: codigo } = parseQuestion(
    pregunta ? (lang === 'en' ? pregunta.question_en : pregunta.question_es) : ''
  );
  const opciones = pregunta
    ? ((lang === 'en' ? pregunta.options_en : pregunta.options_es) ?? [])
    : [];

  const empezar = useCallback(async () => {
    setFase('cargando');
    setFallo(null);
    try {
      const r = await placementApi.start(trackId);
      setSessionId(r.session_id);
      setPregunta(r.question);
      setRespondidas(r.questions_answered);
      setFase(r.question ? 'test' : 'error');
      if (!r.question) setFallo(t('placement.noItems'));
    } catch (err) {
      setFallo(err instanceof Error ? err.message : t('placement.errorStart'));
      setFase('error');
    }
  }, [trackId, t]);

  const responder = useCallback(
    async (indice: number) => {
      if (enviando || seleccion !== null || !sessionId || !pregunta) return;
      setSeleccion(indice);
      setEnviando(true);
      try {
        const r = await placementApi.answer(
          sessionId, pregunta.id, indice, Date.now() - mostradaEn.current
        );
        setAcierto(r.correct);
        setTheta(r.ability_estimate);
        setRespondidas(r.questions_answered);

        // Un respiro para ver si se acerto antes de pasar; el motor ya tiene la
        // siguiente pregunta elegida, no hay espera de red aqui.
        setTimeout(async () => {
          if (r.finished || !r.next_question) {
            try {
              setResultado(await placementApi.result(sessionId));
              setFase('resultado');
            } catch (err) {
              setFallo(err instanceof Error ? err.message : t('placement.errorResult'));
              setFase('error');
            }
            return;
          }
          setPregunta(r.next_question);
          setSeleccion(null);
          setAcierto(null);
          setEnviando(false);
        }, 700);
      } catch (err) {
        setFallo(err instanceof Error ? err.message : t('placement.errorAnswer'));
        setFase('error');
      }
    },
    [enviando, seleccion, sessionId, pregunta, t]
  );

  if (fase === 'intro') {
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
        <button className={styles.startBtn} onClick={empezar}>{t('placement.start')}</button>
        <button className={styles.skipBtn} onClick={() => setScreen('tracks')}>
          {t('placement.skip')}
        </button>
      </div>
    );
  }

  if (fase === 'cargando') {
    return <div className={styles.intro}><p>{t('common.loading')}</p></div>;
  }

  if (fase === 'error') {
    return (
      <div className={styles.intro}>
        <span className={styles.introIcon}>⚠️</span>
        <p className={styles.introDesc} role="alert">{fallo}</p>
        <button className={styles.skipBtn} onClick={() => setScreen('tracks')}>
          {t('placement.skip')}
        </button>
      </div>
    );
  }

  if (fase === 'resultado' && resultado) {
    const pct = Math.round(resultado.accuracy * 100);
    const saltables = resultado.module_recommendations.filter((m) => m.can_skip);
    // `reliability` baja cuando el motor se quedo sin preguntas antes de
    // estabilizar la estimacion. Decirlo es mas honesto que enseñar un nivel
    // con la misma confianza en los dos casos.
    const pocoFiable = resultado.reliability < 0.7;

    return (
      <div className={styles.result}>
        <span className={styles.resultIcon}>{pct >= 70 ? '🏆' : pct >= 50 ? '💪' : '📚'}</span>
        <h1 className={styles.resultTitle}>
          {t('placement.abilityResult', { pct: thetaAPorcentaje(resultado.ability_estimate) })}
        </h1>
        <p className={styles.resultPct}>
          {t('placement.pctAccuracy', { pct, correct: resultado.correct, total: resultado.total_questions })}
        </p>
        <div className={styles.resultBar}>
          <ProgressBar
            value={thetaAPorcentaje(resultado.ability_estimate)}
            max={100}
            label={t('a11y.progressScore', { pct: thetaAPorcentaje(resultado.ability_estimate) })}
            color="var(--le-green)"
            height={16}
            showLabel
          />
        </div>

        {pocoFiable && (
          <p className={styles.resultDesc}>
            {t('placement.lowReliability', { pct: Math.round(resultado.reliability * 100) })}
          </p>
        )}

        {saltables.length > 0 ? (
          <>
            <p className={styles.resultDesc}>
              {t('placement.canSkipCount', { count: saltables.length })}
            </p>
            {/* El porqué del salto (35.2). Umbral y mínimo son los de
                backend/app/services/engine/placement.py; los vigila
                backend/tests/test_placement_regla_visible.py. */}
            <p className={styles.resultDesc}>{t('placement.skipRule', { pct: 70, min: 8 })}</p>
            <ul className={styles.skipList}>
              {saltables.map((m) => (
                <li key={m.module_id} className={styles.skipItem}>
                  <span>{lang === 'en' ? m.module_name_en : m.module_name_es}</span>
                  <span className={styles.skipPct}>
                    {t('placement.skipCorrect', { correct: Math.round(m.accuracy * m.questions_seen), total: m.questions_seen })}
                    {' · '}{Math.round(m.accuracy * 100)}%
                  </span>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p className={styles.resultDesc}>{t('placement.noSkips')}</p>
        )}

        <button className={styles.startBtn} onClick={() => setScreen('tracks')}>
          {t('placement.startLearning')}
        </button>
      </div>
    );
  }

  // fase === 'test'
  return (
    <div className={styles.screen}>
      <div className={styles.header}>
        {/* El CAT no tiene un total fijo: para cuando la estimacion se
            estabiliza. Se enseña cuantas van, no una barra que miente. */}
        <span className={styles.headerLabel}>
          {t('placement.answered', { n: respondidas })}
        </span>
      </div>

      <div className={styles.abilityIndicator}>
        <span className={styles.abilityLabel}>{t('placement.estimatedLevel')}</span>
        <div className={styles.abilityBar}>
          <div
            className={styles.abilityFill}
            style={{ width: `${thetaAPorcentaje(theta)}%` }}
          />
        </div>
      </div>

      <div className={styles.questionCard}>
        <h2 className={styles.questionText}>
          {/* Las comillas simples nombran codigo dentro de la frase; sin esto
              el alumno las lee como parte de la respuesta. */}
          {splitInlineCode(enunciado).map((t, i) =>
            t.code ? (
              <code key={i} className={styles.inlineCode}>{t.text}</code>
            ) : (
              <span key={i}>{t.text}</span>
            )
          )}
        </h2>
        {codigo && <pre className={styles.codeBlock}><code>{codigo}</code></pre>}
      </div>

      <div className={styles.options}>
        {opciones.map((opt, i) => {
          let cls = styles.option;
          if (seleccion !== null && i === seleccion) {
            cls += acierto ? ` ${styles.correct}` : ` ${styles.wrong}`;
          }
          return (
            <button
              key={i}
              className={cls}
              onClick={() => responder(i)}
              disabled={seleccion !== null}
            >
              <span className={styles.optLetter}>{String.fromCharCode(65 + i)}</span>
              <span>{opt}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
