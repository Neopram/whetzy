import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { Card } from '../components/common/Card';
import { ProgressBar } from '../components/common/ProgressBar';
import { useApi } from '../hooks/useApi';
import {
  content as contentApi,
  progress as progressApi,
  glossary as glossaryApi,
  type CurriculumModule,
  type TrackRead,
} from '../services/api';
import styles from './TracksScreen.module.css';

type View = 'curriculum' | 'glossary';

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
  const startMockExam = useAppStore((s) => s.startMockExam);
  const [track, setTrack] = useState('track01');
  const [view, setView] = useState<View>('curriculum');
  const { t } = useTranslation();
  const { data: tracks, loading: tracksLoading, error: tracksError } =
    useApi<TrackRead[]>(() => contentApi.tracks(), []);
  const trackList = tracks ?? [];
  const selected = trackList.find((tr) => tr.id === track);

  return (
    <div className={styles.screen}>
      <h1 className={styles.title}>{t('tracks.title')}</h1>
      <p className={styles.subtitle}>{t('tracks.subtitle')}</p>

      {/* Track selector */}
      <div className={styles.trackRow} role="tablist" aria-label={t('tracks.title')}>
        {trackList.map((tr) => (
          <button
            key={tr.id}
            role="tab"
            aria-selected={track === tr.id}
            className={`${styles.trackChip} ${track === tr.id ? styles.trackChipActive : ''}`}
            onClick={() => setTrack(tr.id)}
          >
            <span className={styles.trackChipIcon}>{tr.icon || ICON_FALLBACK}</span>
            <span>{lang === 'es' ? tr.name_es : tr.name_en}</span>
          </button>
        ))}
        {tracksLoading && trackList.length === 0 && (
          <span className={styles.trackChip}>{t('loading')}</span>
        )}
      </div>

      {/* Without this the screen just renders an empty selector and says
          nothing, which is what it did when the endpoint 404'd during
          development - silence looks identical to "no tracks exist". */}
      {!tracksLoading && trackList.length === 0 && (
        <p className={styles.tracksError} role="alert">
          {tracksError ?? t('tracks.empty')}
        </p>
      )}
      {/* View toggle */}
      <div className={styles.viewToggle}>
        <button
          className={`${styles.viewBtn} ${view === 'curriculum' ? styles.viewBtnActive : ''}`}
          onClick={() => setView('curriculum')}
        >{t('tracks.curriculum')}</button>
        <button
          className={`${styles.viewBtn} ${view === 'glossary' ? styles.viewBtnActive : ''}`}
          onClick={() => setView('glossary')}
        >{t('tracks.glossary')}</button>
      </div>

      {/* Only a certification track offers a mock exam, and it says what it
          costs in time before the clock starts. */}
      {selected?.is_certification && selected.exam_question_count && selected.exam_duration_minutes && (
        <button className={styles.mockExamCta} onClick={() => selected && startMockExam(selected.id, selected.exam_question_count ?? 65, selected.exam_duration_minutes ?? 90)}>
          <span className={styles.mockExamTitle}>{t('mockExam.title')}</span>
          <span className={styles.mockExamMeta}>
            {t('mockExam.format', {
              count: selected.exam_question_count,
              minutes: selected.exam_duration_minutes,
            })}
          </span>
        </button>
      )}

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
  const { t } = useTranslation();
  const cur = useApi(() => progressApi.curriculum(track), [track]);
  const [openModule, setOpenModule] = useState<string | null>(null);

  if (cur.loading) return <p className={styles.muted}>{t('tracks.loading')}</p>;
  if (cur.error || !cur.data) return <p className={styles.muted}>{cur.error ?? t('tracks.loading')}</p>;

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
            <p className={styles.overviewMeta}>{completed}/{modules.length} {t('tracks.modulesDone')}</p>
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
                      <p className={styles.lockNote}>🔒 {t('tracks.lockNote')}</p>
                    ) : (
                      <button
                        className={styles.practiceBtn}
                        onClick={() => startQuiz('study', 10, { trackId: track })}
                      >
                        {m.status === 'completed' ? t('tracks.reinforce') : t('tracks.practice')}
                      </button>
                    )}
                  </div>
                )}
              </Card>
            </div>
          );
        })}
      </div>
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
