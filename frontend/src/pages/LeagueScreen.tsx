import { useTranslation } from 'react-i18next';
import { Card } from '../components/common/Card';
import { useApi } from '../hooks/useApi';
import { league as leagueApi } from '../services/api';
import styles from './LeagueScreen.module.css';

const TIER_META: Record<string, { icon: string }> = {
  bronze: { icon: '🥉' }, silver: { icon: '🥈' }, gold: { icon: '🥇' },
  platinum: { icon: '💎' }, diamond: { icon: '👑' },
};

export function LeagueScreen() {
  const { t } = useTranslation();
  const { data, loading, error } = useApi(() => leagueApi.current(), []);

  if (loading) return <div className={styles.screen}><p className={styles.loading}>{t('league.loading')}</p></div>;
  if (error || !data) return <div className={styles.screen}><p className={styles.loading}>{t('league.empty')}</p></div>;

  const tier = TIER_META[data.league.tier] ?? { icon: '🏆' };
  const top3 = data.standings.slice(0, 3);
  const rest = data.standings.slice(3);

  return (
    <div className={styles.screen}>
      <div className={styles.leagueHeader}>
        <span className={styles.leagueIcon}>{tier.icon}</span>
        <h1 className={styles.leagueName}>{t('league.league')} {data.league.name}</h1>
        <p className={styles.leagueInfo}>{t('league.rules')}</p>
      </div>

      {top3.length >= 1 && (
        <div className={styles.podium}>
          {[top3[1], top3[0], top3[2]].map((p, i) => {
            if (!p) return <div key={i} className={styles.podiumSlot} />;
            const heights = [85, 110, 70];
            const medals = ['🥈', '🥇', '🥉'];
            return (
              <div key={p.user_id} className={styles.podiumSlot}>
                <span className={styles.podiumAvatar}>{p.avatar_emoji}</span>
                <span className={styles.podiumName}>{p.display_name.split(' ')[0]}</span>
                <span className={styles.podiumXp}>{p.xp_earned.toLocaleString()} XP</span>
                <div className={styles.podiumBar} style={{ height: heights[i] }}><span className={styles.podiumMedal}>{medals[i]}</span></div>
              </div>
            );
          })}
        </div>
      )}

      <Card>
        {rest.length === 0 && top3.length <= 1 && <p className={styles.loading}>{t('league.soloWeek')}</p>}
        {rest.map((p) => (
          <div key={p.user_id} className={`${styles.row} ${p.is_current_user ? styles.rowUser : ''}`}>
            <span className={styles.rowRank}>{p.rank}</span>
            <span className={styles.rowAvatar}>{p.avatar_emoji}</span>
            <div className={styles.rowInfo}>
              <span className={styles.rowName}>{p.display_name}{p.is_current_user ? ` (${t('league.you')})` : ''}</span>
              <span className={styles.rowXp}>{p.xp_earned.toLocaleString()} XP</span>
            </div>
            {data.promotion_zone > 0 && p.rank <= data.promotion_zone && <span className={styles.rowPromo}>▲</span>}
            {data.demotion_zone > 0 && p.rank > data.standings.length - data.demotion_zone && <span className={styles.rowDemote}>▼</span>}
          </div>
        ))}
      </Card>
    </div>
  );
}
