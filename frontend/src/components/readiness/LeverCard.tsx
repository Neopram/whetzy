/**
 * «Tu mayor palanca»: el dominio del examen que más acerca al aprobado
 * (`biggestLever`). Sale en Preparación y, desde 46.3c, como primera tarjeta
 * de Hoy. Late una vez al aparecer (docs/PLAN_UI_AVANZADA.md §6.2); con
 * movimiento reducido, aparece quieta.
 */
import { motion, useReducedMotion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { bandForDomain } from '../../lib/evidenceBand';
import type { DomainReadiness } from '../../services/api';
import styles from './LeverCard.module.css';

export function LeverCard({
  lever,
  name,
  examName,
  onPractice,
}: {
  lever: DomainReadiness;
  name: string;
  /** En Hoy la certificación puede no ser la ruta activa: se nombra. En
   *  Preparación ya está en la cabecera y no hace falta. */
  examName?: string;
  onPractice: () => void;
}) {
  const { t } = useTranslation();
  const reduce = useReducedMotion();
  return (
    <motion.section
      className={styles.lever}
      aria-label={t('readiness.lever')}
      data-testid="lever-card"
      animate={reduce ? undefined : { scale: [1, 1.02, 1] }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
    >
      <p className={styles.leverLabel}>
        {t('readiness.lever')}
        {examName && <span className={styles.exam}> · {examName}</span>}
      </p>
      <p className={styles.leverBody}>
        {t('readiness.leverBody', { name, weight: lever.weight_pct, band: t(`bands.${bandForDomain(lever)}`) })}
      </p>
      <button type="button" className={styles.btnPrimary} onClick={onPractice}>
        {t('readiness.practice')}
      </button>
      <p className={styles.hint}>{t('readiness.practiceHint')}</p>
    </motion.section>
  );
}
