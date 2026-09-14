import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { ProgressBar } from '../components/common/ProgressBar';
import { Card } from '../components/common/Card';
import { useApi } from '../hooks/useApi';
import { progress as progressApi, gamification } from '../services/api';
import styles from './HomeScreen.module.css';

function getTimeOfDay(lang: 'es' | 'en'): string {
  const h = new Date().getHours();
  if (lang === 'en') return h < 12 ? 'morning' : h < 19 ? 'afternoon' : 'evening';
  return h < 12 ? 'días' : h < 19 ? 'tardes' : 'noches';
}

export function HomeScreen() {
  const user = useAppStore((s) => s.user);
  const startQuiz = useAppStore((s) => s.startQuiz);
  const lang = user.language;
  const { t } = useTranslation();

  const dash = useApi(() => progressApi.dashboard(), []);
  const missions = useApi(() => gamification.missions(), []);
  const decaying = useApi(() => progressApi.decaying(), []);

  const overallMastery = dash.data
    ? Math.round(
        (dash.data.tracks.reduce((sum, tr) => sum + tr.average_mastery, 0) /
          Math.max(1, dash.data.tracks.length)) * 100
      )
    : 0;
  const reviewsDue = dash.data?.reviews_due ?? 0;
  const streak = dash.data?.current_streak ?? user.currentStreak;

  const topTrack = dash.data?.tracks.slice().sort((a, b) => a.average_mastery - b.average_mastery)[0];

  return (
    <div className={styles.screen}>
      {/* Hero */}
      <div className={styles.hero}>
        <p className={styles.heroGreeting}>{t('home.greeting')} {getTimeOfDay(lang)}, {user.displayName.split(' ')[0]}</p>
        <h1 className={styles.heroTitle}>{t('home.ready')}</h1>
        <div className={styles.heroStats}>
          <div className={styles.heroStat}>
            <span className={styles.heroStatVal}>{user.level}</span>
            <span className={styles.heroStatLabel}>{t('home.level')}</span>
          </div>
          <div className={styles.heroStat}>
            <span className={styles.heroStatVal}>{overallMastery}%</span>
            <span className={styles.heroStatLabel}>{t('home.mastery')}</span>
          </div>
          <div className={styles.heroStat}>
            <span className={styles.heroStatVal}>{streak}</span>
            <span className={styles.heroStatLabel}>{t('home.streak')}</span>
          </div>
        </div>
        <button className={styles.btnStudy} onClick={() => startQuiz('study', 10)}>
          {t('home.studyNow')}
        </button>
        <div className={styles.heroCircle1} />
        <div className={styles.heroCircle2} />
      </div>

      {/* Prediction */}
      {topTrack && (
        <Card className={styles.prediction}>
          <span className={styles.predictionIcon}>🧠</span>
          <div>
            <p className={styles.predictionTitle}>{t('home.prediction')}</p>
            <p className={styles.predictionText}>
              {t('home.predText1')} <strong>{lang === 'es' ? topTrack.name_es : topTrack.name_en}</strong>{' '}
              {t('home.predText2')} <strong>{topTrack.skills_mastered}/{topTrack.total_skills}</strong> {t('home.predText3')}
            </p>
          </div>
        </Card>
      )}

      {/* What you are about to forget — FSRS, made visible.
          Only shown when there is something to say: an empty card here would
          be noise, and inventing urgency to fill it would be the dark pattern
          this feature is meant to avoid. */}
      {decaying.data && decaying.data.length > 0 && (
        <Card>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>{t('home.decayTitle')}</h2>
          </div>
          <p className={styles.muted}>{t('home.decaySubtitle')}</p>
          <ul className={styles.decayList}>
            {decaying.data.map((s) => (
              <li key={s.skill_id} className={styles.decayItem}>
                <button
                  type="button"
                  className={styles.decayName}
                  onClick={() => startQuiz('review', 10, { skillId: s.skill_id })}
                >
                  {lang === 'es' ? s.name_es : s.name_en}
                </button>
                <span className={styles.decayWhen}>
                  {s.days_until_due <= 0
                    ? t('home.decayNow')
                    : s.days_until_due === 1
                      ? t('home.decayTomorrow')
                      : t('home.decayInDays', { count: s.days_until_due })}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Missions */}
      <Card>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>{t('home.missions')}</h2>
          {missions.data && (
            <span className={styles.badge} style={{ background: 'var(--le-orange-light)', color: 'var(--le-text)' }}>
              {missions.data.filter((m) => m.completed).length}/{missions.data.length}
            </span>
          )}
        </div>
        {missions.loading && <p className={styles.muted}>{t('home.loading')}</p>}
        {missions.data?.map((m) => (
          <div key={m.mission.id} className={styles.mission}>
            <div className={styles.missionIcon} style={{ background: m.completed ? 'var(--le-green-light)' : 'var(--le-brand-light)' }}>
              {m.mission.type === 'questions_answered' ? '🎯' : m.mission.type === 'perfect_combo' ? '🔥' : m.mission.type === 'xp_earned' ? '⚡' : '✅'}
            </div>
            <div className={styles.missionInfo}>
              <p className={styles.missionTitle}>{lang === 'es' ? m.mission.name_es : m.mission.name_en}</p>
              <ProgressBar value={m.progress} max={m.mission.target_value} color={m.completed ? 'var(--le-green)' : 'var(--le-brand)'} height={10} />
            </div>
            <span className={styles.missionXp} style={{ color: m.completed ? 'var(--le-green)' : 'var(--le-brand-dark)' }}>
              {m.completed ? t('home.done') : `+${m.mission.xp_reward} XP`}
            </span>
          </div>
        ))}
      </Card>

      {/* Streak */}
      <Card>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>{t('home.yourStreak')}: {streak} {t('home.days')} 🔥</h2>
          <span className={styles.badge} style={{ background: 'var(--le-green-light)', color: 'var(--le-text)' }}>
            {t('home.best')}: {dash.data?.max_streak ?? user.maxStreak}
          </span>
        </div>
        <StreakCalendar streak={streak} />
      </Card>

      {/* Review reminder */}
      {reviewsDue > 0 && (
        <Card className={styles.reviewCard}>
          <span style={{ fontSize: '2rem' }}>⏰</span>
          <div style={{ flex: 1 }}>
            <p className={styles.missionTitle}>{reviewsDue} {t('home.reviewsPending')}</p>
            <p style={{ fontSize: 'var(--le-fs-xs)', color: 'var(--le-text-secondary)' }}>~{Math.max(1, Math.round(reviewsDue * 1.5))} min</p>
          </div>
          <button className={styles.btnReview} onClick={() => startQuiz('review', reviewsDue)}>{t('home.review')}</button>
        </Card>
      )}
    </div>
  );
}

function StreakCalendar({ streak }: { streak: number }) {
  const { t } = useTranslation();
  const days = ['L', 'M', 'X', 'J', 'V', 'S', 'D'];
  const TOTAL = 28;
  const todayIdx = 27;
  return (
    <div className={styles.streakGrid}>
      {days.map((d) => (<div key={d} className={styles.streakLabel}>{d}</div>))}
      {Array.from({ length: TOTAL }).map((_, i) => {
        const isToday = i === todayIdx;
        const active = i > todayIdx - Math.min(streak, TOTAL) && i <= todayIdx;
        let cls = styles.streakDay;
        if (isToday) cls += ` ${styles.today}`;
        else if (active) cls += ` ${styles.active}`;
        return <div key={i} className={cls}>{isToday ? t('home.today') : ''}</div>;
      })}
    </div>
  );
}
