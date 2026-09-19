import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import { useApi } from '../hooks/useApi';
import { content as contentApi, progress as progressApi, type TrackRead } from '../services/api';
import '../styles/marketplace.css';

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
    return <p className="mkt-state">{t('marketplace.loading')}</p>;
  }
  if (tracks.error) {
    return <p className="mkt-state mkt-state--error">{t('marketplace.error')}</p>;
  }

  const totalPreguntas = (tracks.data ?? []).reduce((s, tr) => s + tr.total_questions, 0);

  return (
    <div className="mkt">
      <header className="mkt-head">
        <h1 className="mkt-title">{t('marketplace.title')}</h1>
        <p className="mkt-sub">
          {t('marketplace.summary', {
            tracks: tracks.data?.length ?? 0,
            questions: totalPreguntas.toLocaleString(lang === 'es' ? 'es-ES' : 'en-US'),
          })}
        </p>
      </header>

      <div className="mkt-filters">
        <input
          className="mkt-search"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('marketplace.search_placeholder')}
          aria-label={t('marketplace.search_placeholder')}
        />
        <div className="mkt-tabs" role="tablist" aria-label={t('marketplace.category')}>
          {(['all', 'learning', 'certification'] as const).map((k) => (
            <button
              key={k}
              type="button"
              role="tab"
              aria-selected={tipo === k}
              className={`mkt-tab ${tipo === k ? 'is-active' : ''}`}
              onClick={() => setTipo(k)}
            >
              {t(`marketplace.filter_${k}`)}
            </button>
          ))}
        </div>
      </div>

      {visibles.length === 0 ? (
        <p className="mkt-state">{t('marketplace.no_courses')}</p>
      ) : (
        <ul className="mkt-grid">
          {visibles.map((tr) => {
            const m = masteryPorTrack.get(tr.id);
            const pct = m ? Math.round(m.mastery * 100) : 0;
            const empezado = (m?.total ?? 0) > 0 && pct > 0;
            return (
              <li key={tr.id} className="mkt-card" style={{ ['--mkt-accent' as string]: tr.color }}>
                <div className="mkt-card-top">
                  <span className="mkt-icon" aria-hidden="true">{tr.icon}</span>
                  {tr.is_certification && (
                    <span className="mkt-badge">{tr.cert_provider ?? t('marketplace.certification')}</span>
                  )}
                </div>

                <h2 className="mkt-card-title">{lang === 'es' ? tr.name_es : tr.name_en}</h2>

                <p className="mkt-card-meta">
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
                  <div className="mkt-progress">
                    <div className="mkt-progress-track">
                      <div className="mkt-progress-fill" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="mkt-progress-label">
                      {t('marketplace.mastery_meta', {
                        pct,
                        mastered: m!.mastered,
                        total: m!.total,
                      })}
                    </span>
                  </div>
                )}

                <div className="mkt-card-actions">
                  <button
                    type="button"
                    className="mkt-btn mkt-btn--primary"
                    onClick={() => startQuiz('study', 10, { trackId: tr.id })}
                  >
                    {empezado ? t('marketplace.continue') : t('marketplace.start')}
                  </button>
                  <button
                    type="button"
                    className="mkt-btn"
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
