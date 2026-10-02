import { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { useApi } from '../hooks/useApi';
import {
  duels as duelsApi,
  progress as progressApi,
  type DuelSummary,
  type DuelChallengeResponse,
  type QuestionPublic,
} from '../services/api';
import { parseQuestion } from '../lib/question';
import { showToast } from '../components/common/Toast';
import { RankingTabs } from '../components/layout/RankingTabs';
import styles from './DuelScreen.module.css';

type View = 'list' | 'challenge-modal' | 'playing' | 'result';

export function DuelScreen() {
  const language = useAppStore((s) => s.user.language);
  const currentUser = useAppStore((s) => s.user);
  const { t } = useTranslation();

  const [view, setView] = useState<View>('list');
  const [myDuels, setMyDuels] = useState<DuelSummary[]>([]);
  const [loading, setLoading] = useState(true);
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
  // Se reinicia con cada pregunta: antes se fijaba al montar la pantalla y el
  // tiempo de respuesta que llega al motor crecía pregunta a pregunta.
  const questionStart = useRef(Date.now());

  const fetchDuels = useCallback(async () => {
    try {
      const data = await duelsApi.my();
      setMyDuels(data);
    } catch {
      /* silently skip */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDuels();
  }, [fetchDuels]);

  const startPlaying = (res: DuelChallengeResponse) => {
    setActiveDuel(res);
    setQIndex(0);
    setSelected(null);
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
      await duelsApi.answer(playingDuelId, {
        question_id: q.id,
        selected_index: choice,
        response_time_ms: rt,
      });
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
      questionStart.current = Date.now();
    } else {
      setView('result');
      fetchDuels();
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
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
            <button type="button" className={styles.btnSecondary} onClick={() => setView('list')}>{t('duel.cancel')}</button>
            <button
              type="button"
              className={styles.btnPrimary}
              onClick={handleChallenge}
              disabled={challenging || !opponent.trim()}
            >
              {challenging ? t('duel.sending') : t('duel.send')}
            </button>
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
          {code && <pre className={styles.code}><code>{code}</code></pre>}
        </div>

        {/* Ningún botón antes de las opciones: la primera opción es el primer
            botón de la vista (e2e/duel.spec.ts responde así). */}
        <div className={styles.options}>
          {options.map((opt, i) => (
            <button
              key={i}
              type="button"
              className={`${styles.option} ${selected === i ? styles.optionSelected : ''}`}
              onClick={() => handleAnswer(i)}
              disabled={selected !== null || submitting}
            >
              <span className={styles.letter} aria-hidden="true">{String.fromCharCode(65 + i)}</span>
              <span>{opt}</span>
            </button>
          ))}
        </div>

        {selected !== null && (
          <button type="button" className={styles.btnPrimary} onClick={handleNext}>
            {isLast ? t('duel.finish') : t('duel.next')}
          </button>
        )}
      </div>
    );
  }

  if (view === 'result') {
    return (
      <div className={`${styles.screen} ${styles.centered}`}>
        <h1 className={styles.title}>{t('duel.completed')}</h1>
        <p className={styles.muted}>{t('duel.waitingResult')}</p>
        <button type="button" className={styles.btnPrimary} onClick={() => { setView('list'); fetchDuels(); }}>
          {t('duel.viewMyDuels')}
        </button>
      </div>
    );
  }

  // List view
  return (
    <div className={styles.screen}>
      <RankingTabs />
      <div className={styles.listHead}>
        <h1 className={styles.title}>{t('duel.title')}</h1>
        <button type="button" className={styles.btnPrimary} onClick={() => setView('challenge-modal')}>
          {t('duel.challenge')}
        </button>
      </div>

      {loading ? (
        <p className={styles.muted} role="status">{t('duel.loading')}</p>
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
        <button type="button" className={styles.btnPlay} onClick={onPlay}>{t('duel.play')}</button>
      ) : (
        <span className={styles.cardMeta}>{t('duel.waiting')}</span>
      )}
    </li>
  );
}
