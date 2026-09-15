import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();

  const totalQuestions = dash.data?.total_questions_answered ?? 0;
  const avgMastery = dash.data && dash.data.tracks.length
    ? Math.round((dash.data.tracks.reduce((s, tr) => s + tr.average_mastery, 0) / dash.data.tracks.length) * 100)
    : 0;

  const attemptedSkills = (skills.data ?? []).filter((s) => s.attempts > 0)
    .sort((a, b) => b.p_known - a.p_known);

  return (
    <div className={styles.screen}>
      <h1 className={styles.title}>{t('stats.title')}</h1>

      <div className={styles.overview}>
        <div className={styles.overviewCard} style={{ background: 'linear-gradient(135deg, var(--le-brand-2), var(--le-brand-dark))' }}>
          <span className={styles.overviewVal}>{(dash.data?.total_xp ?? user.totalXp).toLocaleString()}</span>
          <span className={styles.overviewLabel}>{t('stats.totalXp')}</span>
        </div>
        <div className={styles.overviewCard} style={{ background: 'linear-gradient(135deg, #7EE0FF, #1CB0F6)' }}>
          <span className={styles.overviewVal}>{totalQuestions}</span>
          <span className={styles.overviewLabel}>{t('stats.questions')}</span>
        </div>
        <div className={styles.overviewCard} style={{ background: 'linear-gradient(135deg, var(--le-green-light), var(--le-green))' }}>
          <span className={styles.overviewVal}>{avgMastery}%</span>
          <span className={styles.overviewLabel}>{t('stats.mastery')}</span>
        </div>
      </div>

      {/* Track mastery */}
      <Card>
        <h2 className={styles.cardTitle}>{t('stats.byTrack')}</h2>
        {dash.loading && <p className={styles.muted}>{t('stats.loading')}</p>}
        <div className={styles.skills}>
          {dash.data?.tracks.map((tr) => (
            <div key={tr.track_id} className={styles.skill}>
              <div className={styles.skillHeader}>
                <span className={styles.skillName}>{tr.icon} {lang === 'es' ? tr.name_es : tr.name_en}</span>
                <span className={styles.skillPct} style={{ color: masteryColor(tr.average_mastery) }}>{Math.round(tr.average_mastery * 100)}%</span>
              </div>
              <ProgressBar
                value={tr.average_mastery * 100}
                max={100}
                label={t('a11y.progressMastery', { name: lang === 'es' ? tr.name_es : tr.name_en })}
                color={masteryColor(tr.average_mastery)}
                height={8}
              />
              <span className={styles.skillMeta}>{tr.skills_mastered}/{tr.total_skills} {t('stats.skillsMastered')}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Skill breakdown */}
      <Card>
        <h2 className={styles.cardTitle}>{t('stats.bySkill')}</h2>
        {skills.loading && <p className={styles.muted}>{t('stats.loading')}</p>}
        {!skills.loading && attemptedSkills.length === 0 && <p className={styles.muted}>{t('stats.noData')}</p>}
        <div className={styles.skills}>
          {attemptedSkills.slice(0, 12).map((s) => (
            <div key={s.skill_id} className={styles.skill}>
              <div className={styles.skillHeader}>
                <span className={styles.skillName}>{lang === 'es' ? s.name_es : s.name_en}</span>
                <span className={styles.skillPct} style={{ color: masteryColor(s.p_known) }}>{Math.round(s.p_known * 100)}%</span>
              </div>
              <ProgressBar
                value={s.p_known * 100}
                max={100}
                label={t('a11y.progressMastery', { name: lang === 'es' ? s.name_es : s.name_en })}
                color={masteryColor(s.p_known)}
                height={8}
              />
              <span className={styles.skillMeta}>{s.correct_count}/{s.attempts} · Elo {Math.round(s.elo_rating)}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
