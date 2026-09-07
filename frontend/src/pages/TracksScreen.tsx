import { useEffect, useMemo, useState } from 'react';
import { useAppStore } from '../stores/useAppStore';
import { Card } from '../components/common/Card';
import { ProgressBar } from '../components/common/ProgressBar';
import { useApi } from '../hooks/useApi';
import {
  progress as progressApi,
  glossary as glossaryApi,
  type CurriculumModule,
} from '../services/api';
import styles from './TracksScreen.module.css';

type View = 'curriculum' | 'glossary';

const TRACKS: { id: string; icon: string; name_es: string; name_en: string }[] = [
  { id: 'track01', icon: '🐍', name_es: 'Python Básico', name_en: 'Python Basics' },
  { id: 'track02', icon: '🧩', name_es: 'Python Intermedio', name_en: 'Python Intermediate' },
  { id: 'track03', icon: '⚙️', name_es: 'Python Avanzado', name_en: 'Python Advanced' },
  { id: 'track04', icon: '🏗️', name_es: 'Ing. de Software', name_en: 'Software Engineering' },
  { id: 'track05', icon: '🌐', name_es: 'Arquitectura', name_en: 'Software Architecture' },
  { id: 'track06', icon: '🤖', name_es: 'Fundamentos de IA', name_en: 'AI Fundamentals' },
  { id: 'track07', icon: '🧠', name_es: 'Ingeniería de IA', name_en: 'AI Engineering' },
];

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
  const [track, setTrack] = useState('track01');
  const [view, setView] = useState<View>('curriculum');
  const L = TEXT[lang];

  return (
    <div className={styles.screen}>
      <h1 className={styles.title}>{L.title}</h1>
      <p className={styles.subtitle}>{L.subtitle}</p>

      {/* Track selector */}
      <div className={styles.trackRow} role="tablist" aria-label={L.title}>
        {TRACKS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={track === t.id}
            className={`${styles.trackChip} ${track === t.id ? styles.trackChipActive : ''}`}
            onClick={() => setTrack(t.id)}
          >
            <span className={styles.trackChipIcon}>{t.icon}</span>
            <span>{lang === 'es' ? t.name_es : t.name_en}</span>
          </button>
        ))}
      </div>

      {/* View toggle */}
      <div className={styles.viewToggle}>
        <button
          className={`${styles.viewBtn} ${view === 'curriculum' ? styles.viewBtnActive : ''}`}
          onClick={() => setView('curriculum')}
        >{L.curriculum}</button>
        <button
          className={`${styles.viewBtn} ${view === 'glossary' ? styles.viewBtnActive : ''}`}
          onClick={() => setView('glossary')}
        >{L.glossary}</button>
      </div>

      {view === 'curriculum'
        ? <CurriculumView track={track} lang={lang} startQuiz={startQuiz} />
        : <GlossaryView track={track} lang={lang} />}
    </div>
  );
}

function CurriculumView({
  track, lang, startQuiz,
}: {
  track: string;
  lang: 'es' | 'en';
  startQuiz: (mode: 'study', total: number, opts?: { trackId?: string; skillId?: string }) => void;
}) {
  const L = TEXT[lang];
  const cur = useApi(() => progressApi.curriculum(track), [track]);
  const [openModule, setOpenModule] = useState<string | null>(null);

  if (cur.loading) return <p className={styles.muted}>{L.loading}</p>;
  if (cur.error || !cur.data) return <p className={styles.muted}>{cur.error ?? L.loading}</p>;

  const modules = cur.data.modules;
  const threshold = cur.data.mastery_threshold;
  const completed = modules.filter((m) => m.status === 'completed').length;

  return (
    <>
      <Card className={styles.overviewCard}>
        <div className={styles.overviewText}>
          <span className={styles.overviewIcon}>{cur.data.icon}</span>
          <div>
            <p className={styles.overviewName}>{lang === 'es' ? cur.data.name_es : cur.data.name_en}</p>
            <p className={styles.overviewMeta}>{completed}/{modules.length} {L.modulesDone}</p>
          </div>
        </div>
        <ProgressBar value={completed} max={modules.length} color="var(--le-green)" height={10} />
      </Card>

      <div className={styles.spine}>
        {modules.map((m, i) => {
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
                        ? `${L.lockedUntil} ${prereq ? (lang === 'es' ? prereq.name_es : prereq.name_en) : ''} · ${Math.round(m.min_mastery_to_unlock * 100)}%`
                        : `${m.skills.length} ${L.skills} · ${Math.round(m.average_mastery * 100)}% ${L.mastery}`}
                    </span>
                  </span>
                  <span className={styles.chevron}>{isOpen ? '▾' : '▸'}</span>
                </button>

                {!locked && (
                  <div className={styles.moduleBar}>
                    <ProgressBar
                      value={m.average_mastery * 100}
                      max={100}
                      color={m.status === 'completed' ? 'var(--le-green)' : 'var(--le-brand)'}
                      height={6}
                    />
                  </div>
                )}

                {isOpen && (
                  <div className={styles.skills}>
                    {m.description_es && (
                      <p className={styles.moduleDesc}>{lang === 'es' ? m.description_es : m.description_en}</p>
                    )}
                    {m.skills.map((s) => (
                      <div key={s.skill_id} className={styles.skill}>
                        <span className={styles.skillDot} style={{
                          background: s.mastered ? 'var(--le-green)' : s.attempts > 0 ? 'var(--le-brand)' : 'var(--le-border)',
                        }} />
                        <span className={styles.skillName}>{lang === 'es' ? s.name_es : s.name_en}</span>
                        <span className={styles.skillPct}>
                          {s.mastered ? '★' : `${Math.round(s.p_known * 100)}%`}
                        </span>
                      </div>
                    ))}
                    {locked ? (
                      <p className={styles.lockNote}>🔒 {L.lockNote}</p>
                    ) : (
                      <button
                        className={styles.practiceBtn}
                        onClick={() => startQuiz('study', 10, { trackId: track })}
                      >
                        {m.status === 'completed' ? L.reinforce : L.practice}
                      </button>
                    )}
                  </div>
                )}
              </Card>
            </div>
          );
        })}
      </div>
      <p className={styles.footnote}>{L.thresholdNote.replace('{n}', String(Math.round(threshold * 100)))}</p>
    </>
  );
}

function GlossaryView({ track, lang }: { track: string; lang: 'es' | 'en' }) {
  const L = TEXT[lang];
  const gloss = useApi(() => glossaryApi.forTrack(track), [track]);
  const [q, setQ] = useState('');

  // Clear the filter when switching tracks so a stale query doesn't hide
  // the new track's terms behind an empty "no results" state.
  useEffect(() => { setQ(''); }, [track]);

  const terms = useMemo(() => {
    const data = gloss.data ?? [];
    const needle = q.trim().toLowerCase();
    if (!needle) return data;
    return data.filter((t) =>
      t.term_es.toLowerCase().includes(needle) ||
      t.term_en.toLowerCase().includes(needle) ||
      t.definition_es.toLowerCase().includes(needle) ||
      t.definition_en.toLowerCase().includes(needle)
    );
  }, [gloss.data, q]);

  if (gloss.loading) return <p className={styles.muted}>{L.loading}</p>;
  if (gloss.error) return <p className={styles.muted}>{gloss.error}</p>;

  return (
    <>
      <input
        className={styles.search}
        type="search"
        placeholder={L.searchTerms}
        value={q}
        onChange={(e) => setQ(e.target.value)}
        aria-label={L.searchTerms}
      />
      {terms.length === 0 && <p className={styles.muted}>{L.noTerms}</p>}
      <div className={styles.terms}>
        {terms.map((t) => {
          const primary = lang === 'es' ? t.term_es : t.term_en;
          const secondary = lang === 'es' ? t.term_en : t.term_es;
          const def = lang === 'es' ? t.definition_es : t.definition_en;
          return (
            <Card key={t.id} className={styles.term}>
              <div className={styles.termHead}>
                <span className={styles.termName}>{primary}</span>
                {secondary && secondary !== primary && (
                  <span className={styles.termAlt}>{secondary}</span>
                )}
              </div>
              <p className={styles.termDef}>{def}</p>
              {t.source && <span className={styles.termSource}>📖 {t.source}</span>}
            </Card>
          );
        })}
      </div>
    </>
  );
}

const TEXT = {
  es: {
    title: 'Rutas de aprendizaje',
    subtitle: 'Currículo desbloqueable por dominio y glosario por track.',
    curriculum: 'Currículo',
    glossary: 'Glosario',
    loading: 'Cargando…',
    modulesDone: 'módulos completados',
    skills: 'habilidades',
    mastery: 'dominio',
    lockedUntil: 'Se desbloquea al dominar',
    lockNote: 'Domina el módulo anterior para desbloquear este.',
    practice: 'Practicar',
    reinforce: 'Reforzar',
    thresholdNote: 'Una habilidad se marca dominada al {n}% de probabilidad de conocimiento (BKT). Un módulo desbloquea el siguiente al superar su umbral de dominio.',
    searchTerms: 'Buscar término…',
    noTerms: 'Sin resultados.',
  },
  en: {
    title: 'Learning paths',
    subtitle: 'Mastery-gated curriculum and a per-track glossary.',
    curriculum: 'Curriculum',
    glossary: 'Glossary',
    loading: 'Loading…',
    modulesDone: 'modules completed',
    skills: 'skills',
    mastery: 'mastery',
    lockedUntil: 'Unlocks once you master',
    lockNote: 'Master the previous module to unlock this one.',
    practice: 'Practice',
    reinforce: 'Reinforce',
    thresholdNote: 'A skill is marked mastered at {n}% known-probability (BKT). A module unlocks the next once it clears its mastery threshold.',
    searchTerms: 'Search term…',
    noTerms: 'No results.',
  },
} as const;
