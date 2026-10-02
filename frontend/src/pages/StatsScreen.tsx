import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { ProgressBar } from '../components/common/ProgressBar';
import { useApi } from '../hooks/useApi';
import { progress as progressApi } from '../services/api';
import styles from './StatsScreen.module.css';

const pct = (x: number) => Math.round(x * 100);

// Escala de datos (acero → hielo) y verde solo para lo que el motor da por
// dominado: un número bajo no es un error, así que nunca va en rojo.
const barColor = (mastered: boolean) => (mastered ? 'var(--le-green)' : 'var(--le-blue)');

export function StatsScreen() {
  const user = useAppStore((s) => s.user);
  const openTrack = useAppStore((s) => s.openTrack);
  const lang = user.language;
  const dash = useApi(() => progressApi.dashboard(), []);
  const skills = useApi(() => progressApi.skills(), []);
  const { t } = useTranslation();

  // Solo las rutas empezadas: el panel devuelve las 35 y listarlas todas a 0 %
  // (o promediarlas) escondía el progreso real, como pasaba en Hoy.
  const allTracks = dash.data?.tracks ?? [];
  const started = allTracks
    .filter((tr) => tr.average_mastery > 0 || tr.skills_mastered > 0)
    .sort((a, b) => b.average_mastery - a.average_mastery);
  const attemptedSkills = (skills.data ?? [])
    .filter((s) => s.attempts > 0)
    .sort((a, b) => b.p_known - a.p_known);

  return (
    <div className={styles.screen}>
      <h1 className={styles.title}>{t('stats.title')}</h1>

      <div className={styles.overview}>
        <div className={styles.tile}>
          <span className={styles.tileVal}>{(dash.data?.total_xp ?? user.totalXp).toLocaleString()}</span>
          <span className={styles.tileLabel}>{t('stats.totalXp')}</span>
        </div>
        <div className={styles.tile}>
          <span className={styles.tileVal}>{dash.data?.total_questions_answered ?? 0}</span>
          <span className={styles.tileLabel}>{t('stats.questions')}</span>
        </div>
        <div className={styles.tile}>
          <span className={styles.tileVal}>{attemptedSkills.length}</span>
          <span className={styles.tileLabel}>{t('stats.skillsPractised')}</span>
        </div>
      </div>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>{t('stats.byTrack')}</h2>
        {dash.loading && <p className={styles.muted}>{t('stats.loading')}</p>}
        {!dash.loading && started.length === 0 && <p className={styles.muted}>{t('stats.noData')}</p>}
        <ul className={styles.list}>
          {started.map((tr) => {
            const name = lang === 'es' ? tr.name_es : tr.name_en;
            return (
              <li key={tr.track_id}>
                <button type="button" className={styles.row} onClick={() => openTrack(tr.track_id)}>
                  <span className={styles.rowHead}>
                    <span className={styles.rowName}>{tr.icon} {name}</span>
                    <span className={styles.rowPct}>{pct(tr.average_mastery)}%</span>
                  </span>
                  <ProgressBar
                    value={pct(tr.average_mastery)}
                    max={100}
                    label={t('a11y.progressMastery', { name })}
                    color="var(--le-blue)"
                    height={4}
                  />
                  <span className={styles.rowMeta}>{tr.skills_mastered}/{tr.total_skills} {t('stats.skillsMastered')}</span>
                </button>
              </li>
            );
          })}
        </ul>
        {allTracks.length > started.length && (
          <p className={styles.muted}>{t('stats.notStarted', { count: allTracks.length - started.length })}</p>
        )}
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>{t('stats.bySkill')}</h2>
        {skills.loading && <p className={styles.muted}>{t('stats.loading')}</p>}
        {!skills.loading && attemptedSkills.length === 0 && <p className={styles.muted}>{t('stats.noData')}</p>}
        <ul className={styles.list}>
          {attemptedSkills.slice(0, 12).map((s) => {
            const name = lang === 'es' ? s.name_es : s.name_en;
            return (
              <li key={s.skill_id} className={styles.item}>
                <span className={styles.rowHead}>
                  <span className={styles.rowName}>{name}</span>
                  <span className={`${styles.rowPct} ${s.mastered ? styles.pctMastered : ''}`}>{pct(s.p_known)}%</span>
                </span>
                <ProgressBar
                  value={pct(s.p_known)}
                  max={100}
                  label={t('a11y.progressMastery', { name })}
                  color={barColor(s.mastered)}
                  height={4}
                />
                <span className={styles.rowMeta}>
                  {t('stats.correctOf', { correct: s.correct_count, total: s.attempts })} · Elo {Math.round(s.elo_rating)}
                </span>
              </li>
            );
          })}
        </ul>
      </section>
    </div>
  );
}
