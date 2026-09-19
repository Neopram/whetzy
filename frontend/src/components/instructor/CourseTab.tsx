import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import styles from './CourseTab.module.css'

interface Course {
  id: string
  title: string
  description?: string
  price_cents: number
  enrolled_count: number
  revenue_cents: number
  status: 'draft' | 'published' | 'archived'
}

export default function CourseTab() {
  const { t } = useTranslation()
  const [courses, setCourses] = useState<Course[]>([
    {
      id: 'course-1',
      title: 'Python Basics',
      description: 'Learn Python fundamentals',
      price_cents: 9999,
      enrolled_count: 42,
      revenue_cents: 629930,
      status: 'published',
    },
  ])

  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price_cents: 0,
    video_url: '',
    materials_url: '',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'price_cents' ? parseInt(value, 10) : value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Implement API call POST /instructor/courses
    console.log('Course upload:', formData)
    setFormData({
      title: '',
      description: '',
      price_cents: 0,
      video_url: '',
      materials_url: '',
    })
    setShowForm(false)
  }

  const formatPrice = (cents: number) => `$${(cents / 100).toFixed(2)}`

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>{t('instructor.courses.title')}</h2>
        <button onClick={() => setShowForm(!showForm)} className={styles.addButton}>
          {showForm ? t('instructor.common.cancel') : t('instructor.courses.addCourse')}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="title">{t('instructor.courses.title')}</label>
            <input
              id="title"
              name="title"
              type="text"
              value={formData.title}
              onChange={handleChange}
              required
              maxLength={255}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="description">{t('instructor.courses.description')}</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
            />
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label htmlFor="price_cents">{t('instructor.courses.price')} (USD)</label>
              <input
                id="price_cents"
                name="price_cents"
                type="number"
                value={formData.price_cents / 100}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    price_cents: Math.round(parseFloat(e.target.value) * 100),
                  }))
                }
                step="0.01"
                min="0"
                required
              />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="video_url">{t('instructor.courses.videoUrl')}</label>
            <input
              id="video_url"
              name="video_url"
              type="url"
              value={formData.video_url}
              onChange={handleChange}
              placeholder="https://..."
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="materials_url">{t('instructor.courses.materialsUrl')}</label>
            <input
              id="materials_url"
              name="materials_url"
              type="url"
              value={formData.materials_url}
              onChange={handleChange}
              placeholder="https://..."
            />
          </div>

          <button type="submit" className={styles.submitButton}>
            {t('instructor.courses.publishCourse')}
          </button>
        </form>
      )}

      <div className={styles.coursesList}>
        {courses.length === 0 ? (
          <p>{t('instructor.courses.noCourses')}</p>
        ) : (
          courses.map((course) => (
            <div key={course.id} className={styles.courseCard}>
              <div className={styles.courseHeader}>
                <h3>{course.title}</h3>
                <span className={`${styles.status} ${styles[course.status]}`}>
                  {t(`instructor.courses.status.${course.status}`)}
                </span>
              </div>
              {course.description && <p className={styles.description}>{course.description}</p>}
              <div className={styles.stats}>
                <div>
                  <strong>{t('instructor.courses.price')}</strong>
                  <span>{formatPrice(course.price_cents)}</span>
                </div>
                <div>
                  <strong>{t('instructor.courses.students')}</strong>
                  <span>{course.enrolled_count}</span>
                </div>
                <div>
                  <strong>{t('instructor.courses.revenue')}</strong>
                  <span>{formatPrice(course.revenue_cents)}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
