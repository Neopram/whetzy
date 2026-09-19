import { useTranslation } from 'react-i18next'
import InstructorPanel from '../components/instructor/InstructorPanel'

export function InstructorScreen() {
  const { t } = useTranslation()

  return (
    <div className="page-container">
      <InstructorPanel />
    </div>
  )
}
