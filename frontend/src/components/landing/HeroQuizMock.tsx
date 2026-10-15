import { useTranslation } from 'react-i18next';
import { BrandMark } from '../common/BrandMark';
import styles from './LandingMocks.module.css';

/** Hero de la landing (2026-10-15): una pregunta de ejemplo dibujada en HTML,
 *  no una captura. Una sola opción correcta, y está en el `CORRECT` de abajo:
 *  la maqueta que trajo el dueño marcaba dos «6» y un test lo vigila. */
export const MOCK_OPTIONS = ['5', '6', '7', 'error'] as const;
export const MOCK_CORRECT = 1;

export function HeroQuizMock() {
  const { t } = useTranslation();
  return (
    <figure className={styles.window} aria-label={t('landing.mock.label')}>
      <div className={styles.windowHeader}>
        <span className={styles.windowBrand}>
          <BrandMark height={18} /> Whetzy
        </span>
        <span className={styles.windowMeta}>{t('landing.mock.progress')}</span>
      </div>
      <div className={styles.windowBody}>
        <div className={styles.progressTrack} aria-hidden="true">
          <div className={styles.progressFill} />
        </div>
        <span className={styles.levelTag}>{t('landing.mock.level')}</span>
        <p className={styles.mockQuestion}>{t('landing.mock.question')}</p>
        <pre className={styles.mockCode}>print(len("Python"))</pre>
        <ol className={styles.mockOptions}>
          {MOCK_OPTIONS.map((o, i) => {
            const correct = i === MOCK_CORRECT;
            return (
              <li
                key={o}
                className={correct ? styles.mockOptionCorrect : styles.mockOption}
                data-correct={correct ? 'true' : undefined}
              >
                <span className={styles.mockLetter} aria-hidden="true">{String.fromCharCode(65 + i)}</span>
                <span>{o === 'error' ? t('landing.mock.error') : o}</span>
                {correct && <span className={styles.mockVerdict}>{t('landing.mock.correct')}</span>}
              </li>
            );
          })}
        </ol>
      </div>
      <figcaption className={styles.mockCaption}>{t('landing.mock.label')}</figcaption>
    </figure>
  );
}
