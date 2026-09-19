import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import styles from './AnalyticsTab.module.css'

interface AnalyticsData {
  total_earnings_cents: number
  total_revenue_cents: number
  active_courses: number
  total_students: number
  avg_completion_percent: number
  pending_payout_cents: number
}

export default function AnalyticsTab() {
  const { t } = useTranslation()
  const [analytics] = useState<AnalyticsData>({
    total_earnings_cents: 629930,
    total_revenue_cents: 899900,
    active_courses: 1,
    total_students: 42,
    avg_completion_percent: 65.5,
    pending_payout_cents: 629930,
  })

  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // TODO: Implement API call GET /instructor/analytics
    setIsLoading(false)
  }, [])

  const formatPrice = (cents: number) => `$${(cents / 100).toFixed(2)}`

  if (isLoading) {
    return <div className={styles.loading}>{t('instructor.common.loading')}</div>
  }

  return (
    <div className={styles.container}>
      <h2>{t('instructor.analytics.title')}</h2>

      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>{t('instructor.analytics.totalEarnings')}</div>
          <div className={styles.metricValue}>{formatPrice(analytics.total_earnings_cents)}</div>
          <div className={styles.metricDescription}>
            {t('instructor.analytics.afterPlatformSplit')}
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>{t('instructor.analytics.totalRevenue')}</div>
          <div className={styles.metricValue}>{formatPrice(analytics.total_revenue_cents)}</div>
          <div className={styles.metricDescription}>
            {t('instructor.analytics.beforePlatformSplit')}
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>{t('instructor.analytics.activeCourses')}</div>
          <div className={styles.metricValue}>{analytics.active_courses}</div>
          <div className={styles.metricDescription}>
            {t('instructor.analytics.publishedCourses')}
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>{t('instructor.analytics.totalStudents')}</div>
          <div className={styles.metricValue}>{analytics.total_students}</div>
          <div className={styles.metricDescription}>
            {t('instructor.analytics.enrolledStudents')}
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>{t('instructor.analytics.avgCompletion')}</div>
          <div className={styles.metricValue}>{analytics.avg_completion_percent.toFixed(1)}%</div>
          <div className={styles.metricDescription}>
            {t('instructor.analytics.completionRate')}
          </div>
        </div>

        <div className={`${styles.metricCard} ${styles.highlight}`}>
          <div className={styles.metricLabel}>{t('instructor.analytics.pendingPayout')}</div>
          <div className={styles.metricValue}>{formatPrice(analytics.pending_payout_cents)}</div>
          <div className={styles.metricDescription}>
            {t('instructor.analytics.readyForWithdrawal')}
          </div>
        </div>
      </div>

      <div className={styles.section}>
        <h3>{t('instructor.analytics.platformSplit')}</h3>
        <div className={styles.splitInfo}>
          <div className={styles.splitRow}>
            <span>{t('instructor.analytics.yourShare')}</span>
            <strong>70%</strong>
          </div>
          <div className={styles.splitRow}>
            <span>{t('instructor.analytics.platformShare')}</span>
            <strong>30%</strong>
          </div>
          <div className={styles.splitRow}>
            <span>{t('instructor.analytics.example')}</span>
            <span className={styles.example}>
              ${(100).toFixed(2)} → ${(70).toFixed(2)} {t('instructor.analytics.youGet')} / ${(30).toFixed(2)} {t('instructor.analytics.platform')}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
