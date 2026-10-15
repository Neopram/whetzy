import { useTranslation } from 'react-i18next';
import type { EvidenceBand } from '../../lib/evidenceBand';
import styles from './BandChip.module.css';

const BAND_CLASS: Record<EvidenceBand, string> = {
  strong: styles.strong,
  developing: styles.developing,
  insufficient: styles.insufficient,
};

/** ADR-60: el estado de una skill en palabras, nunca como %. `data-band` deja
 *  que los tests lean la banda sin depender del idioma. */
export function BandChip({ band }: { band: EvidenceBand }) {
  const { t } = useTranslation();
  return (
    <span className={`${styles.chip} ${BAND_CLASS[band]}`} data-band={band}>
      {t(`bands.${band}`)}
    </span>
  );
}
