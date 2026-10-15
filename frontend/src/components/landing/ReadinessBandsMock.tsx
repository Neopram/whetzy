import { useTranslation } from 'react-i18next';
import type { EvidenceBand } from '../../lib/evidenceBand';
import styles from './LandingMocks.module.css';

/** Preparación por dominio en la landing, con las bandas de ADR-60 (#189) y
 *  sin porcentaje global. Los pesos son los de `content/curriculum/tracks.json`
 *  (track08, `exam_weight_pct`); las bandas, un ejemplo rotulado como tal. */
export const MOCK_DOMAINS: { key: 'd1' | 'd2' | 'd3' | 'd4'; weight: number; band: EvidenceBand }[] = [
  { key: 'd1', weight: 24, band: 'strong' },
  { key: 'd2', weight: 30, band: 'developing' },
  { key: 'd3', weight: 34, band: 'developing' },
  { key: 'd4', weight: 12, band: 'insufficient' },
];

const BAND_CLASS: Record<EvidenceBand, string> = {
  strong: styles.bandStrong,
  developing: styles.bandDeveloping,
  insufficient: styles.bandInsufficient,
};

export function ReadinessBandsMock() {
  const { t } = useTranslation();
  return (
    <figure className={styles.window} aria-label={t('landing.bandsMock.label')}>
      <div className={styles.windowHeader}>
        <span className={styles.windowBrand}>{t('landing.bandsMock.title')}</span>
      </div>
      <ul className={styles.domainList}>
        {MOCK_DOMAINS.map((d) => (
          <li key={d.key} className={styles.domainRow}>
            <span className={styles.domainName}>
              {t(`landing.bandsMock.${d.key}`)}
              <span className={styles.domainWeight}>{t('landing.bandsMock.weight', { w: d.weight })}</span>
            </span>
            <span className={`${styles.bandChip} ${BAND_CLASS[d.band]}`}>{t(`bands.${d.band}`)}</span>
          </li>
        ))}
      </ul>
      <figcaption className={styles.mockCaption}>{t('landing.bandsMock.note')}</figcaption>
    </figure>
  );
}
