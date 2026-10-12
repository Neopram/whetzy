import { useTranslation } from 'react-i18next';
import { retiredCertificationFor } from '../../lib/retiredCertifications';
import styles from './RetiredCertNotice.module.css';

/** D-19 (dueño, 2026-10-12): el aviso de examen sustituido sale en cada pantalla
 *  donde la certificación se elige, se practica o se compra, no solo en Rutas. */
export function RetiredCertNotice({ trackId }: { trackId: string | null | undefined }) {
  const { t } = useTranslation();
  const retired = trackId ? retiredCertificationFor(trackId) : undefined;
  if (!retired) return null;
  return (
    <p className={styles.notice} role="status" data-testid="retired-cert-notice">
      {t('tracks.certRetiredNotice', { code: retired.code, replacement: retired.replacement })}
    </p>
  );
}
