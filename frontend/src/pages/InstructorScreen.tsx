import { useTranslation } from 'react-i18next'
import InstructorPanel from '../components/instructor/InstructorPanel'
import { Button } from '../components/common/Button'
import { useAppStore } from '../stores/useAppStore'
import styles from './InstructorScreen.module.css'

export default function InstructorScreen() {
  const { t } = useTranslation()
  const canCreateCourses = useAppStore((s) => s.user.canCreateCourses)
  const setScreen = useAppStore((s) => s.setScreen)

  // 28.3: ProfileScreen ya oculta el enlace, pero la pantalla se monta también
  // por `screen === 'instructor'` (estado persistido, deep link): la guarda va aquí.
  if (!canCreateCourses) {
    return (
      <div className={styles.screen}>
        <h1 className={styles.title}>{t('instructor.title')}</h1>
        <p className={styles.notice} role="alert">{t('instructor.noAccess')}</p>
        <Button type="button" variant="secondary" onClick={() => setScreen('profile')}>
          {t('instructor.backToProfile')}
        </Button>
      </div>
    )
  }

  return (
    <div className={styles.screen}>
      <h1 className={styles.title}>{t('instructor.title')}</h1>
      <InstructorPanel />
    </div>
  )
}
