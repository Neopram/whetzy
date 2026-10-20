import { useTranslation } from 'react-i18next'
import { useApi } from '../../hooks/useApi'
import { instructor } from '../../services/api'
import styles from './AnalyticsTab.module.css'
import { Loading } from '../common/Loading'

export default function AnalyticsTab() {
  const { t } = useTranslation()
  const { data, loading, error } = useApi(() => instructor.analytics(), [])

  const formatPrice = (cents: number) => `€${(cents / 100).toFixed(2)}`

  if (loading) return <Loading label={t('instructor.common.loading')} shape="line" />
  if (error || !data) return <div className={styles.loading}>{t('instructor.common.error')}</div>

  const metricas = [
    {
      label: t('instructor.analytics.totalEarnings'),
      value: formatPrice(data.total_earnings_cents),
      desc: t('instructor.analytics.afterPlatformSplit'),
    },
    {
      label: t('instructor.analytics.pendingPayout'),
      value: formatPrice(data.pending_payout_cents),
      desc: t('instructor.analytics.readyForWithdrawal'),
    },
    {
      label: t('instructor.analytics.publishedCourses'),
      value: String(data.active_courses),
      desc: t('instructor.analytics.activeCourses'),
    },
    {
      label: t('instructor.analytics.totalStudents'),
      value: String(data.total_students),
      desc: t('instructor.analytics.enrolledStudents'),
    },
    {
      label: t('instructor.analytics.completionRate'),
      value: `${data.avg_completion_percent.toFixed(1)}%`,
      desc: t('instructor.analytics.avgCompletion'),
    },
  ]

  return (
    <div className={styles.container}>
      <h2>{t('instructor.analytics.title')}</h2>

      <div className={styles.metricsGrid}>
        {metricas.map((m) => (
          <div key={m.label} className={styles.metricCard}>
            <div className={styles.metricLabel}>{m.label}</div>
            <div className={styles.metricValue}>{m.value}</div>
            <div className={styles.metricDescription}>{m.desc}</div>
          </div>
        ))}
      </div>

      <section className={styles.section}>
        <h3>{t('instructor.analytics.platformSplit')}</h3>
        <div className={styles.splitInfo}>
          <div className={styles.splitRow}>
            <span>{t('instructor.analytics.yourShare')}</span>
            <span className={styles.highlight}>80%</span>
          </div>
          <div className={styles.splitRow}>
            <span>{t('instructor.analytics.platformShare')}</span>
            <span>20%</span>
          </div>
        </div>
      </section>
    </div>
  )
}
