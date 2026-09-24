import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { duels as duelsApi, type DuelSummary, type DuelChallengeResponse, type QuestionPublic } from '../services/api';
import { showToast } from '../components/common/Toast';

type View = 'list' | 'challenge-modal' | 'playing' | 'result';

export function DuelScreen() {
  const language = useAppStore((s) => s.user.language);
  const currentUser = useAppStore((s) => s.user);
  const { t } = useTranslation();

  const [view, setView] = useState<View>('list');
  const [myDuels, setMyDuels] = useState<DuelSummary[]>([]);
  const [loading, setLoading] = useState(true);

  // Challenge modal
  const [opponent, setOpponent] = useState('');
  const [skillId, setSkillId] = useState('');
  const [challenging, setChallenging] = useState(false);

  // Playing a duel
  const [activeDuel, setActiveDuel] = useState<DuelChallengeResponse | null>(null);
  const [qIndex, setQIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [_answered, setAnswered] = useState<boolean[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [playingDuelId, setPlayingDuelId] = useState<string | null>(null);
  const questionStart = useState(() => Date.now())[0];

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

  // ── Challenge ─────────────────────────────────────────────────────────────
  const handleChallenge = async () => {
    if (!opponent.trim()) return;
    setChallenging(true);
    try {
      const res = await duelsApi.challenge({
        opponent_username: opponent.trim(),
        skill_id: skillId.trim() || undefined,
      });
      setActiveDuel(res);
      setQIndex(0);
      setSelected(null);
      setAnswered([]);
      setPlayingDuelId(res.duel_id);
      setView('playing');
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
      const res = await duelsApi.join(duel.duel_id);
      setActiveDuel(res);
      setQIndex(0);
      setSelected(null);
      setAnswered([]);
      setPlayingDuelId(res.duel_id);
      setView('playing');
    } catch (e) {
      showToast(e instanceof Error ? e.message : 'Error', 'error');
    }
  };

  // ── Answer ────────────────────────────────────────────────────────────────
  const handleAnswer = async (choice: number) => {
    if (!activeDuel || !playingDuelId || submitting || selected !== null) return;
    setSelected(choice);
    setSubmitting(true);
    const rt = Date.now() - questionStart;
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
    } else {
      setView('result');
      fetchDuels();
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  if (view === 'challenge-modal') {
    return (
      <div style={styles.container}>
        <div style={styles.modal}>
          <h2 style={styles.modalTitle}>{t('duel.challengeTitle')}</h2>
          <input
            style={styles.input}
            placeholder={t('duel.opponentPlaceholder')}
            value={opponent}
            onChange={(e) => setOpponent(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleChallenge()}
            autoFocus
          />
          <input
            style={styles.input}
            placeholder={t('duel.skillOptional')}
            value={skillId}
            onChange={(e) => setSkillId(e.target.value)}
          />
          <div style={styles.row}>
            <button style={styles.btnSecondary} onClick={() => setView('list')}>{t('duel.cancel')}</button>
            <button
              style={{...styles.btnPrimary, opacity: challenging ? 0.6 : 1}}
              onClick={handleChallenge}
              disabled={challenging || !opponent.trim()}
            >
              {challenging ? '...' : t('duel.send')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (view === 'playing' && activeDuel) {
    const q: QuestionPublic = activeDuel.questions[qIndex];
    const qText = language === 'en' ? q.question_en : q.question_es;
    const options = (language === 'en' ? q.options_en : q.options_es) ?? [];
    const isLast = qIndex === activeDuel.questions.length - 1;

    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <span style={styles.meta}>⚔️ vs {activeDuel.opponent_username}</span>
          <span style={styles.meta}>{t('duel.q')} {qIndex + 1} {t('duel.of')} {activeDuel.questions.length}</span>
        </div>

        <div style={styles.progressBar}>
          <div style={{...styles.progressFill, width: `${((qIndex + 1) / activeDuel.questions.length) * 100}%`}} />
        </div>

        <div style={styles.questionCard}>
          <p style={styles.questionText}>{qText}</p>
        </div>

        <div style={styles.options}>
          {options.map((opt, i) => (
            <button
              key={i}
              style={{
                ...styles.optionBtn,
                background: selected === i ? 'var(--le-brand)' : 'var(--le-surface)',
                color: selected === i ? '#fff' : 'var(--le-text)',
                borderColor: selected === i ? 'var(--le-brand)' : 'var(--le-border)',
              }}
              onClick={() => handleAnswer(i)}
              disabled={selected !== null || submitting}
            >
              {opt}
            </button>
          ))}
        </div>

        {selected !== null && (
          <button style={styles.btnPrimary} onClick={handleNext}>
            {isLast ? t('duel.finish') : t('duel.next')}
          </button>
        )}
      </div>
    );
  }

  if (view === 'result') {
    return (
      <div style={{...styles.container, justifyContent: 'center', textAlign: 'center', gap: 20}}>
        <div style={{fontSize: 72}}>⚔️</div>
        <h2 style={{color: 'var(--le-text)', fontSize: 22, fontWeight: 800}}>{t('duel.completed')}</h2>
        <p style={{color: 'var(--le-text-muted)', fontSize: 14}}>{t('duel.waitingResult')}</p>
        <p style={{color: 'var(--le-brand)', fontWeight: 700}}>{t('duel.participationXp')}</p>
        <button style={styles.btnPrimary} onClick={() => { setView('list'); fetchDuels(); }}>
          {t('duel.viewMyDuels')}
        </button>
      </div>
    );
  }

  // List view
  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>{t('duel.title')}</h1>
        <button style={{ ...styles.btnPrimary, flex: '0 0 auto' }} onClick={() => setView('challenge-modal')}>
          ⚔️ {t('duel.challenge')}
        </button>
      </div>

      {loading ? (
        <div style={{color: 'var(--le-text-muted)', padding: 32, textAlign: 'center'}}>{t('duel.loading')}</div>
      ) : myDuels.length === 0 ? (
        <div style={styles.empty}>
          <div style={{fontSize: 48}}>⚔️</div>
          <p style={{color: 'var(--le-text-muted)', marginTop: 12}}>{t('duel.noDuels')}</p>
        </div>
      ) : (
        <div style={styles.list}>
          {myDuels.map((duel) => (
            <DuelCard
              key={duel.duel_id}
              duel={duel}
              currentUserId={currentUser.id}
              onPlay={duel.is_your_turn ? () => { void joinDuel(duel); } : undefined}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function DuelCard({
  duel,
  currentUserId,
  onPlay,
}: {
  duel: DuelSummary;
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
    <div style={styles.card}>
      <div style={styles.cardLeft}>
        <span style={{fontSize: 28}}>{duel.opponent_avatar}</span>
        <div>
          <div style={{fontWeight: 700, color: 'var(--le-text)', fontSize: 15}}>
            {duel.opponent_username}
          </div>
          <div style={{fontSize: 12, color: 'var(--le-text-muted)'}}>
            {duel.skill_id} · {statusLabel}
          </div>
        </div>
      </div>
      <div style={styles.cardRight}>
        {duel.status === 'completed' ? (
          <span style={{
            fontWeight: 800, fontSize: 13,
            color: isDraw ? 'var(--le-orange)' : isWinner ? 'var(--le-green)' : 'var(--le-red)',
          }}>
            {isDraw ? t('duel.draw') : isWinner ? t('duel.won') : t('duel.lost')}
            {!isDraw && duel.your_correct !== null && ` (${duel.your_correct}/5)`}
          </span>
        ) : duel.is_your_turn ? (
          <button style={{...styles.btnPrimary, padding: '6px 14px', fontSize: 13}} onClick={onPlay}>
            {t('duel.play')}
          </button>
        ) : (
          <span style={{color: 'var(--le-text-muted)', fontSize: 12}}>{t('duel.waiting')}</span>
        )}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100%',
    padding: '16px 16px 90px',
    gap: 16,
    background: 'var(--le-bg)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  title: {
    fontSize: 22,
    fontWeight: 800,
    color: 'var(--le-text)',
    margin: 0,
  },
  meta: {
    fontSize: 13,
    color: 'var(--le-text-muted)',
    fontWeight: 600,
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
    background: 'var(--le-border)',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    background: 'var(--le-brand)',
    borderRadius: 3,
    transition: 'width 0.3s ease',
  },
  questionCard: {
    background: 'var(--le-surface)',
    borderRadius: 16,
    padding: '20px 16px',
    border: '1.5px solid var(--le-border)',
  },
  questionText: {
    fontSize: 16,
    fontWeight: 600,
    color: 'var(--le-text)',
    lineHeight: 1.5,
    margin: 0,
  },
  options: {
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  optionBtn: {
    padding: '14px 16px',
    borderRadius: 12,
    border: '1.5px solid',
    fontSize: 15,
    fontWeight: 600,
    textAlign: 'left',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  card: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    background: 'var(--le-surface)',
    borderRadius: 14,
    padding: '14px 16px',
    border: '1.5px solid var(--le-border)',
  },
  cardLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  cardRight: {
    display: 'flex',
    alignItems: 'center',
  },
  empty: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 80,
  },
  modal: {
    background: 'var(--le-surface)',
    borderRadius: 20,
    padding: '28px 20px',
    border: '1.5px solid var(--le-border)',
    display: 'flex',
    flexDirection: 'column',
    gap: 14,
    marginTop: 40,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 800,
    color: 'var(--le-text)',
    margin: 0,
    textAlign: 'center',
  },
  input: {
    padding: '12px 14px',
    borderRadius: 10,
    border: '1.5px solid var(--le-border)',
    fontSize: 15,
    background: 'var(--le-bg)',
    color: 'var(--le-text)',
    outline: 'none',
  },
  row: {
    display: 'flex',
    gap: 10,
  },
  btnPrimary: {
    flex: 1,
    padding: '13px 20px',
    borderRadius: 12,
    border: 'none',
    background: 'var(--le-brand)',
    color: 'var(--le-text-inverse)',
    fontSize: 15,
    fontWeight: 700,
    cursor: 'pointer',
    transition: 'opacity 0.15s',
  },
  btnSecondary: {
    flex: 1,
    padding: '13px 20px',
    borderRadius: 12,
    border: '1.5px solid var(--le-border)',
    background: 'transparent',
    color: 'var(--le-text)',
    fontSize: 15,
    fontWeight: 600,
    cursor: 'pointer',
  },
};
