import { useAppStore } from '../stores/useAppStore';
import { Card } from '../components/common/Card';
import { ProgressBar } from '../components/common/ProgressBar';
import { useApi } from '../hooks/useApi';
import { progress as progressApi } from '../services/api';
import styles from './StatsScreen.module.css';

function masteryColor(m: number): string {
  if (m >= 0.85) return 'var(--le-green)';
  if (m >= 0.6) return 'var(--le-brand)';
  if (m >= 0.4) return 'var(--le-orange)';
  return 'var(--le-red)';
}

export function StatsScreen() {
  const user = useAppStore((s) => s.user);
  const lang = user.language;
  const dash = useApi(() => progressApi.dashboard(), []);
  const skills = useApi(() => progressApi.skills(), []);
  const L = TEXT[lang];

  const totalQuestions = dash.data?.total_questions_answered ?? 0;
  const _accuracy = Math.round((dash.data?.overall_accuracy ?? 0) * 100);
  const avgMastery = dash.data && dash.data.tracks.length
    ? Math.round((dash.data.tracks.reduce((s, t) => s + t.average_mastery, 0) / dash.data.tracks.length) * 100)
    : 0;

  const attemptedSkills = (skills.data ?? []).filter((s) => s.attempts > 0)
    .sort((a, b) => b.p_known - a.p_known);

  return (
    <div className={styles.screen}>
      <h1 className={styles.title}>{L.title}</h1>

      <div className={styles.overview}>
        <div className={styles.overviewCard} style={{ background: 'linear-gradient(135deg, var(--le-brand-2), var(--le-brand-dark))' }}>
          <span className={styles.overviewVal}>{(dash.data?.total_xp ?? user.totalXp).toLocaleString()}</span>
          <span className={styles.overviewLabel}>{L.totalXp}</span>
        </div>
        <div className={styles.overviewCard} style={{ background: 'linear-gradient(135deg, #7EE0FF, #1CB0F6)' }}>
          <span className={styles.overviewVal}>{totalQuestions}</span>
          <span className={styles.overviewLabel}>{L.questions}</span>
        </div>
        <div className={styles.overviewCard} style={{ background: 'linear-gradient(135deg, var(--le-green-light), var(--le-green))' }}>
          <span className={styles.overviewVal}>{avgMastery}%</span>
          <span className={styles.overviewLabel}>{L.mastery}</span>
        </div>
      </div>

      {/* Track mastery */}
      <Card>
        <h2 className={styles.cardTitle}>{L.byTrack}</h2>
        {dash.loading && <p className={styles.muted}>{L.loading}</p>}
        <div className={styles.skills}>
          {dash.data?.tracks.map((t) => (
            <div key={t.track_id} className={styles.skill}>
              <div className={styles.skillHeader}>
                <span className={styles.skillName}>{t.icon} {lang === 'es' ? t.name_es : t.name_en}</span>
                <span className={styles.skillPct} style={{ color: masteryColor(t.average_mastery) }}>{Math.round(t.average_mastery * 100)}%</span>
              </div>
              <ProgressBar value={t.average_mastery * 100} max={100} color={masteryColor(t.average_mastery)} height={8} />
              <span className={styles.skillMeta}>{t.skills_mastered}/{t.total_skills} {L.skillsMastered}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Skill breakdown */}
      <Card>
        <h2 className={styles.cardTitle}>{L.bySkill}</h2>
        {skills.loading && <p className={styles.muted}>{L.loading}</p>}
        {!skills.loading && attemptedSkills.length === 0 && <p className={styles.muted}>{L.noData}</p>}
        <div className={styles.skills}>
          {attemptedSkills.slice(0, 12).map((s) => (
            <div key={s.skill_id} className={styles.skill}>
              <div className={styles.skillHeader}>
                <span className={styles.skillName}>{lang === 'es' ? s.name_es : s.name_en}</span>
                <span className={styles.skillPct} style={{ color: masteryColor(s.p_known) }}>{Math.round(s.p_known * 100)}%</span>
              </div>
              <ProgressBar value={s.p_known * 100} max={100} color={masteryColor(s.p_known)} height={8} />
              <span className={styles.skillMeta}>{s.correct_count}/{s.attempts} · Elo {Math.round(s.elo_rating)}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

const TEXT = {
  es: { title: 'Estadísticas', totalXp: 'XP Total', questions: 'Preguntas', mastery: 'Dominio',
    byTrack: 'Dominio por track', bySkill: 'Dominio por habilidad', skillsMastered: 'dominadas',
    loading: 'Cargando…', noData: 'Responde preguntas para ver tu progreso aquí.' },
  en: { title: 'Statistics', totalXp: 'Total XP', questions: 'Questions', mastery: 'Mastery',
    byTrack: 'Mastery by track', bySkill: 'Mastery by skill', skillsMastered: 'mastered',
    loading: 'Loading…', noData: 'Answer questions to see your progress here.' },
} as const;
