import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { useAppStore } from '../stores/useAppStore';
import { ProgressBar } from '../components/common/ProgressBar';
import { Card } from '../components/common/Card';
import { StreakFreezeShop } from '../components/home/StreakFreezeShop';
import { useApi } from '../hooks/useApi';
import { progress as progressApi, gamification, type SkillMasteryDetail } from '../services/api';
import { listVariants, listItemVariants, flickerVariants } from '../lib/motion';
import styles from './HomeScreen.module.css';

// Saludo entero por clave: «Buenos» + «noches» salía «Buenos noches».
function greetingKey(): 'home.greetingMorning' | 'home.greetingAfternoon' | 'home.greetingEvening' {
  const h = new Date().getHours();
  return h < 12 ? 'home.greetingMorning' : h < 19 ? 'home.greetingAfternoon' : 'home.greetingEvening';
}

export function HomeScreen() {
  const user = useAppStore((s) => s.user);
  const startQuiz = useAppStore((s) => s.startQuiz);
  const lang = user.language;
  const { t } = useTranslation();

  const dash = useApi(() => progressApi.dashboard(), []);
  const missions = useApi(() => gamification.missions(), []);
  const decaying = useApi(() => progressApi.decaying(), []);
  const skills = useApi(() => progressApi.skills(), []);

  const overallMastery = dash.data
    ? Math.round(
        (dash.data.tracks.reduce((sum, tr) => sum + tr.average_mastery, 0) /
          Math.max(1, dash.data.tracks.length)) * 100
      )
    : 0;
  const reviewsDue = dash.data?.reviews_due ?? 0;
  const streak = dash.data?.current_streak ?? user.currentStreak;
  const topTrack = dash.data?.tracks.slice().sort((a, b) => a.average_mastery - b.average_mastery)[0];

  // Elo medio real de las skills con al menos un intento (24.4: lo que aquí
  // se llamaba "nivel" era XP, no Elo — el motor sí calcula un Elo por
  // skill, `skills.data[].elo_rating`, y no se mostraba en ningún sitio).
  // undefined mientras no haya ninguna skill con intentos: mostrar 1500 (el
  // valor de arranque, sin señal real) sería un dato inventado.
  const practicedSkills = skills.data?.filter((s) => s.attempts > 0) ?? [];
  const avgElo = practicedSkills.length > 0
    ? Math.round(practicedSkills.reduce((sum, s) => sum + s.elo_rating, 0) / practicedSkills.length)
    : undefined;

  return (
    <motion.div
      className={styles.screen}
      variants={listVariants}
      initial="initial"
      animate="animate"
    >
      {/* Hero */}
      <motion.div className={styles.hero} variants={listItemVariants}>
        <p className={styles.heroGreeting}>{t(greetingKey())}, {user.displayName.split(' ')[0]}</p>
        <h1 className={styles.heroTitle}>{t('home.ready')}</h1>
        <div className={styles.heroStats}>
          {[
            { val: user.level, label: t('home.level') },
            { val: `${overallMastery}%`, label: t('home.mastery') },
            { val: streak, label: t('home.streak'), isStreak: true },
          ].map(({ val, label, isStreak }) => (
            <div key={label} className={styles.heroStat}>
              <motion.span
                className={styles.heroStatVal}
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: 'spring', stiffness: 260, damping: 18, delay: 0.15 }}
              >
                {isStreak
                  ? <motion.span variants={flickerVariants} animate="animate">{val} 🔥</motion.span>
                  : val}
              </motion.span>
              <span className={styles.heroStatLabel}>{label}</span>
            </div>
          ))}
        </div>
        <motion.button
          className={styles.btnStudy}
          onClick={() => startQuiz('study', 10)}
          whileTap={{ scale: 0.96 }}
          whileHover={{ scale: 1.02 }}
          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
        >
          {t('home.studyNow')}
        </motion.button>
        <div className={styles.heroCircle1} aria-hidden="true" />
        <div className={styles.heroCircle2} aria-hidden="true" />
      </motion.div>

      {/* Prediction */}
      {topTrack && (
        <motion.div variants={listItemVariants}>
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
        </motion.div>
      )}

      {/* Decaying skills — FSRS, made visible */}
      {decaying.data && decaying.data.length > 0 && (
        <motion.div variants={listItemVariants}>
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
        </motion.div>
      )}

      {/* Missions */}
      <motion.div variants={listItemVariants}>
        <Card>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>{t('home.missions')}</h2>
            {missions.data && (
              <span className={`${styles.badge} ${styles.badgeWarning}`}>
                {missions.data.filter((m) => m.completed).length}/{missions.data.length}
              </span>
            )}
          </div>
          {missions.loading && <p className={styles.muted}>{t('home.loading')}</p>}
          {missions.data?.map((m, i) => (
            <motion.div
              key={m.mission.id}
              className={styles.mission}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.06, type: 'spring', stiffness: 300, damping: 20 }}
            >
              <motion.div
                className={styles.missionIcon}
                style={{ background: m.completed ? 'var(--le-green-light)' : 'var(--le-brand-light)' }}
                animate={m.completed ? { scale: [1, 1.15, 1] } : {}}
                transition={{ duration: 0.4 }}
              >
                {m.mission.type === 'questions_answered' ? '🎯' : m.mission.type === 'perfect_combo' ? '🔥' : m.mission.type === 'xp_earned' ? '⚡' : '✅'}
              </motion.div>
              <div className={styles.missionInfo}>
                <p className={styles.missionTitle}>{lang === 'es' ? m.mission.name_es : m.mission.name_en}</p>
                <ProgressBar
                  value={m.progress}
                  max={m.mission.target_value}
                  label={t('a11y.progressMission', { name: lang === 'es' ? m.mission.name_es : m.mission.name_en })}
                  color={m.completed ? 'var(--le-green)' : 'var(--le-brand)'}
                  height={10}
                />
              </div>
              <span className={styles.missionXp} style={{ color: m.completed ? 'var(--le-success-text)' : 'var(--le-brand-text)' }}>
                {m.completed ? t('home.done') : `+${m.mission.xp_reward} XP`}
              </span>
            </motion.div>
          ))}
        </Card>
      </motion.div>

      {/* Streak card */}
      <motion.div variants={listItemVariants}>
        <Card>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>
              {t('home.yourStreak')}: {streak} {t('home.days', { count: streak })}{' '}
              <motion.span variants={flickerVariants} animate="animate" style={{ display: 'inline-block' }}>🔥</motion.span>
            </h2>
            <span className={`${styles.badge} ${styles.badgeSuccess}`}>
              {t('home.best')}: {dash.data?.max_streak ?? user.maxStreak}
            </span>
          </div>
          <StreakCalendar streak={streak} />
          <p className={styles.streakNote}>
            <span aria-hidden="true">🧊 </span>
            {t('home.freeze', { count: user.streakFreezeAvailable })} {t('home.streakKind')}
          </p>
          <StreakFreezeShop />
        </Card>
      </motion.div>

      {/* Review reminder */}
      {reviewsDue > 0 && (
        <motion.div variants={listItemVariants}>
          <Card className={styles.reviewCard}>
            <motion.span
              style={{ fontSize: '2rem' }}
              animate={{ rotate: [-8, 8, -6, 6, -4, 4, 0] }}
              transition={{ duration: 0.5, delay: 1 }}
            >
              ⏰
            </motion.span>
            <div style={{ flex: 1 }}>
              <p className={styles.missionTitle}>{reviewsDue} {t('home.reviewsPending')}</p>
              <p style={{ fontSize: 'var(--le-fs-xs)', color: 'var(--le-text-secondary)' }}>
                ~{Math.max(1, Math.round(reviewsDue * 1.5))} min
              </p>
            </div>
            <motion.button
              className={styles.btnReview}
              onClick={() => startQuiz('review', reviewsDue)}
              whileTap={{ scale: 0.94 }}
            >
              {t('home.review')}
            </motion.button>
          </Card>
        </motion.div>
      )}
      {/* Playground shortcut */}
      <motion.div variants={listItemVariants}>
        <Card className={styles.playgroundCard}>
          <span style={{ fontSize: '1.5rem' }}>💻</span>
          <div style={{ flex: 1 }}>
            <p className={styles.missionTitle}>{t('playground.openPlayground')}</p>
            <p style={{ fontSize: 'var(--le-fs-xs)', color: 'var(--le-text-secondary)' }}>
              Python · SQL · JS
            </p>
          </div>
          <motion.button
            className={styles.btnReview}
            onClick={() => useAppStore.getState().setScreen('playground')}
            whileTap={{ scale: 0.94 }}
          >
            →
          </motion.button>
        </Card>
      </motion.div>

      {/* Projects shortcut */}
      <motion.div variants={listItemVariants}>
        <Card className={styles.playgroundCard}>
          <span style={{ fontSize: '1.5rem' }}>🏗️</span>
          <div style={{ flex: 1 }}>
            <p className={styles.missionTitle}>{t('project.title')}</p>
            <p style={{ fontSize: 'var(--le-fs-xs)', color: 'var(--le-text-secondary)' }}>
              {t('project.step')}-by-{t('project.step').toLowerCase()}
            </p>
          </div>
          <motion.button
            className={styles.btnReview}
            onClick={() => useAppStore.getState().setScreen('projects')}
            whileTap={{ scale: 0.94 }}
          >
            →
          </motion.button>
        </Card>
      </motion.div>

      {/* Territorio: cada skill practicada con su dominio real (BKT). La idea
          es de 24.4; el numero, a diferencia de entonces, sale del motor. */}
      {(skills.data?.length ?? 0) > 0 && (
        <motion.section className={styles.territory} variants={listItemVariants}>
          <div className={styles.cardHeader}>
            <h2 className={styles.sectionTitle}>{t('home.territory')}</h2>
            {avgElo !== undefined && (
              <span className={`${styles.badge} ${styles.badgeSuccess}`} title={t('home.eloHint')}>
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
                const estado = s.p_known >= 0.75 ? 'dominated' : s.p_known >= 0.4 ? 'partial' : 'frontier';
                return (
                  <div
                    key={s.skill_id}
                    className={`${styles.territoryNode} ${styles[estado]}`}
                    role="group"
                    aria-label={`${lang === 'es' ? s.name_es : s.name_en}: ${pct}%`}
                  >
                    <span className={styles.nodeName}>{lang === 'es' ? s.name_es : s.name_en}</span>
                    <span className={styles.nodeMastery}>{pct}%</span>
                    <span className={styles.nodeBar} style={{ width: `${pct}%` }} aria-hidden="true" />
                  </div>
                );
              })}
          </div>
        </motion.section>
      )}

    </motion.div>
  );
}

function StreakCalendar({ streak }: { streak: number }) {
  const { t, i18n } = useTranslation();
  // Inicial de cada día de lunes a domingo en el idioma activo (L M X J V S D
  // en ES, M T W T F S S en EN). El 1 de enero de 2024 fue lunes.
  const fmt = new Intl.DateTimeFormat(i18n.language, { weekday: 'narrow' });
  const days = Array.from({ length: 7 }, (_, i) => fmt.format(new Date(2024, 0, 1 + i)));
  const TOTAL = 28;
  const todayIdx = 27;
  return (
    <div className={styles.streakGrid}>
      {days.map((d, i) => (<div key={i} className={styles.streakLabel}>{d}</div>))}
      {Array.from({ length: TOTAL }).map((_, i) => {
        const isToday = i === todayIdx;
        const active = i > todayIdx - Math.min(streak, TOTAL) && i <= todayIdx;
        let cls = styles.streakDay;
        if (isToday) cls += ` ${styles.today}`;
        else if (active) cls += ` ${styles.active}`;
        return (
          <motion.div
            key={i}
            className={cls}
            initial={active ? { scale: 0 } : false}
            animate={active ? { scale: 1 } : {}}
            transition={{ delay: (TOTAL - i) * 0.015, type: 'spring', stiffness: 300, damping: 20 }}
          >
            {isToday ? t('home.today') : ''}
          </motion.div>
        );
      })}
    </div>
  );
}
