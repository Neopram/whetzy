import { useTranslation } from 'react-i18next';
import { useAppStore } from '../stores/useAppStore';
import styles from './OnboardingScreen.module.css';

interface Props { onDone: () => void; }

export function OnboardingScreen({ onDone }: Props) {
  const user = useAppStore((s) => s.user);
  const startQuiz = useAppStore((s) => s.startQuiz);
  const { t } = useTranslation();

  function handleStart() {
    try {
      localStorage.setItem(`whetzy_onboarded_${user.id}`, '1');
    } catch { /* storage unavailable */ }
    startQuiz('study', 10);
    onDone();
  }

  return (
    <div className={styles.screen}>
      <div className={styles.logoWrap} aria-hidden="true">
        <div className={styles.logo}>⚡</div>
        <span className={styles.logoText}>Whetzy</span>
      </div>

      <h1 className={styles.headline}>{t('onboarding.headline')}</h1>
      <p className={styles.sub}>{t('onboarding.sub')}</p>

      <ul className={styles.features} aria-label="Características">
        <li className={styles.feature}>
          <span className={styles.featureIcon} aria-hidden="true">🎯</span>
          <div>
            <strong className={styles.featureTitle}>{t('onboarding.f1')}</strong>
            <span className={styles.featureDesc}>{t('onboarding.f1d')}</span>
          </div>
        </li>
        <li className={styles.feature}>
          <span className={styles.featureIcon} aria-hidden="true">⚡</span>
          <div>
            <strong className={styles.featureTitle}>{t('onboarding.f2')}</strong>
            <span className={styles.featureDesc}>{t('onboarding.f2d')}</span>
          </div>
        </li>
        <li className={styles.feature}>
          <span className={styles.featureIcon} aria-hidden="true">🏆</span>
          <div>
            <strong className={styles.featureTitle}>{t('onboarding.f3')}</strong>
            <span className={styles.featureDesc}>{t('onboarding.f3d')}</span>
          </div>
        </li>
      </ul>

      <button className={styles.cta} onClick={handleStart} aria-label={t('onboarding.cta')}>
        {t('onboarding.cta')}
      </button>
    </div>
  );
}
