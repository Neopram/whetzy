import { useTranslation } from 'react-i18next'
import { useApi } from '../../hooks/useApi'
import { instructor } from '../../services/api'
import styles from './PayoutsTab.module.css'

export default function PayoutsTab() {
  const { t, i18n } = useTranslation()
  const { data, loading, error } = useApi(() => instructor.payouts(), [])

  const fecha = (iso: string) =>
    new Date(iso).toLocaleDateString(i18n.language === 'es' ? 'es-ES' : 'en-US', {
      month: 'short',
      year: 'numeric',
    })

  if (loading) return <div className={styles.container}>{t('instructor.common.loading')}</div>
  if (error) return <div className={styles.container}>{t('instructor.common.error')}</div>

  return (
    <div className={styles.container}>
      <h2>{t('instructor.payouts.title')}</h2>

      {/* Sin pagos todavía no se enseña una tabla vacía con ceros: se dice qué
          falta para que haya alguno. Hoy falta el alta en la pasarela. */}
      {(data?.length ?? 0) === 0 ? (
        <div className={styles.placeholderBox}>
          <div className={styles.placeholderIcon}>💸</div>
          <p>{t('instructor.payouts.comingSoon')}</p>
          <p className={styles.techNote}>{t('instructor.payouts.dependsOnPaymentRail')}</p>
        </div>
      ) : (
        <div className={styles.steps}>
          {data!.map((p) => (
            <div key={p.id} className={styles.step}>
              <div className={styles.stepNumber}>{fecha(p.period_start)}</div>
              <div className={styles.stepContent}>
                <strong>€{(p.earnings_cents / 100).toFixed(2)}</strong>
                <span> · {t(`instructor.payouts.status.${p.status}`, p.status)}</span>
                {p.payout_date && <span> · {fecha(p.payout_date)}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
