import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useApi } from '../../hooks/useApi'
import { instructor, type InstructorProfile } from '../../services/api'
import styles from './ProfileTab.module.css'
import { Loading } from '../common/Loading'

const EMPTY: InstructorProfile = { display_name: '', bio: null, avatar_url: null, website: null }

export default function ProfileTab() {
  const { t } = useTranslation()
  const { data, loading: fetching, error: loadError } = useApi(() => instructor.profile(), [])
  const [formData, setFormData] = useState<InstructorProfile>(EMPTY)

  // 28.8: antes el formulario arrancaba siempre vacío y el envío era un
  // `console.log` — ni leía ni guardaba nada. `data` llega una vez, al cargar.
  useEffect(() => {
    if (data) setFormData(data)
  }, [data])

  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState('')

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setMessage('')

    try {
      const updated = await instructor.updateProfile(formData)
      setFormData(updated)
      setMessage(t('instructor.messages.profileUpdated'))
    } catch {
      setMessage(t('instructor.messages.error'))
    } finally {
      setIsLoading(false)
    }
  }

  if (fetching) return <Loading label={t('instructor.common.loading')} shape="line" />
  if (loadError) return <div className={styles.container}>{t('instructor.common.error')}</div>

  return (
    <div className={styles.container}>
      <h2>{t('instructor.profile.title')}</h2>

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.formGroup}>
          <label htmlFor="display_name">{t('instructor.profile.displayName')}</label>
          <input
            id="display_name"
            name="display_name"
            type="text"
            value={formData.display_name}
            onChange={handleChange}
            required
            maxLength={100}
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="bio">{t('instructor.profile.bio')}</label>
          <textarea
            id="bio"
            name="bio"
            value={formData.bio ?? ''}
            onChange={handleChange}
            rows={4}
            placeholder={t('instructor.profile.bioPlaceholder')}
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="avatar_url">{t('instructor.profile.avatarUrl')}</label>
          <input
            id="avatar_url"
            name="avatar_url"
            type="url"
            value={formData.avatar_url ?? ''}
            onChange={handleChange}
            placeholder="https://..."
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="website">{t('instructor.profile.website')}</label>
          <input
            id="website"
            name="website"
            type="url"
            value={formData.website ?? ''}
            onChange={handleChange}
            placeholder="https://..."
          />
        </div>

        <button type="submit" disabled={isLoading} className={styles.submitButton}>
          {isLoading ? t('instructor.common.saving') : t('instructor.common.save')}
        </button>

        {message && <div className={styles.message}>{message}</div>}
      </form>
    </div>
  )
}
