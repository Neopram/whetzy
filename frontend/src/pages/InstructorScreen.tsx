import { useTranslation } from 'react-i18next'
import InstructorPanel from '../components/instructor/InstructorPanel'

export default function InstructorScreen() {
  const { t } = useTranslation()

  return (
    <div className="page-container instructor-page">
      <h1>{t('instructor.title')}</h1>
      <InstructorPanel />
    </div>
  )
}
