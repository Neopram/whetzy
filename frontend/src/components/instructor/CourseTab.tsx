import { useCallback, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useApi } from '../../hooks/useApi'
import { instructor, type InstructorCourse } from '../../services/api'
import styles from './CourseTab.module.css'

/**
 * Cursos del instructor autenticado.
 *
 * Antes traía un «Python Basics» con 42 alumnos y 629.930 céntimos de ingresos
 * escrito dentro del componente, y el formulario de publicar no llamaba a
 * ninguna parte. Ahora lee `GET /instructor/courses` y publica con
 * `POST /instructor/courses`.
 */
export default function CourseTab() {
  const { t } = useTranslation()
  const { data, loading, error, reload } = useApi<InstructorCourse[]>(
    () => instructor.courses(),
    []
  )

  const [showForm, setShowForm] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [fallo, setFallo] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price_eur: '',
    video_url: '',
    materials_url: '',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      if (enviando) return
      setEnviando(true)
      setFallo(null)
      try {
        // El precio se pide en euros porque es lo que el instructor tiene en la
        // cabeza; el backend trabaja en céntimos y ahí se convierte, una sola vez.
        const cents = Math.round(parseFloat(formData.price_eur || '0') * 100)
        await instructor.createCourse({
          title: formData.title.trim(),
          description: formData.description.trim() || null,
          price_cents: cents,
          video_url: formData.video_url.trim() || null,
          materials_url: formData.materials_url.trim() || null,
        })
        setFormData({ title: '', description: '', price_eur: '', video_url: '', materials_url: '' })
        setShowForm(false)
        reload()
      } catch (err) {
        setFallo(err instanceof Error ? err.message : t('instructor.common.error'))
      } finally {
        setEnviando(false)
      }
    },
    [enviando, formData, reload, t]
  )

  if (loading) return <div className={styles.container}>{t('instructor.common.loading')}</div>
  if (error) return <div className={styles.container}>{t('instructor.common.error')}</div>

  const cursos = data ?? []

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>{t('instructor.courses.title')}</h2>
        <button
          type="button"
          className={styles.addButton}
          onClick={() => setShowForm((v) => !v)}
        >
          {showForm ? t('instructor.common.cancel') : t('instructor.courses.addCourse')}
        </button>
      </div>

      {showForm && (
        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label htmlFor="ic-title">{t('instructor.courses.courseTitle')}</label>
            <input
              id="ic-title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              required
              maxLength={255}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="ic-desc">{t('instructor.courses.description')}</label>
            <textarea
              id="ic-desc"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
            />
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label htmlFor="ic-price">{t('instructor.courses.price')}</label>
              <input
                id="ic-price"
                name="price_eur"
                type="number"
                min="0.01"
                step="0.01"
                value={formData.price_eur}
                onChange={handleChange}
                required
              />
            </div>
            <div className={styles.formGroup}>
              <label htmlFor="ic-video">{t('instructor.courses.videoUrl')}</label>
              <input id="ic-video" name="video_url" type="url" value={formData.video_url} onChange={handleChange} />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="ic-mat">{t('instructor.courses.materialsUrl')}</label>
            <input id="ic-mat" name="materials_url" type="url" value={formData.materials_url} onChange={handleChange} />
          </div>

          {fallo && <p role="alert">{fallo}</p>}

          <button type="submit" className={styles.submitButton} disabled={enviando}>
            {enviando ? t('instructor.common.loading') : t('instructor.courses.publishCourse')}
          </button>
        </form>
      )}

      {cursos.length === 0 ? (
        <p>{t('instructor.courses.noCourses')}</p>
      ) : (
        <div className={styles.coursesList}>
          {cursos.map((c) => (
            <article key={c.id} className={styles.courseCard}>
              <div className={styles.courseHeader}>
                <h3>{c.title}</h3>
                <span className={styles.status}>
                  {t(`instructor.courses.status.${c.status}`, c.status)}
                </span>
              </div>
              {c.description && <p className={styles.description}>{c.description}</p>}
              <div className={styles.stats}>
                <span>€{(c.price_cents / 100).toFixed(2)}</span>
                <span>{t('instructor.courses.students', { count: c.enrolled_count })}</span>
                <span>
                  {t('instructor.courses.revenue')}: €{(c.revenue_cents / 100).toFixed(2)}
                </span>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
