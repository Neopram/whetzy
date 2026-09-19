import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import styles from './ProfileTab.module.css'

interface ProfileFormData {
  display_name: string
  bio: string
  avatar_url: string
  website: string
}

export default function ProfileTab() {
  const { t } = useTranslation()
  const [formData, setFormData] = useState<ProfileFormData>({
    display_name: 'Your Name',
    bio: 'Tell students about yourself',
    avatar_url: '',
    website: '',
  })

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
      // TODO: Implement API call POST /instructor/profile
      console.log('Profile update:', formData)
      setMessage(t('instructor.messages.profileUpdated'))
    } catch (error) {
      setMessage(t('instructor.messages.error'))
      console.error('Profile update error:', error)
    } finally {
      setIsLoading(false)
    }
  }

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
            value={formData.bio}
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
            value={formData.avatar_url}
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
            value={formData.website}
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
