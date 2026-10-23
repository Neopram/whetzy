import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { ProgressBar } from '../components/common/ProgressBar';
import { BandChip } from '../components/common/BandChip';
import { bandForSkill } from '../lib/evidenceBand';
import { useApi } from '../hooks/useApi';
import { progress as progressApi } from '../services/api';
import { StaggerItem, StaggerList } from '../components/common/Stagger';
import styles from './StatsScreen.module.css';
import { TrackIcon } from '../components/common/AppIcon';
import { Loading } from '../components/common/Loading';
import { ErrorState } from '../components/common/ErrorState';

// ADR-60: ni la ruta ni la skill se enseñan como % del modelo mientras no
// esté calibrado. La ruta, por skills dominadas (un hecho); la skill, por banda.

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
        {dash.loading && <Loading label={t('stats.loading')} shape="line" />}
        {/* Revisión de UI del 2026-10-23: un fallo de red salía como «sin datos». */}
        {dash.error !== null && <ErrorState message={t('common.loadError')} onRetry={dash.reload} />}
        {!dash.loading && dash.error === null && started.length === 0 && <p className={styles.muted}>{t('stats.noData')}</p>}
        <StaggerList className={styles.list}>
          {started.map((tr) => {
            const name = lang === 'es' ? tr.name_es : tr.name_en;
            return (
              <StaggerItem key={tr.track_id}>
                <button type="button" className={styles.row} onClick={() => openTrack(tr.track_id)}>
                  <span className={styles.rowHead}>
                    <span className={styles.rowName}><TrackIcon trackId={tr.track_id} fallback={tr.icon} size={20} /> {name}</span>
                  </span>
                  {/* Sin ninguna dominada, una barra vacía no dice nada: basta el recuento. */}
                  {tr.skills_mastered > 0 && (
                    <ProgressBar
                      value={tr.skills_mastered}
                      max={Math.max(tr.total_skills, 1)}
                      label={t('a11y.progressMastered', { name })}
                      color="var(--le-blue)"
                      height={4}
                      grow
                    />
                  )}
                  <span className={styles.rowMeta}>{tr.skills_mastered}/{tr.total_skills} {t('stats.skillsMastered')}</span>
                </button>
              </StaggerItem>
            );
          })}
        </StaggerList>
        {allTracks.length > started.length && (
          <p className={styles.muted}>{t('stats.notStarted', { count: allTracks.length - started.length })}</p>
        )}
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>{t('stats.bySkill')}</h2>
        {skills.loading && <Loading label={t('stats.loading')} shape="line" />}
        {skills.error !== null && <ErrorState message={t('common.loadError')} onRetry={skills.reload} />}
        {!skills.loading && skills.error === null && attemptedSkills.length === 0 && <p className={styles.muted}>{t('stats.noData')}</p>}
        <StaggerList className={styles.list}>
          {attemptedSkills.slice(0, 12).map((s) => {
            const name = lang === 'es' ? s.name_es : s.name_en;
            return (
              <StaggerItem key={s.skill_id} className={styles.item}>
                <span className={styles.rowHead}>
                  <span className={styles.rowName}>{name}</span>
                  <BandChip band={bandForSkill(s)} />
                </span>
                <span className={styles.rowMeta}>
                  {t('stats.correctOf', { correct: s.correct_count, total: s.attempts })}
                  {/* ADR-60: el Elo de la skill, solo para depurar. */}
                  {import.meta.env.DEV && ` · Elo ${Math.round(s.elo_rating)}`}
                </span>
              </StaggerItem>
            );
          })}
        </StaggerList>
      </section>
    </div>
  );
}
