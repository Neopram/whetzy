import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { useApi } from '../hooks/useApi';
import { content as contentApi, progress as progressApi, type TrackRead } from '../services/api';
import { nextLessonSkillId } from '../lib/nextStep';
import styles from './MarketplaceScreen.module.css';
import { TrackIcon } from '../components/common/AppIcon';
import { Loading } from '../components/common/Loading';

/**
 * Catálogo de lo que se puede estudiar.
 *
 * La versión anterior traía ocho cursos escritos dentro del fichero, con
 * `rating`, `reviews_count`, `students_count` y `price_usd`. Ninguno de esos
 * campos existe en el backend, y con cero usuarios reales una valoración de
 * 4,8 sobre 312 reseñas no es un dato incompleto: es inventado. Aquí solo sale
 * lo que se puede leer del catálogo y del progreso del propio usuario.
 */
export function MarketplaceScreen() {
  const { t } = useTranslation();
  const lang = useAppStore((s) => s.user.language);
  const setScreen = useAppStore((s) => s.setScreen);
  const startQuiz = useAppStore((s) => s.startQuiz);
  const startLesson = useAppStore((s) => s.startLesson);
  // 43.5 (ADR-65 D7): estudiar una ruta empieza por su siguiente lección
  // pendiente; sin ninguna, practica. Sin red, practica (el backend decide).
  const study = async (trackId: string) => {
    try {
      const next = nextLessonSkillId(await progressApi.curriculum(trackId));
      if (next) return startLesson(next);
    } catch { /* sin red */ }
    startQuiz('study', 10, { trackId });
  };

  const tracks = useApi<TrackRead[]>(() => contentApi.tracks(), []);
  const dash = useApi(() => progressApi.dashboard(), []);

  const [query, setQuery] = useState('');
  const [tipo, setTipo] = useState<'all' | 'learning' | 'certification'>('all');

  // El dominio por track lo da el dashboard; se indexa una vez para no
  // recorrerlo dentro del map de abajo.
  const masteryPorTrack = useMemo(() => {
    const m = new Map<string, { mastery: number; mastered: number; total: number }>();
    for (const tr of dash.data?.tracks ?? []) {
      m.set(tr.track_id, {
        mastery: tr.average_mastery,
        mastered: tr.skills_mastered,
        total: tr.total_skills,
      });
    }
    return m;
  }, [dash.data]);

  const visibles = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (tracks.data ?? [])
      .filter((tr) => {
        if (tipo === 'certification' && !tr.is_certification) return false;
        if (tipo === 'learning' && tr.is_certification) return false;
        if (!q) return true;
        return `${tr.name_es} ${tr.name_en} ${tr.cert_provider ?? ''}`.toLowerCase().includes(q);
      })
      .sort((a, b) => a.order - b.order);
  }, [tracks.data, tipo, query]);

  if (tracks.loading) {
    return <Loading label={t('marketplace.loading')} shape="list" />;
  }
  if (tracks.error) {
    return <p className={`${styles.mktState} ${styles.mktStateError}`}>{t('marketplace.error')}</p>;
  }

  const totalPreguntas = (tracks.data ?? []).reduce((s, tr) => s + tr.total_questions, 0);

  return (
    <div className={styles.mkt}>
      <header className={styles.mktHead}>
        <h1 className={styles.mktTitle}>{t('marketplace.title')}</h1>
        <p className={styles.mktSub}>
          {t('marketplace.summary', {
            tracks: tracks.data?.length ?? 0,
            questions: totalPreguntas.toLocaleString(lang === 'es' ? 'es-ES' : 'en-US'),
          })}
        </p>
      </header>

      <div className={styles.mktFilters}>
        <input
          className={styles.mktSearch}
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('marketplace.search_placeholder')}
          aria-label={t('marketplace.search_placeholder')}
        />
        <div className={styles.mktTabs} role="tablist" aria-label={t('marketplace.category')}>
          {(['all', 'learning', 'certification'] as const).map((k) => (
            <button
              key={k}
              type="button"
              role="tab"
              aria-selected={tipo === k}
              className={`${styles.mktTab} ${tipo === k ? styles.isActive : ''}`}
              onClick={() => setTipo(k)}
            >
              {t(`marketplace.filter_${k}`)}
            </button>
          ))}
        </div>
      </div>

      {visibles.length === 0 ? (
        <p className={styles.mktState}>{t('marketplace.no_courses')}</p>
      ) : (
        <ul className={styles.mktGrid}>
          {visibles.map((tr) => {
            const m = masteryPorTrack.get(tr.id);
            // ADR-60: progreso por skills dominadas, no por un % del modelo.
            const empezado = (m?.total ?? 0) > 0 && (m?.mastered ?? 0) > 0;
            const pct = m && m.total > 0 ? Math.round((m.mastered / m.total) * 100) : 0;
            return (
              <li key={tr.id} className={styles.mktCard} style={{ ['--mkt-accent' as string]: tr.color }}>
                <div className={styles.mktCardTop}>
                  <span className={styles.mktIcon} aria-hidden="true"><TrackIcon trackId={tr.id} fallback={tr.icon} size={32} /></span>
                  {tr.is_certification && (
                    <span className={styles.mktBadge}>{tr.cert_provider ?? t('marketplace.certification')}</span>
                  )}
                </div>

                <h2 className={styles.mktCardTitle}>{lang === 'es' ? tr.name_es : tr.name_en}</h2>

                <p className={styles.mktCardMeta}>
                  {t('marketplace.questions_count', {
                    count: tr.total_questions,
                  })}
                  {tr.is_certification && tr.exam_question_count
                    ? ` · ${t('marketplace.exam_meta', {
                        count: tr.exam_question_count,
                        minutes: tr.exam_duration_minutes ?? 0,
                      })}`
                    : ''}
                </p>

                {/* El progreso solo aparece si de verdad hay progreso. Una barra
                    al 0 % en todo el catálogo es ruido, no información. */}
                {empezado && (
                  <div className={styles.mktProgress}>
                    <div className={styles.mktProgressTrack}>
                      <div className={styles.mktProgressFill} style={{ width: `${pct}%` }} />
                    </div>
                    <span className={styles.mktProgressLabel}>
                      {t('marketplace.mastery_meta', {
                        mastered: m!.mastered,
                        total: m!.total,
                      })}
                    </span>
                  </div>
                )}

                <div className={styles.mktCardActions}>
                  <button
                    type="button"
                    className={`${styles.mktBtn} ${styles.mktBtnPrimary}`}
                    onClick={() => void study(tr.id)}
                  >
                    {empezado ? t('marketplace.continue') : t('marketplace.start')}
                  </button>
                  <button
                    type="button"
                    className={styles.mktBtn}
                    onClick={() => setScreen('tracks')}
                  >
                    {t('marketplace.see_syllabus')}
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export default MarketplaceScreen;
