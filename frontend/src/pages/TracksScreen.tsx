import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../stores/useAppStore';
import { Card } from '../components/common/Card';
import { ProgressBar } from '../components/common/ProgressBar';
import { ProgressMap } from '../components/tracks/ProgressMap';
import { useApi } from '../hooks/useApi';
import { pageVariants } from '../lib/motion';
import {
  content as contentApi,
  exams as examsApi,
  progress as progressApi,
  glossary as glossaryApi,
  type CurriculumModule,
  type TrackExamBlueprint,
  type TrackRead,
} from '../services/api';
import styles from './TracksScreen.module.css';

type View = 'curriculum' | 'map' | 'glossary';

// No hardcoded track list: it is fetched from the API (task Q.14). Keeping a
// copy here is how the AWS certification track stayed invisible in the app for
// a whole session while being loaded, stored and served correctly.
const ICON_FALLBACK = '📘';

function statusMeta(status: CurriculumModule['status']) {
  switch (status) {
    case 'completed': return { icon: '✓', color: 'var(--le-green)', bg: 'var(--le-green-light)' };
    case 'available': return { icon: '▶', color: 'var(--le-brand)', bg: 'var(--le-brand-light)' };
    default: return { icon: '🔒', color: 'var(--le-text-muted)', bg: 'var(--le-border-light)' };
  }
}

export function TracksScreen() {
  const lang = useAppStore((s) => s.user.language);
  const startQuiz = useAppStore((s) => s.startQuiz);
  const startLesson = useAppStore((s) => s.startLesson);
  const startMockExam = useAppStore((s) => s.startMockExam);
  const startTrackExam = useAppStore((s) => s.startTrackExam);
  const startReadiness = useAppStore((s) => s.startReadiness);
  const startPlacement = useAppStore((s) => s.startPlacement);
  const [track, setTrack] = useState('track01');
  const [view, setView] = useState<View>('curriculum');
  const { t } = useTranslation();
  const { data: tracks, loading: tracksLoading, error: tracksError } =
    useApi<TrackRead[]>(() => contentApi.tracks(), []);
  const trackList = tracks ?? [];
  const selected = trackList.find((tr) => tr.id === track);
  // Refetched per track: the blueprint is derived from that track's skills, so
  // one cached answer reused across tracks would advertise the wrong exam.
  const { data: trackExamBlueprint } = useApi<TrackExamBlueprint>(
    () => examsApi.trackBlueprint(track),
    [track],
  );

  return (
    <div className={styles.screen}>
      <h1 className={styles.title}>{t('tracks.title')}</h1>
      <p className={styles.subtitle}>{t('tracks.subtitle')}</p>

      {/* Track selector */}
      <div className={styles.trackRow} role="tablist" aria-label={t('tracks.title')}>
        {trackList.map((tr) => (
          <motion.button
            key={tr.id}
            role="tab"
            aria-selected={track === tr.id}
            className={`${styles.trackChip} ${track === tr.id ? styles.trackChipActive : ''}`}
            onClick={() => setTrack(tr.id)}
            whileTap={{ scale: 0.93 }}
          >
            <span className={styles.trackChipIcon}>{tr.icon || ICON_FALLBACK}</span>
            <span>{lang === 'es' ? tr.name_es : tr.name_en}</span>
          </motion.button>
        ))}
        {tracksLoading && trackList.length === 0 && (
          <span className={styles.trackChip}>{t('loading')}</span>
        )}
      </div>

      {!tracksLoading && trackList.length === 0 && (
        <p className={styles.tracksError} role="alert">
          {tracksError ?? t('tracks.empty')}
        </p>
      )}

      {/* View toggle — 3 tabs: Curriculum | Map | Glossary */}
      <div className={styles.viewToggle} role="tablist">
        {(['curriculum', 'map', 'glossary'] as View[]).map((v) => (
          <button
            key={v}
            role="tab"
            aria-selected={view === v}
            className={`${styles.viewBtn} ${view === v ? styles.viewBtnActive : ''}`}
            onClick={() => setView(v)}
          >
            {v === 'curriculum' ? t('tracks.curriculum') : v === 'map' ? t('tracks.map') : t('tracks.glossary')}
          </button>
        ))}
      </div>

      {/* La prueba de nivel es por ruta, asi que vive junto al selector de
          rutas. Antes la pantalla existia y no la abria nadie. */}
      {selected && (
        <motion.button
          className={styles.placementCta}
          onClick={() => startPlacement(selected.id)}
          whileTap={{ scale: 0.97 }}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <span className={styles.mockExamTitle}>{t('tracks.placementCta')}</span>
          <span className={styles.mockExamMeta}>{t('tracks.placementSub')}</span>
        </motion.button>
      )}

      {selected?.is_certification && selected.exam_question_count && selected.exam_duration_minutes && (
        <>
          <motion.button
            className={styles.mockExamCta}
            onClick={() => selected && startMockExam(selected.id, selected.exam_question_count ?? 65, selected.exam_duration_minutes ?? 90)}
            whileTap={{ scale: 0.97 }}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <span className={styles.mockExamTitle}>{t('mockExam.title')}</span>
            <span className={styles.mockExamMeta}>
              {t('mockExam.format', {
                count: selected.exam_question_count,
                minutes: selected.exam_duration_minutes,
              })}
            </span>
          </motion.button>
          <motion.button
            className={styles.readinessCta}
            onClick={() => selected && startReadiness(selected.id)}
            whileTap={{ scale: 0.97 }}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
          >
            <span className={styles.mockExamTitle}>{t('readiness.title')}</span>
            <span className={styles.mockExamMeta}>{t('readiness.ctaSubtitle')}</span>
          </motion.button>
        </>
      )}

      {/* Final exam, for the tracks that are courses rather than rehearsals of
          somebody else's certification (17.2). The blueprint is fetched rather
          than guessed: the figures on this button have to be the ones the exam
          will actually use, or the learner commits to the wrong thing. */}
      {selected && !selected.is_certification && trackExamBlueprint && (
        <motion.button
          className={styles.mockExamCta}
          onClick={() =>
            startTrackExam('track_final', selected.id, {
              questions: trackExamBlueprint.questions,
              durationMinutes: trackExamBlueprint.duration_minutes,
              passPct: trackExamBlueprint.pass_pct,
            })
          }
          whileTap={{ scale: 0.97 }}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <span className={styles.mockExamTitle}>{t('trackExam.title')}</span>
          <span className={styles.mockExamMeta}>
            {t('trackExam.format', {
              count: trackExamBlueprint.questions,
              minutes: trackExamBlueprint.duration_minutes,
              pass: trackExamBlueprint.pass_pct,
            })}
          </span>
        </motion.button>
      )}

      <AnimatePresence mode="wait">
        <motion.div key={`${track}-${view}`} variants={pageVariants} initial="initial" animate="animate" exit="exit">
          {view === 'curriculum'
            ? <CurriculumView track={track} lang={lang} startQuiz={startQuiz} startLesson={startLesson} />
            : view === 'map'
              ? <MapView track={track} lang={lang} startQuiz={startQuiz} startLesson={startLesson} />
              : <GlossaryView track={track} lang={lang} />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

function MapView({
  track, lang, startQuiz,
}: {
  track: string;
  lang: 'es' | 'en';
  startQuiz: (mode: 'study', total: number, opts?: { trackId?: string; skillId?: string }) => void;
  startLesson: (skillId: string) => void;
}) {
  const { t } = useTranslation();
  const cur = useApi(() => progressApi.curriculum(track), [track]);

  if (cur.loading) return <p className={styles.muted}>{t('tracks.loading')}</p>;
  if (cur.error || !cur.data) return <p className={styles.muted}>{cur.error ?? t('tracks.loading')}</p>;

  const modules = cur.data.modules;

  const handleSelect = (mod: CurriculumModule) => {
    if (mod.status !== 'locked') {
      startQuiz('study', 10, { trackId: track });
    }
  };

  return <ProgressMap modules={modules} lang={lang} onSelect={handleSelect} />;
}

function CurriculumView({
  track, lang, startQuiz, startLesson,
}: {
  track: string;
  lang: 'es' | 'en';
  startQuiz: (mode: 'study', total: number, opts?: { trackId?: string; skillId?: string }) => void;
  startLesson: (skillId: string) => void;
}) {
  const { t } = useTranslation();
  const cur = useApi(() => progressApi.curriculum(track), [track]);
  const [openModule, setOpenModule] = useState<string | null>(null);

  if (cur.loading) return <p className={styles.muted}>{t('tracks.loading')}</p>;
  if (cur.error || !cur.data) return <p className={styles.muted}>{cur.error ?? t('tracks.loading')}</p>;

  const modules = cur.data.modules;
  const threshold = cur.data.mastery_threshold;
  const completed = modules.filter((m) => m.status === 'completed').length;

  const LEVEL_LABELS: Record<number, { es: string; en: string }> = {
    1: { es: 'Fundamentos', en: 'Fundamentals' },
    2: { es: 'Intermedio', en: 'Intermediate' },
    3: { es: 'Avanzado', en: 'Advanced' },
  };

  const levels = [1, 2, 3].filter((lvl) => modules.some((m) => m.level === lvl));

  return (
    <>
      <Card className={styles.overviewCard}>
        <div className={styles.overviewText}>
          <span className={styles.overviewIcon}>{cur.data.icon}</span>
          <div>
            <p className={styles.overviewName}>{lang === 'es' ? cur.data.name_es : cur.data.name_en}</p>
            <p className={styles.overviewMeta}>{completed}/{modules.length} {t('tracks.modulesDone')}</p>
          </div>
        </div>
        <ProgressBar
          value={completed}
          max={modules.length}
          label={t('a11y.progressModules', { done: completed, total: modules.length })}
          color="var(--le-green)"
          height={10}
        />
      </Card>

      {levels.map((lvl) => {
        const lvlMods = modules.filter((m) => m.level === lvl);
        const lvlLabel = LEVEL_LABELS[lvl] ?? { es: `Nivel ${lvl}`, en: `Level ${lvl}` };
        const lvlCompleted = lvlMods.filter((m) => m.status === 'completed').length;
        return (
          <div key={lvl} className={styles.levelSection}>
            <div className={styles.levelHeader}>
              <span className={styles.levelBadge}>{lvl}</span>
              <span className={styles.levelTitle}>{lang === 'es' ? lvlLabel.es : lvlLabel.en}</span>
              <span className={styles.levelMeta}>{lvlCompleted}/{lvlMods.length}</span>
            </div>
            <div className={styles.spine}>
        {lvlMods.map((m, _i) => {
          const i = modules.indexOf(m);
          const meta = statusMeta(m.status);
          const isOpen = openModule === m.id;
          const locked = m.status === 'locked';
          const prereq = i > 0 ? modules[i - 1] : null;
          return (
            <div key={m.id} className={styles.moduleWrap}>
              {i > 0 && (
                <div
                  className={`${styles.connector} ${m.prerequisite_met ? styles.connectorMet : ''}`}
                  aria-hidden="true"
                />
              )}
              <Card className={`${styles.module} ${locked ? styles.moduleLocked : ''}`}>
                <button
                  className={styles.moduleHeader}
                  onClick={() => setOpenModule(isOpen ? null : m.id)}
                  aria-expanded={isOpen}
                >
                  <span className={styles.moduleBadge} style={{ background: meta.bg, color: meta.color }}>
                    {meta.icon}
                  </span>
                  <span className={styles.moduleInfo}>
                    <span className={styles.moduleName}>{lang === 'es' ? m.name_es : m.name_en}</span>
                    <span className={styles.moduleSub}>
                      {locked
                        ? `${t('tracks.lockedUntil')} ${prereq ? (lang === 'es' ? prereq.name_es : prereq.name_en) : ''} · ${Math.round(m.min_mastery_to_unlock * 100)}%`
                        : `${m.skills.length} ${t('tracks.skills')} · ${Math.round(m.average_mastery * 100)}% ${t('tracks.mastery')}`}
                    </span>
                  </span>
                  <span className={styles.chevron}>{isOpen ? '▾' : '▸'}</span>
                </button>

                {!locked && (
                  <div className={styles.moduleBar}>
                    <ProgressBar
                      value={m.average_mastery * 100}
                      max={100}
                      label={t('a11y.progressMastery', { name: lang === 'es' ? m.name_es : m.name_en })}
                      color={m.status === 'completed' ? 'var(--le-green)' : 'var(--le-brand)'}
                      height={6}
                    />
                  </div>
                )}

                <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    className={styles.skills}
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2, ease: 'easeInOut' }}
                    style={{ overflow: 'hidden' }}
                  >
                    {m.description_es && (
                      <p className={styles.moduleDesc}>{lang === 'es' ? m.description_es : m.description_en}</p>
                    )}
                    {m.skills.map((s, si) => (
                      <motion.div
                        key={s.skill_id}
                        className={styles.skill}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: si * 0.04, duration: 0.15 }}
                      >
                        <span className={styles.skillDot} style={{
                          background: s.mastered ? 'var(--le-green)' : s.attempts > 0 ? 'var(--le-brand)' : 'var(--le-border)',
                        }} />
                        <span className={styles.skillName}>{lang === 'es' ? s.name_es : s.name_en}</span>
                        <span className={styles.skillPct} style={{ color: s.mastered ? 'var(--le-green)' : undefined }}>
                          {s.mastered ? '★' : `${Math.round(s.p_known * 100)}%`}
                        </span>
                      </motion.div>
                    ))}
                    {locked ? (
                      <p className={styles.lockNote}>🔒 {t('tracks.lockNote')}</p>
                    ) : (
                      <div className={styles.skillActions}>
                        <button
                          className={styles.learnBtn}
                          onClick={() => startLesson(m.skills?.[0]?.skill_id ?? '')}
                          title={t('tracks.learn')}
                        >
                          📖 {t('tracks.learn')}
                        </button>
                        <button
                          className={styles.practiceBtn}
                          onClick={() => startQuiz('study', 10, { trackId: track })}
                        >
                          {m.status === 'completed' ? t('tracks.reinforce') : t('tracks.practice')}
                        </button>
                      </div>
                    )}
                  </motion.div>
                )}
                </AnimatePresence>
              </Card>
            </div>
          );
        })}
            </div>
          </div>
        );
      })}
      <p className={styles.footnote}>{t('tracks.thresholdNote', { n: Math.round(threshold * 100) })}</p>
    </>
  );
}

function GlossaryView({ track, lang }: { track: string; lang: 'es' | 'en' }) {
  const { t } = useTranslation();
  const gloss = useApi(() => glossaryApi.forTrack(track), [track]);
  const [q, setQ] = useState('');

  useEffect(() => { setQ(''); }, [track]);

  const terms = useMemo(() => {
    const data = gloss.data ?? [];
    const needle = q.trim().toLowerCase();
    if (!needle) return data;
    return data.filter((term) =>
      term.term_es.toLowerCase().includes(needle) ||
      term.term_en.toLowerCase().includes(needle) ||
      term.definition_es.toLowerCase().includes(needle) ||
      term.definition_en.toLowerCase().includes(needle)
    );
  }, [gloss.data, q]);

  if (gloss.loading) return <p className={styles.muted}>{t('tracks.loading')}</p>;
  if (gloss.error) return <p className={styles.muted}>{gloss.error}</p>;

  return (
    <>
      <input
        className={styles.search}
        type="search"
        placeholder={t('tracks.searchTerms')}
        value={q}
        onChange={(e) => setQ(e.target.value)}
        aria-label={t('tracks.searchTerms')}
      />
      {terms.length === 0 && <p className={styles.muted}>{t('tracks.noTerms')}</p>}
      <div className={styles.terms}>
        {terms.map((term) => {
          const primary = lang === 'es' ? term.term_es : term.term_en;
          const secondary = lang === 'es' ? term.term_en : term.term_es;
          const def = lang === 'es' ? term.definition_es : term.definition_en;
          return (
            <Card key={term.id} className={styles.term}>
              <div className={styles.termHead}>
                <span className={styles.termName}>{primary}</span>
                {secondary && secondary !== primary && (
                  <span className={styles.termAlt}>{secondary}</span>
                )}
              </div>
              <p className={styles.termDef}>{def}</p>
              {term.source && <span className={styles.termSource}>📖 {term.source}</span>}
            </Card>
          );
        })}
      </div>
    </>
  );
}
