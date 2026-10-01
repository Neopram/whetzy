import { useTranslation } from 'react-i18next';
import { useAppStore } from '../../stores/useAppStore';
import styles from './RankingTabs.module.css';

/** Liga y duelos comparten la pestaña «Ranking» (design/v2): este selector es
 *  la única forma de pasar de una a otra. */
export function RankingTabs() {
  const { t } = useTranslation('common');
  const currentScreen = useAppStore((s) => s.currentScreen);
  const setScreen = useAppStore((s) => s.setScreen);

  return (
    <div className={styles.tabs} role="tablist" aria-label={t('nav.ranking')}>
      {(['league', 'duels'] as const).map((id) => (
        <button
          key={id}
          type="button"
          role="tab"
          aria-selected={currentScreen === id}
          className={`${styles.tab} ${currentScreen === id ? styles.active : ''}`}
          onClick={() => setScreen(id)}
        >
          {t(id === 'league' ? 'nav.league' : 'nav.duels')}
        </button>
      ))}
    </div>
  );
}
