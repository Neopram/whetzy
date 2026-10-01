import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { useAppStore } from '../stores/useAppStore';
import { ProgressBar } from '../components/common/ProgressBar';
import { Card } from '../components/common/Card';
import { ReadinessGauge } from '../components/common/ReadinessGauge';
import { StreakFreezeShop } from '../components/home/StreakFreezeShop';
import { useApi } from '../hooks/useApi';
import { progress as progressApi, gamification, type SkillMasteryDetail } from '../services/api';
import { listVariants, listItemVariants } from '../lib/motion';
import styles from './HomeScreen.module.css';

// Saludo entero por clave: «Buenos» + «noches» salía «Buenos noches».
function greetingKey(): 'home.greetingMorning' | 'home.greetingAfternoon' | 'home.greetingEvening' {
  const h = new Date().getHours();
  return h < 12 ? 'home.greetingMorning' : h < 19 ? 'home.greetingAfternoon' : 'home.greetingEvening';
}

// Dos cifras distintas, cada una con su nombre: el objetivo de preparación
// (la marca del arco y «rutas listas») y el umbral con el que el motor da una
// habilidad por dominada (MASTERY_THRESHOLD del backend, el ✓ de Rutas).
const READY = 0.75;
const MASTERED = 0.95;

export function HomeScreen() {
  const user = useAppStore((s) => s.user);
  const startQuiz = useAppStore((s) => s.startQuiz);
  const setScreen = useAppStore((s) => s.setScreen);
  const openTrack = useAppStore((s) => s.openTrack);
  const lang = user.language;
  const { t } = useTranslation();

  const dash = useApi(() => progressApi.dashboard(), []);
  const missions = useApi(() => gamification.missions(), []);
  const decaying = useApi(() => progressApi.decaying(), []);
  const skills = useApi(() => progressApi.skills(), []);

  // Solo las rutas con algo practicado: el panel devuelve las 35, y promediar
  // sobre las que nunca se abrieron hundía el dominio a 0 % con progreso real.
  const tracks = (dash.data?.tracks ?? [])
    .filter((tr) => tr.average_mastery > 0 || tr.skills_mastered > 0)
    .sort((a, b) => b.average_mastery - a.average_mastery);
  const overallMastery = tracks.length
    ? Math.round((tracks.reduce((sum, tr) => sum + tr.average_mastery, 0) / tracks.length) * 100)
    : 0;
  const tracksReady = tracks.filter((tr) => tr.average_mastery >= READY).length;
  const shownTracks = tracks.slice(0, 5);
  const reviewsDue = dash.data?.reviews_due ?? 0;
  const streak = dash.data?.current_streak ?? user.currentStreak;

  // Elo medio real de las skills con al menos un intento (24.4). undefined
  // mientras no haya ninguna: mostrar 1500 (el arranque) sería inventarlo.
  const practicedSkills = skills.data?.filter((s) => s.attempts > 0) ?? [];
  const avgElo = practicedSkills.length > 0
    ? Math.round(practicedSkills.reduce((sum, s) => sum + s.elo_rating, 0) / practicedSkills.length)
    : undefined;

  return (
    <motion.div className={styles.screen} variants={listVariants} initial="initial" animate="animate">
      <motion.header className={styles.head} variants={listItemVariants}>
        <p className={styles.eyebrow}>{t(greetingKey())}, {user.displayName.split(' ')[0]}</p>
        <h1 className={styles.title}>{t('home.heroTitle')}</h1>
      </motion.header>

      {/* Preparación + siguiente paso: lo único que hay que hacer, arriba. */}
      <div className={styles.topGrid}>
        <motion.section className={styles.readiness} variants={listItemVariants} aria-label={t('home.masteryLabel')}>
          <ReadinessGauge
            value={overallMastery}
            label={t('home.masteryLabel')}
            ariaLabel={`${t('home.masteryLabel')}: ${overallMastery} %`}
          >
            <p className={styles.gaugeMeta}>
              <span className={styles.readyDot} aria-hidden="true" />
              <strong>{tracksReady} / {tracks.length}</strong> {t('home.tracksReady')}
            </p>
          </ReadinessGauge>
          <p className={styles.threshold}>{t('home.thresholdNote')}</p>
        </motion.section>

        <motion.section className={styles.next} variants={listItemVariants} aria-label={t('home.nextStep')}>
          <p className={styles.nextLabel}>{t('home.nextStep')}</p>
          <p className={styles.nextName}>{t('home.nextStudy')}</p>
          <p className={styles.nextHint}>{t('home.nextHint')}</p>
          <motion.button
            className={styles.btnStudy}
            onClick={() => startQuiz('study', 10)}
            whileTap={{ scale: 0.98 }}
          >
            {t('home.studyNow')}
          </motion.button>
        </motion.section>
      </div>

      <div className={styles.split}>
        {/* Repaso: FSRS a la vista, con el estado tranquilo cuando no toca. */}
        <motion.div variants={listItemVariants}>
          <Card className={styles.panel}>
            <h2 className={styles.cardTitle}>{t('home.reviewTitle')}</h2>
            {reviewsDue > 0 ? (
              <>
                <p className={styles.reviewCount}>
                  <strong>{reviewsDue}</strong> {t('home.reviewsPending')}
                </p>
                <button type="button" className={styles.btnSecondary} onClick={() => startQuiz('review', reviewsDue)}>
                  {t('home.review')}
                </button>
              </>
            ) : (
              <p className={styles.muted}>{t('home.reviewCalm')}</p>
            )}
            {decaying.data && decaying.data.length > 0 && (
              <div className={styles.decay}>
                <p className={styles.decayTitle}>{t('home.decayTitle')}</p>
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
              </div>
            )}
          </Card>
        </motion.div>

        {/* Racha compacta: tres cifras con su nombre, sin cuadrícula vacía. */}
        <motion.div variants={listItemVariants}>
          <Card className={styles.panel}>
            <h2 className={styles.cardTitle}>
              {t('home.yourStreak')}: {streak} {t('home.days', { count: streak })}
            </h2>
            <div className={styles.streakStats}>
              <div className={styles.streakItem}>
                <strong>{streak}</strong>
                <span>{t('home.currentStreak')}</span>
              </div>
              <div className={styles.streakItem}>
                <strong>{dash.data?.max_streak ?? user.maxStreak}</strong>
                <span>{t('home.best')}</span>
              </div>
              <div className={styles.streakItem}>
                <strong>{user.streakFreezeAvailable}</strong>
                <span>{t('home.freezeLabel')}</span>
              </div>
            </div>
            <p className={styles.muted}>
              {t('home.freeze', { count: user.streakFreezeAvailable })} {t('home.streakKind')}
            </p>
            <StreakFreezeShop />
          </Card>
        </motion.div>
      </div>

      {shownTracks.length > 0 && (
        <motion.section className={styles.section} variants={listItemVariants}>
          <div className={styles.cardHeader}>
            <h2 className={styles.sectionTitle}>{t('home.yourTracks')}</h2>
            <button type="button" className={styles.link} onClick={() => setScreen('tracks')}>
              {t('home.allTracks')} →
            </button>
          </div>
          <div className={styles.trackList}>
            {shownTracks.map((tr) => (
              <button key={tr.track_id} type="button" className={styles.trackRow} onClick={() => openTrack(tr.track_id)}>
                <span className={styles.trackIcon} aria-hidden="true">{tr.icon}</span>
                <span className={styles.trackBody}>
                  <span className={styles.trackName}>{lang === 'es' ? tr.name_es : tr.name_en}</span>
                  <ProgressBar
                    value={Math.round(tr.average_mastery * 100)}
                    max={100}
                    label={lang === 'es' ? tr.name_es : tr.name_en}
                    color="var(--le-blue)"
                    height={6}
                  />
                  <span className={styles.trackNumbers}>
                    <span>{tr.skills_mastered}/{tr.total_skills} {t('home.skillsMastered')}</span>
                    <b>{Math.round(tr.average_mastery * 100)}%</b>
                  </span>
                </span>
              </button>
            ))}
          </div>
        </motion.section>
      )}

      <motion.div variants={listItemVariants}>
        <Card className={styles.panel}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>{t('home.missions')}</h2>
            {missions.data && (
              <span className={styles.badge}>
                {missions.data.filter((m) => m.completed).length}/{missions.data.length}
              </span>
            )}
          </div>
          {missions.loading && <p className={styles.muted}>{t('home.loading')}</p>}
          {missions.data?.map((m) => {
            const name = lang === 'es' ? m.mission.name_es : m.mission.name_en;
            return (
              <div key={m.mission.id} className={styles.mission}>
                <div className={styles.missionInfo}>
                  <p className={styles.missionTitle}>{name}</p>
                  <ProgressBar
                    value={m.progress}
                    max={m.mission.target_value}
                    label={t('a11y.progressMission', { name })}
                    color={m.completed ? 'var(--le-green)' : 'var(--le-blue)'}
                    height={6}
                  />
                </div>
                <span className={m.completed ? styles.missionDone : styles.missionXp}>
                  {m.completed ? t('home.done') : `+${m.mission.xp_reward} XP`}
                </span>
              </div>
            );
          })}
        </Card>
      </motion.div>

      {/* Territorio: cada skill practicada con su dominio real (BKT, 24.4). */}
      {(skills.data?.length ?? 0) > 0 && (
        <motion.section className={styles.section} variants={listItemVariants}>
          <div className={styles.cardHeader}>
            <h2 className={styles.sectionTitle}>{t('home.territory')}</h2>
            {avgElo !== undefined && (
              <span className={styles.badge} title={t('home.eloHint')}>
                {t('home.eloLabel')}: {avgElo}
              </span>
            )}
          </div>
          <div className={styles.territoryGrid}>
            {skills.data!
              .slice()
              .sort((a: SkillMasteryDetail, b: SkillMasteryDetail) => b.p_known - a.p_known)
              .slice(0, 8)
              .map((s: SkillMasteryDetail) => {
                const pct = Math.round(s.p_known * 100);
                const estado = s.p_known >= MASTERED ? 'dominated' : s.p_known >= 0.4 ? 'partial' : 'frontier';
                const name = lang === 'es' ? s.name_es : s.name_en;
                return (
                  <div key={s.skill_id} className={`${styles.node} ${styles[estado]}`} role="group" aria-label={`${name}: ${pct}%`}>
                    <span className={styles.nodeName}>{name}</span>
                    <span className={styles.nodeMastery}>{pct}%</span>
                    <span className={styles.nodeBar} style={{ width: `${pct}%` }} aria-hidden="true" />
                  </div>
                );
              })}
          </div>
        </motion.section>
      )}

      <motion.section className={styles.section} variants={listItemVariants}>
        <h2 className={styles.sectionTitle}>{t('home.tools')}</h2>
        <div className={styles.tools}>
          <button type="button" className={styles.tool} onClick={() => setScreen('playground')}>
            <span aria-hidden="true">💻</span>
            <span className={styles.toolName}>{t('playground.openPlayground')}</span>
            <span className={styles.toolMeta}>Python · SQL · JS</span>
          </button>
          <button type="button" className={styles.tool} onClick={() => setScreen('projects')}>
            <span aria-hidden="true">🏗️</span>
            <span className={styles.toolName}>{t('project.title')}</span>
            <span className={styles.toolMeta}>{t('project.step')}-by-{t('project.step').toLowerCase()}</span>
          </button>
        </div>
      </motion.section>
    </motion.div>
  );
}
