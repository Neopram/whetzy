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

  const dash = useApi(() => progressApi.dashboard(), []);
  const missions = useApi(() => gamification.missions(), []);

  const overallMastery = dash.data
    ? Math.round(
        (dash.data.tracks.reduce((sum, t) => sum + t.average_mastery, 0) /
          Math.max(1, dash.data.tracks.length)) * 100
      )
    : 0;
  const reviewsDue = dash.data?.reviews_due ?? 0;
  const streak = dash.data?.current_streak ?? user.currentStreak;

  const L = TEXT[lang];
  const topTrack = dash.data?.tracks.slice().sort((a, b) => a.average_mastery - b.average_mastery)[0];

  return (
    <div className={styles.screen}>
      {/* Hero */}
      <div className={styles.hero}>
        <p className={styles.heroGreeting}>{L.greeting} {getTimeOfDay(lang)}, {user.displayName.split(' ')[0]}</p>
        <h1 className={styles.heroTitle}>{L.ready}</h1>
        <div className={styles.heroStats}>
          <div className={styles.heroStat}>
            <span className={styles.heroStatVal}>{user.level}</span>
            <span className={styles.heroStatLabel}>{L.level}</span>
          </div>
          <div className={styles.heroStat}>
            <span className={styles.heroStatVal}>{overallMastery}%</span>
            <span className={styles.heroStatLabel}>{L.mastery}</span>
          </div>
          <div className={styles.heroStat}>
            <span className={styles.heroStatVal}>{streak}</span>
            <span className={styles.heroStatLabel}>{L.streak}</span>
          </div>
        </div>
        <button className={styles.btnStudy} onClick={() => startQuiz('study', 10)}>
          {L.studyNow}
        </button>
        <div className={styles.heroCircle1} />
        <div className={styles.heroCircle2} />
      </div>

      {/* Prediction */}
      {topTrack && (
        <Card className={styles.prediction}>
          <span className={styles.predictionIcon}>🧠</span>
          <div>
            <p className={styles.predictionTitle}>{L.prediction}</p>
            <p className={styles.predictionText}>
              {L.predText1} <strong>{lang === 'es' ? topTrack.name_es : topTrack.name_en}</strong>{' '}
              {L.predText2} <strong>{topTrack.skills_mastered}/{topTrack.total_skills}</strong> {L.predText3}
            </p>
          </div>
        </Card>
      )}

      {/* Missions */}
      <Card>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>{L.missions}</h2>
          {missions.data && (
            <span className={styles.badge} style={{ background: 'var(--le-orange-light)', color: 'var(--le-text)' }}>
              {missions.data.filter((m) => m.completed).length}/{missions.data.length}
            </span>
          )}
        </div>
        {missions.loading && <p className={styles.muted}>{L.loading}</p>}
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
              {m.completed ? L.done : `+${m.mission.xp_reward} XP`}
            </span>
          </div>
        ))}
      </Card>

      {/* Streak */}
      <Card>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>{L.yourStreak}: {streak} {L.days} 🔥</h2>
          <span className={styles.badge} style={{ background: 'var(--le-green-light)', color: 'var(--le-text)' }}>
            {L.best}: {dash.data?.max_streak ?? user.maxStreak}
          </span>
        </div>
        <StreakCalendar streak={streak} />
      </Card>

      {/* Review reminder */}
      {reviewsDue > 0 && (
        <Card className={styles.reviewCard}>
          <span style={{ fontSize: '2rem' }}>⏰</span>
          <div style={{ flex: 1 }}>
            <p className={styles.missionTitle}>{reviewsDue} {L.reviewsPending}</p>
            <p style={{ fontSize: 'var(--le-fs-xs)', color: 'var(--le-text-secondary)' }}>~{Math.max(1, Math.round(reviewsDue * 1.5))} min</p>
          </div>
          <button className={styles.btnReview} onClick={() => startQuiz('review', reviewsDue)}>{L.review}</button>
        </Card>
      )}
    </div>
  );
}

function StreakCalendar({ streak }: { streak: number }) {
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
        return <div key={i} className={cls}>{isToday ? 'Hoy' : ''}</div>;
      })}
    </div>
  );
}

const TEXT = {
  es: {
    greeting: 'Buenos', ready: '¿Listo para aprender?', level: 'NIVEL', mastery: 'DOMINIO', streak: 'RACHA',
    studyNow: 'ESTUDIAR AHORA', prediction: 'Progreso del sistema', predText1: 'Tu track más próximo es',
    predText2: '— dominas', predText3: 'habilidades', missions: 'Misiones del día', loading: 'Cargando…',
    done: '¡Completada!', yourStreak: 'Tu racha', days: 'días', best: 'Mejor', reviewsPending: 'repasos pendientes', review: 'Repasar',
  },
  en: {
    greeting: 'Good', ready: 'Ready to learn?', level: 'LEVEL', mastery: 'MASTERY', streak: 'STREAK',
    studyNow: 'STUDY NOW', prediction: 'System progress', predText1: 'Your nearest track is',
    predText2: '— you master', predText3: 'skills', missions: 'Daily missions', loading: 'Loading…',
    done: 'Done!', yourStreak: 'Your streak', days: 'days', best: 'Best', reviewsPending: 'reviews pending', review: 'Review',
  },
} as const;
