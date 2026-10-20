import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../stores/useAppStore';
import { Badge } from '../components/common/Badge';
import { ProgressBar } from '../components/common/ProgressBar';
import { BandChip } from '../components/common/BandChip';
import { ProgressMap } from '../components/tracks/ProgressMap';
import { useApi } from '../hooks/useApi';
import { pageVariants } from '../lib/motion';
import { retiredCertificationFor } from '../lib/retiredCertifications';
import { bandForSkill, overallBand } from '../lib/evidenceBand';
import {
  content as contentApi,
  exams as examsApi,
  progress as progressApi,
  glossary as glossaryApi,
  projects as projectsApi,
  type CurriculumModule,
  type CurriculumSkill,
  type TestOutBlueprint,
  type TrackExamBlueprint,
  type TrackRead,
} from '../services/api';
import { canPractice } from '../lib/nextStep';
import styles from './TracksScreen.module.css';
import { TrackIcon } from '../components/common/AppIcon';
import { Loading } from '../components/common/Loading';

type View = 'curriculum' | 'map' | 'glossary';
type Filter = 'all' | 'learn' | 'cert';
type StartQuiz = (mode: 'study', total: number, opts?: { trackId?: string; skillId?: string }) => void;

// No hardcoded track list: it is fetched from the API (task Q.14). Keeping a
// copy here is how the AWS certification track stayed invisible in the app for
// a whole session while being loaded, stored and served correctly.
const ICON_FALLBACK = '📘';

// Habilidad más floja sin dominar: la que abre «Aprender» y la del mapa.
function weakestSkill(skills: CurriculumSkill[]): string {
  const weakest = [...skills].filter((s) => !s.mastered).sort((a, b) => a.p_known - b.p_known)[0];
  return weakest?.skill_id ?? skills[0]?.skill_id ?? '';
}

const pct = (x: number) => Math.round(x * 100);

export function TracksScreen() {
  const lang = useAppStore((s) => s.user.language);
  const selectedTrackId = useAppStore((s) => s.selectedTrackId);
  const openTrack = useAppStore((s) => s.openTrack);
  const { t } = useTranslation();
  // «Cambiar» (Hoy, Yo) abre el catálogo; el aviso se consume al montar.
  const [browsing, setBrowsing] = useState(() => {
    const browse = useAppStore.getState().tracksBrowse;
    if (browse) useAppStore.setState({ tracksBrowse: false });
    return browse;
  });
  const { data: tracks, loading: tracksLoading, error: tracksError } =
    useApi<TrackRead[]>(() => contentApi.tracks(), []);
  const trackList = tracks ?? [];
  // La ruta guardada puede no existir ya (contenido retirado): la primera vale.
  const selected = trackList.find((tr) => tr.id === selectedTrackId) ?? trackList[0];

  if (!tracksLoading && trackList.length === 0) {
    return (
      <div className={styles.screen}>
        <h1 className={styles.title}>{t('tracks.title')}</h1>
        <p className={styles.error} role="alert">{tracksError ?? t('tracks.empty')}</p>
      </div>
    );
  }

  if (browsing || !selected) {
    return (
      <Catalogue
        tracks={trackList}
        loading={tracksLoading}
        selectedId={selected?.id}
        lang={lang}
        onPick={(id) => {
          openTrack(id);
          setBrowsing(false);
          window.scrollTo(0, 0);
        }}
      />
    );
  }

  return <TrackDetail key={selected.id} track={selected} lang={lang} onBrowse={() => setBrowsing(true)} />;
}

function Catalogue({
  tracks, loading, selectedId, lang, onPick,
}: {
  tracks: TrackRead[];
  loading: boolean;
  selectedId: string | undefined;
  lang: 'es' | 'en';
  onPick: (id: string) => void;
}) {
  const { t } = useTranslation();
  const [filter, setFilter] = useState<Filter>('all');
  const dash = useApi(() => progressApi.dashboard(), []);
  // ADR-60: la ruta se resume en skills dominadas, no en un % del modelo.
  const masteredById = new Map((dash.data?.tracks ?? []).map((m) => [m.track_id, { mastered: m.skills_mastered, total: m.total_skills }]));
  const counts: Record<Filter, number> = {
    all: tracks.length,
    learn: tracks.filter((tr) => !tr.is_certification).length,
    cert: tracks.filter((tr) => tr.is_certification).length,
  };
  const shown = tracks.filter((tr) =>
    filter === 'all' ? true : filter === 'cert' ? tr.is_certification : !tr.is_certification,
  );

  return (
    <div className={styles.screen}>
      <header className={styles.head}>
        <h1 className={styles.title}>{t('tracks.title')}</h1>
        <p className={styles.subtitle}>{t('tracks.subtitle')}</p>
      </header>

      <div className={styles.filters} role="tablist" aria-label={t('tracks.title')}>
        {(['all', 'learn', 'cert'] as Filter[]).map((f) => (
          <button
            key={f}
            type="button"
            role="tab"
            aria-selected={filter === f}
            className={`${styles.filter} ${filter === f ? styles.filterActive : ''}`}
            onClick={() => setFilter(f)}
          >
            {t(`tracks.filter_${f}`)} <span className={styles.filterCount}>{counts[f]}</span>
          </button>
        ))}
      </div>

      {loading && <Loading label={t('tracks.loading')} shape="line" />}

      <ul className={styles.catalogue}>
        {shown.map((tr) => {
          const name = lang === 'es' ? tr.name_es : tr.name_en;
          const prog = masteredById.get(tr.id);
          return (
            <li key={tr.id}>
              <button
                type="button"
                className={styles.trackItem}
                aria-current={tr.id === selectedId ? 'true' : undefined}
                onClick={() => onPick(tr.id)}
              >
                <span className={styles.trackIcon} aria-hidden="true">
                  <TrackIcon trackId={tr.id} fallback={tr.icon || ICON_FALLBACK} size={28} />
                  <span className={styles.hue} style={{ background: tr.color }} />
                </span>
                <span className={styles.trackBody}>
                  <span className={styles.trackName}>
                    {name}
                    {retiredCertificationFor(tr.id) && (
                      <Badge variant="orange" size="sm">{t('tracks.certRetiredBadge')}</Badge>
                    )}
                  </span>
                  <span className={styles.trackMeta}>
                    {tr.is_certification && tr.exam_question_count && tr.exam_duration_minutes
                      ? t('tracks.certMeta', {
                          count: tr.exam_question_count,
                          minutes: tr.exam_duration_minutes,
                          provider: tr.cert_provider ?? '',
                        })
                      : t('tracks.questions', { count: tr.total_questions })}
                  </span>
                  {prog !== undefined && prog.mastered > 0 && (
                    <ProgressBar value={prog.mastered} max={Math.max(prog.total, 1)} label={name} color="var(--le-blue)" height={4} />
                  )}
                </span>
                {prog !== undefined && prog.mastered > 0 && (
                  <span className={styles.trackPct}>{prog.mastered}/{prog.total}</span>
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function TrackDetail({ track, lang, onBrowse }: { track: TrackRead; lang: 'es' | 'en'; onBrowse: () => void }) {
  const { t } = useTranslation();
  const startQuiz = useAppStore((s) => s.startQuiz);
  const startLesson = useAppStore((s) => s.startLesson);
  const startMockExam = useAppStore((s) => s.startMockExam);
  const startTrackExam = useAppStore((s) => s.startTrackExam);
  const startReadiness = useAppStore((s) => s.startReadiness);
  const startPlacement = useAppStore((s) => s.startPlacement);
  const activeTrackId = useAppStore((s) => s.activeTrackId);
  const setActiveTrack = useAppStore((s) => s.setActiveTrack);
  // 43.4 (D5): al hacer tuya una ruta sin progreso se ofrece su prueba de nivel.
  const [offerPlacement, setOfferPlacement] = useState(false);
  const [view, setView] = useState<View>('curriculum');
  const cur = useApi(() => progressApi.curriculum(track.id), [track.id]);
  // 43.6 (ADR-65 D8): la entrada a Proyectos sale solo si la ruta tiene alguno.
  const trackProjects = useApi(() => projectsApi.list(track.id), [track.id]);
  const openProjects = useAppStore((s) => s.openProjects);
  const openPlayground = useAppStore((s) => s.openPlayground);
  // The blueprint is derived from that track's skills, so the figures on the
  // final-exam card are the ones the exam will actually use (17.2).
  const { data: blueprint } = useApi<TrackExamBlueprint>(
    () => examsApi.trackBlueprint(track.id),
    [track.id],
  );

  const modules = cur.data?.modules ?? [];
  const completed = modules.filter((m) => m.status === 'completed').length;
  const skillCount = modules.reduce((n, m) => n + m.skills.length, 0);
  const practised = modules.flatMap((m) => m.skills).filter((s) => s.attempts > 0);
  const trackBand = overallBand(practised.map(bandForSkill));
  const name = lang === 'es' ? track.name_es : track.name_en;
  const certReady = track.is_certification && track.exam_question_count && track.exam_duration_minutes;
  const retiredCert = retiredCertificationFor(track.id);

  return (
    <div className={styles.screen}>
      <button type="button" className={styles.back} onClick={onBrowse}>
        ← {t('tracks.allTracks')}
      </button>

      {retiredCert && (
        <p className={styles.certRetiredNotice} role="status" data-testid="retired-cert-notice">
          {t('tracks.certRetiredNotice', { code: retiredCert.code, replacement: retiredCert.replacement })}
        </p>
      )}

      <header className={styles.hero}>
        <span className={styles.heroIcon} aria-hidden="true"><TrackIcon trackId={track.id} fallback={track.icon || ICON_FALLBACK} size={56} /></span>
        <div className={styles.heroBody}>
          <p className={styles.eyebrow}>
            {track.is_certification
              ? `${t('tracks.kind_cert')}${track.cert_provider ? ` · ${track.cert_provider}` : ''}`
              : t('tracks.kind_learn')}
          </p>
          <h1 className={styles.heroName}>{name}</h1>
          {cur.data && (
            <p className={styles.heroMeta}>
              {completed}/{modules.length} {t('tracks.modulesDone')} · {skillCount} {t('tracks.skills')}
            </p>
          )}
        </div>
        {cur.data && (
          <p className={styles.heroPct}>
            <strong data-band={trackBand}>{t(`bands.${trackBand}`)}</strong>
            <span>{t('tracks.mastery')}</span>
          </p>
        )}
      </header>
      {cur.data && (
        <ProgressBar
          value={completed}
          max={Math.max(1, modules.length)}
          label={t('a11y.progressModules', { done: completed, total: modules.length })}
          color="var(--le-green)"
          height={4}
        />
      )}

      {/* 43.4 (D5): la ruta activa se cambia aquí. Nunca borra progreso. */}
      <div className={styles.activeRow}>
        {activeTrackId === track.id ? (
          <p className={styles.activeBadge} data-testid="track-is-active">{t('tracks.isYourTrack')}</p>
        ) : (
          <button
            type="button"
            className={styles.makeActive}
            onClick={() => {
              setActiveTrack(track.id);
              setOfferPlacement(practised.length === 0);
            }}
          >
            {t('tracks.makeActive')}
          </button>
        )}
      </div>
      {offerPlacement && activeTrackId === track.id && (
        <div className={styles.placementOffer} role="status">
          <p>{t('tracks.offerPlacement')}</p>
          <div className={styles.placementOfferActions}>
            <button type="button" className={styles.makeActive} onClick={() => startPlacement(track.id)}>
              {t('tracks.offerPlacementYes')}
            </button>
            <button type="button" className={styles.back} onClick={() => setOfferPlacement(false)}>
              {t('tracks.offerPlacementNo')}
            </button>
          </div>
        </div>
      )}

      {/* La prueba de nivel es por ruta, así que vive en su detalle. */}
      <button type="button" className={styles.placement} onClick={() => startPlacement(track.id)}>
        <span className={styles.placementText}>
          <strong>{t('tracks.placementCta')}</strong>
          <span>{t('tracks.placementSub')}</span>
        </span>
        <span className={styles.placementGo} aria-hidden="true">→</span>
      </button>

      <div className={styles.exams}>
        {certReady && (
          <>
            <button
              type="button"
              className={styles.examCard}
              onClick={() => startMockExam(track.id, track.exam_question_count ?? 65, track.exam_duration_minutes ?? 90)}
            >
              <span className={styles.examTitle}>{t('mockExam.title')}</span>
              <span className={styles.examMeta}>
                {t('mockExam.format', { count: track.exam_question_count, minutes: track.exam_duration_minutes })}
              </span>
            </button>
            <button type="button" className={styles.examCard} onClick={() => startReadiness(track.id)}>
              <span className={styles.examTitle}>{t('readiness.title')}</span>
              <span className={styles.examMeta}>{t('readiness.ctaSubtitle')}</span>
            </button>
          </>
        )}
        {/* Examen final: para las rutas que son cursos, no ensayos de la
            certificación de otro (17.2). */}
        {!track.is_certification && blueprint && (
          <button
            type="button"
            className={styles.examCard}
            onClick={() =>
              startTrackExam('track_final', track.id, {
                questions: blueprint.questions,
                durationMinutes: blueprint.duration_minutes,
                passPct: blueprint.pass_pct,
              })
            }
          >
            <span className={styles.examTitle}>{t('trackExam.title')}</span>
            <span className={styles.examMeta}>
              {t('trackExam.format', {
                count: blueprint.questions,
                minutes: blueprint.duration_minutes,
                pass: blueprint.pass_pct,
              })}
            </span>
          </button>
        )}
        {(trackProjects.data?.length ?? 0) > 0 && (
          <button
            type="button"
            className={styles.examCard}
            data-testid="track-projects"
            onClick={() => openProjects(track.id)}
          >
            <span className={styles.examTitle}>{t('project.fromTrack')}</span>
            <span className={styles.examMeta}>
              {t('project.count', { count: trackProjects.data?.length ?? 0 })}
            </span>
          </button>
        )}
        {/* 43.7 (ADR-65 D9): acceso secundario al playground libre. */}
        <button
          type="button"
          className={styles.examCard}
          data-testid="track-playground"
          onClick={() => openPlayground(null)}
        >
          <span className={styles.examTitle}>{t('playground.openPlayground')}</span>
          <span className={styles.examMeta}>Python · SQL · JS</span>
        </button>
      </div>

      <div className={styles.viewToggle} role="tablist" aria-label={name}>
        {(['curriculum', 'map', 'glossary'] as View[]).map((v) => (
          <button
            key={v}
            type="button"
            role="tab"
            aria-selected={view === v}
            className={`${styles.viewBtn} ${view === v ? styles.viewBtnActive : ''}`}
            onClick={() => setView(v)}
          >
            {t(`tracks.${v}`)}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div key={view} variants={pageVariants} initial="initial" animate="animate" exit="exit">
          {view === 'glossary' ? (
            <GlossaryView track={track.id} lang={lang} />
          ) : cur.loading ? (
            <Loading label={t('tracks.loading')} shape="line" />
          ) : cur.error || !cur.data ? (
            cur.error ? <p className={styles.muted}>{cur.error}</p> : <Loading label={t('tracks.loading')} shape="line" />
          ) : view === 'map' ? (
            <ProgressMap
              modules={modules}
              lang={lang}
              onSelect={(mod) => {
                if (mod.status === 'locked') return;
                // 32.4: sin ninguna lección vista en el módulo, el backend
                // bloquearía el quiz igual: directo a la lección.
                if (!mod.skills.some(canPractice)) startLesson(weakestSkill(mod.skills));
                else startQuiz('study', 10, { trackId: track.id });
              }}
            />
          ) : (
            <Curriculum
              track={track.id}
              modules={modules}
              threshold={cur.data.mastery_threshold}
              lang={lang}
              startQuiz={startQuiz}
              startLesson={startLesson}
            />
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

function Curriculum({
  track, modules, threshold, lang, startQuiz, startLesson,
}: {
  track: string;
  modules: CurriculumModule[];
  threshold: number;
  lang: 'es' | 'en';
  startQuiz: StartQuiz;
  startLesson: (skillId: string) => void;
}) {
  const { t } = useTranslation();
  const [openModule, setOpenModule] = useState<string | null>(null);
  const levels = [...new Set(modules.map((m) => m.level))].sort((a, b) => a - b);

  return (
    <>
      {levels.map((lvl) => {
        const lvlMods = modules.filter((m) => m.level === lvl);
        return (
          <section key={lvl} className={styles.level}>
            <h2 className={styles.levelHeader}>
              <span className={styles.levelBadge}>{lvl}</span>
              <span className={styles.levelTitle}>
                {[1, 2, 3].includes(lvl) ? t(`tracks.level_${lvl}`) : t('tracks.levelN', { n: lvl })}
              </span>
              <span className={styles.levelMeta}>
                {lvlMods.filter((m) => m.status === 'completed').length}/{lvlMods.length}
              </span>
            </h2>
            <ol className={styles.spine}>
              {lvlMods.map((m) => (
                <ModuleItem
                  key={m.id}
                  module={m}
                  prerequisite={modules.find((p) => p.id === m.prerequisite_id)}
                  open={openModule === m.id}
                  onToggle={() => setOpenModule(openModule === m.id ? null : m.id)}
                  lang={lang}
                  onLesson={startLesson}
                  onPractice={() => startQuiz('study', 10, { trackId: track })}
                />
              ))}
            </ol>
          </section>
        );
      })}
      <p className={styles.footnote}>{t('tracks.thresholdNote', { n: pct(threshold) })}</p>
    </>
  );
}

function ModuleItem({
  module: m, prerequisite, open, onToggle, lang, onLesson, onPractice,
}: {
  module: CurriculumModule;
  prerequisite: CurriculumModule | undefined;
  open: boolean;
  onToggle: () => void;
  lang: 'es' | 'en';
  onLesson: (skillId: string) => void;
  onPractice: () => void;
}) {
  const { t } = useTranslation();
  const locked = m.status === 'locked';
  const name = lang === 'es' ? m.name_es : m.name_en;
  // 32.4: el backend exige haber visto la lección de al menos una habilidad
  // del módulo antes de dejar practicar: botón desactivado con su motivo, no
  // un «Practicar» que acaba en el 200 vacío de /quiz/start.
  const needsLesson = !locked && !m.skills.some(canPractice);
  const masteredCount = m.skills.filter((s) => s.mastered).length;
  const sub = locked
    ? prerequisite
      ? t('tracks.unlockWith', {
          name: lang === 'es' ? prerequisite.name_es : prerequisite.name_en,
        })
      : t('tracks.lockNote')
    : t('tracks.moduleMastered', { mastered: masteredCount, total: m.skills.length });

  return (
    <li className={`${styles.module} ${styles[m.status]}`}>
      <button type="button" className={styles.moduleHeader} onClick={onToggle} aria-expanded={open}>
        <span className={styles.step} aria-hidden="true">
          {m.status === 'completed' ? '✓' : locked ? <LockIcon /> : m.order}
        </span>
        <span className={styles.moduleInfo}>
          <span className={styles.moduleName}>{name}</span>
          <span className={styles.moduleSub}>{sub}</span>
        </span>
        <span className={styles.chevron} aria-hidden="true">{open ? '−' : '+'}</span>
      </button>

      {!locked && (
        <div className={styles.moduleBar}>
          <ProgressBar
            value={masteredCount}
            max={Math.max(m.skills.length, 1)}
            label={t('a11y.progressMastered', { name })}
            color={m.status === 'completed' ? 'var(--le-green)' : 'var(--le-blue)'}
            height={4}
          />
        </div>
      )}

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            className={styles.moduleBody}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
          >
            {m.description_es && (
              <p className={styles.moduleDesc}>{lang === 'es' ? m.description_es : m.description_en}</p>
            )}
            <ul className={styles.skills}>
              {m.skills.map((s) => <SkillRow key={s.skill_id} skill={s} lang={lang} locked={locked} onLesson={onLesson} />)}
            </ul>
            {!locked && (
              <div className={styles.actions}>
                <button type="button" className={styles.learnBtn} onClick={() => onLesson(weakestSkill(m.skills))}>
                  {t('tracks.learn')}
                </button>
                <button
                  type="button"
                  className={styles.practiceBtn}
                  disabled={needsLesson}
                  title={needsLesson ? t('tracks.needsLessonNote') : undefined}
                  onClick={onPractice}
                >
                  {m.status === 'completed' ? t('tracks.reinforce') : t('tracks.practice')}
                </button>
              </div>
            )}
            {needsLesson && <p className={styles.note}>{t('tracks.needsLessonNote')}</p>}
            {m.status === 'available' && <TestOutOffer moduleId={m.id} />}
          </motion.div>
        )}
      </AnimatePresence>
    </li>
  );
}

// Saltar un módulo que ya sabes (17.2, O1.4). Solo en módulos disponibles sin
// completar: aprobar sube el dominio del módulo y eso desbloquea el siguiente.
// Las cifras y si se puede montar las da el backend con la misma función que
// sortea la prueba; sin preguntas suficientes no hay botón que acabe en un 400.
function TestOutOffer({ moduleId }: { moduleId: string }) {
  const { t } = useTranslation();
  const startTrackExam = useAppStore((s) => s.startTrackExam);
  const { data: bp } = useApi<TestOutBlueprint>(() => examsApi.testOutBlueprint(moduleId), [moduleId]);
  if (!bp?.available) return null;
  return (
    <button
      type="button"
      className={styles.placement}
      onClick={() =>
        startTrackExam('test_out', moduleId, {
          questions: bp.questions,
          durationMinutes: bp.duration_minutes,
          passPct: bp.pass_pct,
        })
      }
    >
      <span className={styles.placementText}>
        <strong>{t('tracks.testOutCta')}</strong>
        <span>{t('testOut.format', { count: bp.questions, minutes: bp.duration_minutes, pass: bp.pass_pct })}</span>
      </span>
      <span className={styles.placementGo} aria-hidden="true">→</span>
    </button>
  );
}

// ADR-60: la skill practicada lleva su banda; sin intentos no hay nada que decir.
function SkillRow({
  skill: s, lang, locked, onLesson,
}: {
  skill: CurriculumSkill;
  lang: 'es' | 'en';
  locked: boolean;
  onLesson: (skillId: string) => void;
}) {
  const { t } = useTranslation();
  const name = lang === 'es' ? s.name_es : s.name_en;
  const needsReview = !s.mastered && s.attempts > 0 && s.p_known < 0.3;
  const body = (
    <>
      <span className={`${styles.skillMark} ${s.mastered ? styles.skillMastered : ''}`} aria-hidden="true">
        {s.mastered ? '✓' : ''}
      </span>
      <span className={styles.skillName}>{name}</span>
      {needsReview && <span className={styles.reviewTag}>{t('tracks.needsReview')}</span>}
      {s.attempts > 0 && <BandChip band={bandForSkill(s)} />}
    </>
  );
  return (
    <li>
      {locked ? (
        <div className={styles.skill}>{body}</div>
      ) : (
        <button type="button" className={styles.skill} onClick={() => onLesson(s.skill_id)} title={t('tracks.openLesson')}>
          {body}
        </button>
      )}
    </li>
  );
}

function LockIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" />
    </svg>
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

  if (gloss.loading) return <Loading label={t('tracks.loading')} shape="line" />;
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
      <dl className={styles.terms}>
        {terms.map((term) => {
          const primary = lang === 'es' ? term.term_es : term.term_en;
          const secondary = lang === 'es' ? term.term_en : term.term_es;
          const def = lang === 'es' ? term.definition_es : term.definition_en;
          return (
            <div key={term.id} className={styles.term}>
              <dt className={styles.termHead}>
                <span className={styles.termName}>{primary}</span>
                {secondary && secondary !== primary && <span className={styles.termAlt}>{secondary}</span>}
              </dt>
              <dd className={styles.termDef}>{def}</dd>
              {term.source && <dd className={styles.termSource}>{t('tracks.source')}: {term.source}</dd>}
            </div>
          );
        })}
      </dl>
    </>
  );
}
