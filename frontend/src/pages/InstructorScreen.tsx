import { useTranslation } from 'react-i18next'
import InstructorPanel from '../components/instructor/InstructorPanel'
import { useAppStore } from '../stores/useAppStore'

export default function InstructorScreen() {
  const { t } = useTranslation()
  const canCreateCourses = useAppStore((s) => s.user.canCreateCourses)
  const setScreen = useAppStore((s) => s.setScreen)

  // 28.3: ProfileScreen ya oculta el enlace, pero la pantalla se monta también
  // por `screen === 'instructor'` (estado persistido, deep link): la guarda va aquí.
  if (!canCreateCourses) {
    return (
      <div className="page-container instructor-page">
        <h1>{t('instructor.title')}</h1>
        <p role="alert">{t('instructor.noAccess')}</p>
        <button type="button" onClick={() => setScreen('profile')}>
          {t('instructor.backToProfile')}
        </button>
      </div>
    )
  }

  return (
    <div className="page-container instructor-page">
      <h1>{t('instructor.title')}</h1>
      <InstructorPanel />
    </div>
  )
}
