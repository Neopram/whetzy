import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, useReducedMotion } from 'framer-motion';
import { useAppStore } from '../stores/useAppStore';
import { ProgressBar } from '../components/common/ProgressBar';
import { Card } from '../components/common/Card';
import { StreakFreezeShop } from '../components/home/StreakFreezeShop';
import { useApi } from '../hooks/useApi';
import { content as contentApi, exams, progress as progressApi, gamification, type SkillMasteryDetail } from '../services/api';
import { listVariants, listItemVariants } from '../lib/motion';
import { bandForSkill, overallBand, MIN_EVIDENCE_ANSWERS, type EvidenceBand } from '../lib/evidenceBand';
import { nextLessonSkillId } from '../lib/nextStep';
import { bandMoments, missionMoments } from '../lib/homeMoments';
import { emit as emitFx } from '../lib/feedbackFx';
import { biggestLever } from '../lib/readinessLever';
import { LeverCard } from '../components/readiness/LeverCard';
import styles from './HomeScreen.module.css';
import { TrackIcon } from '../components/common/AppIcon';

// Saludo entero por clave: «Buenos» + «noches» salía «Buenos noches».
function greetingKey(): 'home.greetingMorning' | 'home.greetingAfternoon' | 'home.greetingEvening' {
  const h = new Date().getHours();
  return h < 12 ? 'home.greetingMorning' : h < 19 ? 'home.greetingAfternoon' : 'home.greetingEvening';
}

// ADR-60 / D-16: Hoy no enseña porcentajes del modelo mientras no esté
// calibrado; enseña un estado con la evidencia que lo sostiene.
const BAND_CLASS: Record<EvidenceBand, string> = {
  strong: 'dominated',
  developing: 'partial',
  insufficient: 'frontier',
};

export function HomeScreen() {
  const user = useAppStore((s) => s.user);
  const startQuiz = useAppStore((s) => s.startQuiz);
  const setScreen = useAppStore((s) => s.setScreen);
  const openProjects = useAppStore((s) => s.openProjects);
  const openTrack = useAppStore((s) => s.openTrack);
  // 43.4 (ADR-65 D6): Hoy es de la ruta activa. La banda, el siguiente paso,
  // los repasos y el territorio salen solo de ella; antes mezclaban todas.
  const activeTrackId = useAppStore((s) => s.activeTrackId);
  const browseTracks = useAppStore((s) => s.browseTracks);
  const startLesson = useAppStore((s) => s.startLesson);
  const lang = user.language;
  const { t } = useTranslation();

  const dash = useApi(() => progressApi.dashboard(), []);
  const missions = useApi(() => gamification.missions(), []);
  const decaying = useApi(() => progressApi.decaying(7, 5, activeTrackId ?? undefined), [activeTrackId]);
  const skills = useApi(() => progressApi.skills(activeTrackId ?? undefined), [activeTrackId]);
  // 43.5 (ADR-65 D7): «Estudiar» abre la siguiente lección pendiente de la
  // ruta activa; solo cuando no queda ninguna, practica.
  const cur = useApi(
    () => (activeTrackId ? progressApi.curriculum(activeTrackId) : Promise.resolve(null)),
    [activeTrackId],
  );
  const curFailed = Boolean(activeTrackId) && !cur.loading && cur.error !== null;
  // 46.3c: «Tu mayor palanca» sube aquí desde Preparación. Solo hay dominios
  // de examen en una certificación: la ruta activa si lo es y, si no, la
  // certificación elegida en el onboarding (que deja activa la ruta de
  // aprendizaje). Sin ninguna de las dos no se pide nada.
  const trackList = useApi(() => contentApi.tracks(), []);
  const isCertTrack = (id: string | null) => Boolean(id && trackList.data?.find((tr) => tr.id === id)?.is_certification);
  const certTrackId = isCertTrack(activeTrackId) ? activeTrackId : isCertTrack(user.targetCertificationId) ? user.targetCertificationId : null;
  const certTrack = trackList.data?.find((tr) => tr.id === certTrackId);
  const readiness = useApi(
    () => (certTrackId ? exams.certificationReadiness(certTrackId) : Promise.resolve(null)),
    [certTrackId],
  );
  // Sin ninguna respuesta en esa certificación la palanca solo sería «el
  // dominio que más pesa», y practicar llevaría a «Empieza por la lección»
  // (needs_lesson, medido en local): lo primero sigue siendo la lección.
  const certAnswers = readiness.data?.domains.reduce((sum, d) => sum + (d.answers ?? 0), 0) ?? 0;
  const lever = readiness.data && certAnswers > 0 ? biggestLever(readiness.data.domains) : undefined;
  const nextLessonId = cur.data ? nextLessonSkillId(cur.data) : null;
  const nextLesson = cur.data?.modules.flatMap((m) => m.skills).find((s) => s.skill_id === nextLessonId);

  const activeTrack = (dash.data?.tracks ?? []).find((tr) => tr.track_id === activeTrackId);
  // Solo las rutas con algo practicado: el panel devuelve las 35, y promediar
  // sobre las que nunca se abrieron hundía el dominio a 0 % con progreso real.
  // La activa va en la cabecera, no aquí: esto son «otras rutas en curso».
  const tracks = (dash.data?.tracks ?? [])
    .filter((tr) => tr.track_id !== activeTrackId)
    .filter((tr) => tr.average_mastery > 0 || tr.skills_mastered > 0)
    .sort((a, b) => b.average_mastery - a.average_mastery);
  const shownTracks = tracks.slice(0, 5);
  const reviewsDue = dash.data?.reviews_due ?? 0;
  const streak = dash.data?.current_streak ?? user.currentStreak;

  // Elo medio real de las skills con al menos un intento (24.4). undefined
  // mientras no haya ninguna: mostrar 1500 (el arranque) sería inventarlo.
  const practicedSkills = skills.data?.filter((s) => s.attempts > 0) ?? [];
  const skillBands = practicedSkills.map(bandForSkill);
  const band = overallBand(skillBands);
  const bandCount = (b: EvidenceBand) => skillBands.filter((x) => x === b).length;
  const answers = practicedSkills.reduce((sum, s) => sum + s.attempts, 0);
  const correct = practicedSkills.reduce((sum, s) => sum + s.correct_count, 0);
  // 46.3b: lo que cambió desde la última visita se celebra una vez (foto en
  // localStorage, lib/homeMoments.ts). Sin foto previa no se celebra nada.
  const reduceMotion = useReducedMotion();
  const [missionsJustDone, setMissionsJustDone] = useState<string[]>([]);
  const [skillsJustUp, setSkillsJustUp] = useState<string[]>([]);
  useEffect(() => {
    if (!missions.data) return;
    const today = new Date().toISOString().slice(0, 10);
    const done = missionMoments(
      user.id, today, missions.data.map((m) => ({ id: m.mission.id, completed: m.completed })),
    );
    setMissionsJustDone(done);
    if (done.length > 0) emitFx({ type: 'mission' });
  }, [missions.data, user.id]);
  useEffect(() => {
    if (!skills.data) return;
    setSkillsJustUp(
      bandMoments(user.id, skills.data.filter((s) => s.attempts > 0).map((s) => ({ id: s.skill_id, band: bandForSkill(s) }))),
    );
  }, [skills.data, user.id]);

  const avgElo = practicedSkills.length > 0
    ? Math.round(practicedSkills.reduce((sum, s) => sum + s.elo_rating, 0) / practicedSkills.length)
    : undefined;

  return (
    <motion.div className={styles.screen} variants={listVariants} initial="initial" animate="animate">
      <motion.header className={styles.head} variants={listItemVariants}>
        <p className={styles.eyebrow}>{t(greetingKey())}, {user.displayName.split(' ')[0]}</p>
        <h1 className={styles.title}>{t('home.heroTitle')}</h1>
        <p className={styles.activeTrack} data-testid="home-active-track">
          {activeTrackId
            ? <span>{t('home.activeTrack', { name: activeTrack ? (lang === 'es' ? activeTrack.name_es : activeTrack.name_en) : activeTrackId })}</span>
            : <span>{t('home.noActiveTrack')}</span>}
          <button type="button" className={styles.link} onClick={browseTracks}>
            {activeTrackId ? t('home.changeTrack') : t('home.chooseTrack')}
          </button>
        </p>
      </motion.header>

      {lever && certTrackId && (
        <LeverCard
          lever={lever}
          name={lang === 'es' ? lever.name_es : lever.name_en}
          examName={certTrack ? (lang === 'es' ? certTrack.name_es : certTrack.name_en) : undefined}
          onPractice={() => startQuiz('study', 10, { trackId: certTrackId })}
        />
      )}

      {/* Preparación + siguiente paso: lo único que hay que hacer, arriba. */}
      <div className={styles.topGrid}>
        <motion.section className={styles.readiness} variants={listItemVariants} aria-label={t('home.bandTitle')}>
          <p className={styles.bandLabel}>{t('home.bandTitle')}</p>
          <p className={`${styles.bandName} ${styles[BAND_CLASS[band]]}`} data-testid="home-band">
            {t(`bands.${band}`)}
          </p>
          <p className={styles.gaugeMeta}>
            <span className={styles.readyDot} aria-hidden="true" />
            {t('bands.evidence', { answers, correct })}
          </p>
          <p className={styles.threshold}>
            {band === 'insufficient'
              // Aquí se suman las respuestas de todas las skills: «menos de 7
              // respuestas» contradecía un total de 40. Lo que falta es por skill.
              ? t('bands.why.insufficientPerSkill', { n: MIN_EVIDENCE_ANSWERS })
              : t('home.bandCounts', {
                strong: bandCount('strong'),
                developing: bandCount('developing'),
                insufficient: bandCount('insufficient'),
              })}
          </p>
        </motion.section>

        <motion.section className={styles.next} variants={listItemVariants} aria-label={t('home.nextStep')}>
          <p className={styles.nextLabel}>{t('home.nextStep')}</p>
          <p className={styles.nextName} data-testid="home-next">
            {nextLesson
              ? t('home.nextLesson', { name: lang === 'es' ? nextLesson.name_es : nextLesson.name_en })
              : t('home.nextStudy')}
          </p>
          <p className={styles.nextHint}>
            {curFailed ? t('home.curriculumError') : nextLesson ? t('home.nextLessonHint') : t('home.nextHint')}
          </p>
          {curFailed ? (
            // Segundo §7 de 43.5: si el currículo no carga no hay forma de
            // saber la siguiente lección; lanzar un quiz entonces es lo mismo
            // que pulsar mientras carga. Se ofrece reintentar.
            <motion.button className={styles.btnStudy} onClick={cur.reload} whileTap={{ scale: 0.98 }}>
              {t('home.retry')}
            </motion.button>
          ) : (
          <motion.button
            className={styles.btnStudy}
            // §7 de 43.5: mientras carga el currículo de la ruta activa no se
            // sabe cuál es la siguiente lección; pulsar entonces lanzaba un quiz
            // y el backend respondía `needs_lesson`. Sin ruta activa no hay
            // «siguiente lección»: decide el backend (practica si hay lección
            // vista; si no, «Empieza por la lección» → «Ir a las lecciones»).
            disabled={Boolean(activeTrackId) && cur.loading}
            onClick={() => {
              if (nextLessonId) startLesson(nextLessonId);
              else startQuiz('study', 10, activeTrackId ? { trackId: activeTrackId } : undefined);
            }}
            whileTap={{ scale: 0.98 }}
          >
            {t('home.studyNow')}
          </motion.button>
          )}
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
                <button type="button" className={styles.btnSecondary} onClick={() => startQuiz('review', reviewsDue, activeTrackId ? { trackId: activeTrackId } : undefined)}>
                  {t('home.review')}
                </button>
              </>
            ) : (
              // «Vuelve mañana» no casa con una lista de skills que se olvidan hoy.
              <p className={styles.muted}>
                {decaying.data && decaying.data.length > 0 ? t('home.reviewCalmDecaying') : t('home.reviewCalm')}
              </p>
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
            <h2 className={styles.sectionTitle}>{activeTrackId ? t('home.otherTracks') : t('home.yourTracks')}</h2>
            <button type="button" className={styles.link} onClick={() => setScreen('tracks')}>
              {t('home.allTracks')} →
            </button>
          </div>
          <div className={styles.trackList}>
            {shownTracks.map((tr) => (
              <button key={tr.track_id} type="button" className={styles.trackRow} onClick={() => openTrack(tr.track_id)}>
                <span className={styles.trackIcon} aria-hidden="true"><TrackIcon trackId={tr.track_id} fallback={tr.icon} size={28} /></span>
                <span className={styles.trackBody}>
                  <span className={styles.trackName}>{lang === 'es' ? tr.name_es : tr.name_en}</span>
                  {/* Sin ninguna dominada, una barra vacía no dice nada: basta el recuento. */}
                  {tr.skills_mastered > 0 && (
                    <ProgressBar
                      value={tr.skills_mastered}
                      max={Math.max(tr.total_skills, 1)}
                      label={lang === 'es' ? tr.name_es : tr.name_en}
                      color="var(--le-blue)"
                      height={6}
                    />
                  )}
                  <span className={styles.trackNumbers}>
                    <span>{tr.skills_mastered}/{tr.total_skills} {t('home.skillsMastered')}</span>
                  </span>
                </span>
              </button>
            ))}
          </div>
        </motion.section>
      )}

      {/* Sin misiones de hoy no hay nada que enseñar: una tarjeta «0/0» vacía, no. */}
      {missions.data?.length !== 0 && (
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
                    {missionsJustDone.includes(m.mission.id) && (
                      <svg className={styles.check} viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" data-testid="mission-check">
                        <motion.path
                          d="M3 8.5 6.5 12 13 4.5"
                          initial={reduceMotion ? false : { pathLength: 0 }}
                          animate={{ pathLength: 1 }}
                          transition={{ duration: 0.3, ease: 'easeOut' }}
                        />
                      </svg>
                    )}
                    {m.completed ? t('home.done') : `+${m.mission.xp_reward} XP`}
                  </span>
                </div>
              );
            })}
          </Card>
        </motion.div>
      )}

      {/* Territorio: cada skill practicada con su dominio real (BKT, 24.4). */}
      {(skills.data?.length ?? 0) > 0 && (
        <motion.section className={styles.section} variants={listItemVariants}>
          <div className={styles.cardHeader}>
            <h2 className={styles.sectionTitle}>{t('home.territory')}</h2>
            {/* ADR-60: el Elo es un número crudo del modelo; solo para depurar. */}
            {import.meta.env.DEV && avgElo !== undefined && (
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
                const skillBand = bandForSkill(s);
                const name = lang === 'es' ? s.name_es : s.name_en;
                const evidence = t('bands.evidence', { answers: s.attempts, correct: s.correct_count });
                return (
                  <div
                    key={s.skill_id}
                    className={`${styles.node} ${styles[BAND_CLASS[skillBand]]} ${skillsJustUp.includes(s.skill_id) ? styles.bandUp : ''}`}
                    data-band-up={skillsJustUp.includes(s.skill_id) || undefined}
                    role="group"
                    aria-label={`${name}: ${t(`bands.${skillBand}`)} (${evidence})`}
                  >
                    <span className={styles.nodeName}>{name}</span>
                    <span className={styles.nodeMastery}>{t(`bands.${skillBand}`)}</span>
                    <span className={styles.nodeEvidence}>{evidence}</span>
                  </div>
                );
              })}
          </div>
        </motion.section>
      )}

      <motion.section className={styles.section} variants={listItemVariants}>
        <h2 className={styles.sectionTitle}>{t('home.tools')}</h2>
        <div className={styles.tools}>
          {/* 43.7 (ADR-65 D9): el playground sale de Hoy; se abre desde la lección
              («Probar este código») y, libre, desde Rutas. */}
          <button type="button" className={styles.tool} onClick={() => openProjects(null)}>
            <span aria-hidden="true">🏗️</span>
            <span className={styles.toolName}>{t('project.title')}</span>
            <span className={styles.toolMeta}>{t('home.projectsMeta')}</span>
          </button>
        </div>
      </motion.section>
    </motion.div>
  );
}
