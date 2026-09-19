import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import ProfileTab from './ProfileTab'
import CourseTab from './CourseTab'
import AnalyticsTab from './AnalyticsTab'
import PayoutsTab from './PayoutsTab'
import styles from './InstructorPanel.module.css'

type TabType = 'profile' | 'courses' | 'analytics' | 'payouts'

export default function InstructorPanel() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<TabType>('profile')

  return (
    <div className={styles.container}>
      <div className={styles.tabsNav}>
        {(['profile', 'courses', 'analytics', 'payouts'] as const).map((tab) => (
          <button
            key={tab}
            className={`${styles.tabButton} ${activeTab === tab ? styles.active : ''}`}
            onClick={() => setActiveTab(tab)}
            aria-label={t(`instructor.tabs.${tab}`)}
          >
            {t(`instructor.tabs.${tab}`)}
          </button>
        ))}
      </div>

      <div className={styles.tabContent}>
        {activeTab === 'profile' && <ProfileTab />}
        {activeTab === 'courses' && <CourseTab />}
        {activeTab === 'analytics' && <AnalyticsTab />}
        {activeTab === 'payouts' && <PayoutsTab />}
      </div>
    </div>
  )
}
