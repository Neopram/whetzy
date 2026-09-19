import { useTranslation } from 'react-i18next'
import styles from './PayoutsTab.module.css'

export default function PayoutsTab() {
  const { t } = useTranslation()

  return (
    <div className={styles.container}>
      <h2>{t('instructor.payouts.title')}</h2>

      <div className={styles.placeholderBox}>
        <div className={styles.placeholderIcon}>💳</div>
        <h3>{t('instructor.payouts.comingSoon')}</h3>
        <p>{t('instructor.payouts.dependsOnPaymentRail')}</p>
        <p className={styles.techNote}>
          {t('instructor.payouts.technicalNote')}
        </p>
      </div>

      <div className={styles.section}>
        <h3>{t('instructor.payouts.setupGuide')}</h3>
        <div className={styles.steps}>
          <div className={styles.step}>
            <div className={styles.stepNumber}>1</div>
            <div className={styles.stepContent}>
              <strong>{t('instructor.payouts.step1Title')}</strong>
              <p>{t('instructor.payouts.step1Desc')}</p>
            </div>
          </div>

          <div className={styles.step}>
            <div className={styles.stepNumber}>2</div>
            <div className={styles.stepContent}>
              <strong>{t('instructor.payouts.step2Title')}</strong>
              <p>{t('instructor.payouts.step2Desc')}</p>
            </div>
          </div>

          <div className={styles.step}>
            <div className={styles.stepNumber}>3</div>
            <div className={styles.stepContent}>
              <strong>{t('instructor.payouts.step3Title')}</strong>
              <p>{t('instructor.payouts.step3Desc')}</p>
            </div>
          </div>
        </div>
      </div>

      <div className={styles.section}>
        <h3>{t('instructor.payouts.requirements')}</h3>
        <ul className={styles.requirementsList}>
          <li>{t('instructor.payouts.req1')}</li>
          <li>{t('instructor.payouts.req2')}</li>
          <li>{t('instructor.payouts.req3')}</li>
          <li>{t('instructor.payouts.req4')}</li>
        </ul>
      </div>
    </div>
  )
}
