import { useAppStore } from '../stores/useAppStore';
import styles from './OnboardingScreen.module.css';

const TEXT = {
  es: {
    headline: 'Aprende Python de 0 a AI Engineer',
    sub: 'El motor que se adapta a tu ritmo y te hace avanzar cada día.',
    f1: 'Adaptativo', f1d: 'Preguntas calibradas a tu nivel exacto',
    f2: 'Gamificado', f2d: 'XP, rachas, ligas y duelos en vivo',
    f3: 'Certificaciones', f3d: 'De Python básico a cloud y AI',
    cta: 'EMPEZAR A APRENDER',
  },
  en: {
    headline: 'Learn Python — from zero to AI Engineer',
    sub: 'The engine that adapts to your pace and pushes you forward every day.',
    f1: 'Adaptive', f1d: 'Questions calibrated to your exact level',
    f2: 'Gamified', f2d: 'XP, streaks, leagues and live duels',
    f3: 'Certifications', f3d: 'From basic Python to cloud and AI',
    cta: 'START LEARNING',
  },
} as const;

interface Props { onDone: () => void; }

export function OnboardingScreen({ onDone }: Props) {
  const user = useAppStore((s) => s.user);
  const startQuiz = useAppStore((s) => s.startQuiz);
  const L = TEXT[user.language];

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

      <h1 className={styles.headline}>{L.headline}</h1>
      <p className={styles.sub}>{L.sub}</p>

      <ul className={styles.features} aria-label="Características">
        <li className={styles.feature}>
          <span className={styles.featureIcon} aria-hidden="true">🎯</span>
          <div>
            <strong className={styles.featureTitle}>{L.f1}</strong>
            <span className={styles.featureDesc}>{L.f1d}</span>
          </div>
        </li>
        <li className={styles.feature}>
          <span className={styles.featureIcon} aria-hidden="true">⚡</span>
          <div>
            <strong className={styles.featureTitle}>{L.f2}</strong>
            <span className={styles.featureDesc}>{L.f2d}</span>
          </div>
        </li>
        <li className={styles.feature}>
          <span className={styles.featureIcon} aria-hidden="true">🏆</span>
          <div>
            <strong className={styles.featureTitle}>{L.f3}</strong>
            <span className={styles.featureDesc}>{L.f3d}</span>
          </div>
        </li>
      </ul>

      <button className={styles.cta} onClick={handleStart} aria-label={L.cta}>
        {L.cta}
      </button>
    </div>
  );
}
