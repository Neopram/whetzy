import { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, useReducedMotion } from 'framer-motion';
import { DUR } from '../lib/motion';
import { emit as emitFx } from '../lib/feedbackFx';
import { useAppStore } from '../stores/useAppStore';
import { useApi } from '../hooks/useApi';
import { Button } from '../components/common/Button';
import {
  duels as duelsApi,
  progress as progressApi,
  type DuelSummary,
  type DuelAnswerResponse,
  type DuelChallengeResponse,
  type DuelResultResponse,
  type DuelRivalAnswer,
  type QuestionPublic,
} from '../services/api';
import { parseQuestion } from '../lib/question';
import { showToast } from '../components/common/Toast';
import { RankingTabs } from '../components/layout/RankingTabs';
import styles from './DuelScreen.module.css';
import { Loading } from '../components/common/Loading';
import { ErrorState } from '../components/common/ErrorState';

type View = 'list' | 'challenge-modal' | 'playing' | 'result';

export function DuelScreen() {
  const language = useAppStore((s) => s.user.language);
  const currentUser = useAppStore((s) => s.user);
  const { t } = useTranslation();

  const [view, setView] = useState<View>('list');
  const [myDuels, setMyDuels] = useState<DuelSummary[]>([]);
  const [loading, setLoading] = useState(true);
  // Revisión de UI del 2026-10-23: un fallo de red salía como «no tienes duelos».
  const [loadFailed, setLoadFailed] = useState(false);
  // Nombres de habilidad: el duelo solo trae `skill_id`, y la lista enseñaba
  // «sk010102» tal cual (auditoría).
  const skills = useApi(() => progressApi.skills(), []);
  const skillName = (id: string) => {
    const s = skills.data?.find((x) => x.skill_id === id);
    return s ? (language === 'en' ? s.name_en : s.name_es) : null;
  };
  const practised = (skills.data ?? []).filter((s) => s.attempts > 0);

  // Challenge modal
  const [opponent, setOpponent] = useState('');
  const [skillId, setSkillId] = useState('');
  const [challenging, setChallenging] = useState(false);

  // Playing a duel
  const [activeDuel, setActiveDuel] = useState<DuelChallengeResponse | null>(null);
  const [qIndex, setQIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [playingDuelId, setPlayingDuelId] = useState<string | null>(null);
  const [duelResult, setDuelResult] = useState<DuelResultResponse | null>(null);
  // Partida grabada: si el rival ya jugó, tras cada respuesta se ve cómo le fue
  // a él en esa misma pregunta. Lo decide el servidor (`rival` solo llega
  // cuando el otro terminó); aquí no se adivina nada.
  const [rival, setRival] = useState<DuelRivalAnswer | null>(null);
  // 42.4: tras contestar, si acertó, cuál era la buena y por qué.
  const [feedback, setFeedback] = useState<DuelAnswerResponse | null>(null);
  // Se reinicia con cada pregunta: antes se fijaba al montar la pantalla y el
  // tiempo de respuesta que llega al motor crecía pregunta a pregunta.
  const questionStart = useRef(Date.now());

  const fetchDuels = useCallback(async () => {
    try {
      const data = await duelsApi.my();
      setMyDuels(data);
      setLoadFailed(false);
    } catch {
      setLoadFailed(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDuels();
  }, [fetchDuels]);

  const startPlaying = (res: DuelChallengeResponse) => {
    // 42.5: quien vuelve a un duelo a medias sigue por la primera sin contestar.
    const answered = new Set(res.answered_question_ids ?? []);
    const next = res.questions.findIndex((x) => !answered.has(x.id));
    setActiveDuel(res);
    setQIndex(next === -1 ? 0 : next);
    setSelected(null);
    setRival(null);
    setFeedback(null);
    setPlayingDuelId(res.duel_id);
    questionStart.current = Date.now();
    setView('playing');
  };

  // ── Challenge ─────────────────────────────────────────────────────────────
  const handleChallenge = async () => {
    if (!opponent.trim()) return;
    setChallenging(true);
    try {
      const res = await duelsApi.challenge({
        opponent_username: opponent.trim(),
        skill_id: skillId || undefined,
      });
      startPlaying(res);
      showToast(t('duel.challengeSent', { username: res.opponent_username }), 'success');
    } catch (e) {
      showToast(e instanceof Error ? e.message : 'Error', 'error');
    } finally {
      setChallenging(false);
    }
  };

  // ── Playing: join existing duel ───────────────────────────────────────────
  const joinDuel = async (duel: DuelSummary) => {
    try {
      startPlaying(await duelsApi.join(duel.duel_id));
    } catch (e) {
      showToast(e instanceof Error ? e.message : 'Error', 'error');
    }
  };

  // ── Answer ────────────────────────────────────────────────────────────────
  const handleAnswer = async (choice: number) => {
    if (!activeDuel || !playingDuelId || submitting || selected !== null) return;
    setSelected(choice);
    setSubmitting(true);
    const rt = Date.now() - questionStart.current;
    const q = activeDuel.questions[qIndex];
    try {
      const res = await duelsApi.answer(playingDuelId, {
        question_id: q.id,
        selected_index: choice,
        response_time_ms: rt,
      });
      setRival(res.rival ?? null);
      setFeedback(res);
    } catch {
      /* continue anyway */
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    if (!activeDuel) return;
    if (qIndex + 1 < activeDuel.questions.length) {
      setQIndex((i) => i + 1);
      setSelected(null);
      setRival(null);
      setFeedback(null);
      questionStart.current = Date.now();
    } else {
      setDuelResult(null);
      setView('result');
      fetchDuels();
      // Try to fetch the result immediately; 202 means opponent hasn't finished.
      if (playingDuelId) {
        duelsApi.result(playingDuelId).then(setDuelResult).catch(() => { /* 202 or network */ });
      }
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  // 46.15 C: el resultado del servidor cierra la sesión (nivel 3), una vez.
  const reduce = useReducedMotion();
  useEffect(() => {
    if (duelResult) emitFx({ type: 'session_end' });
  }, [duelResult]);

  if (view === 'challenge-modal') {
    return (
      <div className={styles.screen}>
        <section className={styles.panel} aria-labelledby="duel-new">
          <h1 id="duel-new" className={styles.title}>{t('duel.challengeTitle')}</h1>
          <label className={styles.field}>
            <span>{t('duel.opponentLabel')}</span>
            <input
              className={styles.input}
              placeholder={t('duel.opponentPlaceholder')}
              value={opponent}
              onChange={(e) => setOpponent(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleChallenge()}
              autoFocus
              autoComplete="off"
            />
          </label>
          <label className={styles.field}>
            <span>{t('duel.skillLabel')}</span>
            <select className={styles.input} value={skillId} onChange={(e) => setSkillId(e.target.value)}>
              <option value="">{t('duel.anySkill')}</option>
              {practised.map((s) => (
                <option key={s.skill_id} value={s.skill_id}>{language === 'en' ? s.name_en : s.name_es}</option>
              ))}
            </select>
          </label>
          <div className={styles.row}>
            <Button type="button" variant="ghost" onClick={() => setView('list')}>{t('duel.cancel')}</Button>
            <Button
              type="button"
              onClick={handleChallenge}
              disabled={challenging || !opponent.trim()}
            >
              {challenging ? t('duel.sending') : t('duel.send')}
            </Button>
          </div>
        </section>
      </div>
    );
  }

  if (view === 'playing' && activeDuel) {
    const q: QuestionPublic = activeDuel.questions[qIndex];
    const { prose, code } = parseQuestion(language === 'en' ? q.question_en : q.question_es);
    const options = (language === 'en' ? q.options_en : q.options_es) ?? [];
    const isLast = qIndex === activeDuel.questions.length - 1;

    return (
      <div className={styles.screen}>
        <div className={styles.playHead}>
          <span className={styles.vs}>{t('duel.vs', { username: activeDuel.opponent_username })}</span>
          <span className={styles.counter}>{t('duel.q')} {qIndex + 1} {t('duel.of')} {activeDuel.questions.length}</span>
        </div>
        <div className={styles.progress} aria-hidden="true">
          <span style={{ width: `${((qIndex + 1) / activeDuel.questions.length) * 100}%` }} />
        </div>

        <div className={styles.questionCard}>
          <p className={styles.questionText}>{prose}</p>
          {code && <pre className={styles.code} tabIndex={0}><code>{code}</code></pre>}
        </div>

        {/* e2e/duel.spec.ts responde por `duel-option`: «el primer botón de la
            vista» dejó de ser una opción con la franja de 45.3 en el armazón. */}
        <div className={styles.options}>
          {options.map((opt, i) => (
            <button
              key={i}
              type="button"
              data-testid="duel-option"
              className={`${styles.option} ${selected === i ? styles.optionSelected : ''} ${
                feedback?.correct_index === i ? styles.optionCorrect : ''
              }`}
              onClick={() => handleAnswer(i)}
              disabled={selected !== null || submitting}
            >
              <span className={styles.letter} aria-hidden="true">{String.fromCharCode(65 + i)}</span>
              <span>{opt}</span>
            </button>
          ))}
        </div>

        {/* Una sola región viva: el veredicto, la explicación y, si el rival ya
            jugó, cómo le fue en esta pregunta (42.4). */}
        {(feedback || rival) && (
          <div className={styles.feedback} role="status" data-testid="duel-feedback">
            {feedback && (
              <p className={feedback.correct ? styles.won : styles.lost}>
                {t(feedback.correct ? 'duel.youGotIt' : 'duel.youMissedIt')}
              </p>
            )}
            {feedback && (language === 'en' ? feedback.explanation_en : feedback.explanation_es) && (
              <p className={styles.muted}>
                {language === 'en' ? feedback.explanation_en : feedback.explanation_es}
              </p>
            )}
            {rival && (
              <p className={styles.rival} data-testid="duel-rival">
                <span className={rival.correct ? styles.won : styles.lost} aria-hidden="true">
                  {rival.correct ? '✓' : '✗'}
                </span>{' '}
                {t(rival.correct ? 'duel.rivalCorrect' : 'duel.rivalWrong', {
                  username: activeDuel.opponent_username,
                  s: (rival.response_time_ms / 1000).toLocaleString(language, { maximumFractionDigits: 1 }),
                })}
              </p>
            )}
          </div>
        )}

        {selected !== null && (
          <Button type="button" onClick={handleNext}>
            {isLast ? t('duel.finish') : t('duel.next')}
          </Button>
        )}
      </div>
    );
  }

  if (view === 'result') {
    const weakSkillName = duelResult?.weak_skill_id ? skillName(duelResult.weak_skill_id) : null;
    return (
      <div className={`${styles.screen} ${styles.centered}`}>
        <h1 className={styles.title}>{t('duel.completed')}</h1>
        {duelResult ? (
          <>
            <motion.p
              className={styles.resultOutcome}
              data-fx={reduce ? undefined : 'reveal'}
              initial={reduce ? false : { opacity: 0, scale: 0.94 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: DUR.response }}
            >
              {duelResult.is_draw
                ? t('duel.draw')
                : duelResult.winner_id === currentUser.id
                  ? t('duel.won')
                  : t('duel.lost')}
            </motion.p>
            {duelResult.weak_skill_id && (
              <p className={styles.practiceHint}>
                {t('duel.practiceHint', { skill: weakSkillName ?? duelResult.weak_skill_id })}
              </p>
            )}
          </>
        ) : (
          <p className={styles.muted}>{t('duel.waitingResult')}</p>
        )}
        <Button type="button" onClick={() => { setView('list'); fetchDuels(); }}>
          {t('duel.viewMyDuels')}
        </Button>
      </div>
    );
  }

  // List view
  return (
    <div className={styles.screen}>
      <RankingTabs />
      <div className={styles.listHead}>
        <h1 className={styles.title}>{t('duel.title')}</h1>
        <Button type="button" onClick={() => setView('challenge-modal')}>
          {t('duel.challenge')}
        </Button>
      </div>

      {loading ? (
        <Loading label={t('duel.loading')} shape="list" />
      ) : loadFailed ? (
        <ErrorState
          message={t('common.loadError')}
          onRetry={() => { setLoading(true); void fetchDuels(); }}
        />
      ) : myDuels.length === 0 ? (
        <p className={styles.empty}>{t('duel.noDuels')}</p>
      ) : (
        <ul className={styles.list}>
          {myDuels.map((duel) => (
            <DuelCard
              key={duel.duel_id}
              duel={duel}
              skill={skillName(duel.skill_id)}
              currentUserId={currentUser.id}
              onPlay={duel.is_your_turn ? () => { void joinDuel(duel); } : undefined}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

function DuelCard({
  duel,
  skill,
  currentUserId,
  onPlay,
}: {
  duel: DuelSummary;
  skill: string | null;
  currentUserId: string;
  onPlay?: () => void;
}) {
  const { t } = useTranslation();
  const isWinner = duel.winner_id === currentUserId;
  const isDraw = duel.status === 'completed' && !duel.winner_id;

  const statusLabel =
    duel.status === 'pending' ? t('duel.status_pending')
    : duel.status === 'in_progress' ? t('duel.status_in_progress')
    : duel.status === 'expired' ? t('duel.status_expired')
    : t('duel.status_completed');

  return (
    <li className={styles.card}>
      <span className={styles.avatar} aria-hidden="true">{duel.opponent_avatar}</span>
      <span className={styles.cardBody}>
        <span className={styles.opponent}>{duel.opponent_username}</span>
        <span className={styles.cardMeta}>{skill ? `${skill} · ` : ''}{statusLabel}</span>
      </span>
      {duel.status === 'completed' ? (
        <span className={`${styles.outcome} ${isWinner ? styles.won : ''}`}>
          {isDraw ? t('duel.draw') : isWinner ? t('duel.won') : t('duel.lost')}
          {!isDraw && duel.your_correct !== null && <b> {duel.your_correct}/5</b>}
        </span>
      ) : duel.is_your_turn ? (
        <Button type="button" variant="secondary" size="sm" onClick={onPlay}>{t('duel.play')}</Button>
      ) : (
        <span className={styles.cardMeta}>{t('duel.waiting')}</span>
      )}
    </li>
  );
}
