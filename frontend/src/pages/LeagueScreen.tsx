import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card } from '../components/common/Card';
import { useApi } from '../hooks/useApi';
import { league as leagueApi, type LeagueStandingsResponse } from '../services/api';
import styles from './LeagueScreen.module.css';

const TIER_META: Record<string, { icon: string }> = {
  bronze: { icon: '🥉' }, silver: { icon: '🥈' }, gold: { icon: '🥇' },
  platinum: { icon: '💎' }, diamond: { icon: '👑' },
};

export function LeagueScreen() {
  const { t, i18n } = useTranslation();
  const fetched = useApi(() => leagueApi.current(), []);
  // Tras cambiar la participación manda la respuesta del PUT, sin recargar.
  const [override, setOverride] = useState<LeagueStandingsResponse | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(false);
  const data = override ?? fetched.data;
  const { loading, error } = fetched;

  async function toggleParticipation(next: boolean) {
    setSaving(true);
    setSaveError(false);
    try {
      setOverride(await leagueApi.setParticipation(next));
    } catch {
      setSaveError(true);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className={styles.screen}><p className={styles.loading}>{t('league.loading')}</p></div>;
  if (error || !data) return <div className={styles.screen}><p className={styles.loading}>{t('league.empty')}</p></div>;

  const tier = TIER_META[data.league.tier] ?? { icon: '🏆' };
  // `data.league.name` is a Spanish-only internal label ("Bronce", "Platino"),
  // so rendering it directly showed "League Platino" to English users. The
  // tier key is language-neutral, so the display name comes from i18n; the
  // server name is only a fallback for a tier the client doesn't know yet.
  const leagueName = i18n.exists(`league.tiers.${data.league.tier}`)
    ? t(`league.tiers.${data.league.tier}`)
    : data.league.name;
  const top3 = data.standings.slice(0, 3);
  const rest = data.standings.slice(3);

  return (
    <div className={styles.screen}>
      <div className={styles.leagueHeader}>
        <span className={styles.leagueIcon}>{tier.icon}</span>
        <h1 className={styles.leagueName}>{t('league.league')} {leagueName}</h1>
        {data.participating && <p className={styles.leagueInfo}>{t('league.rules')}</p>}
        <label className={styles.optToggle}>
          <input
            type="checkbox"
            role="switch"
            checked={data.participating}
            disabled={saving}
            onChange={(e) => toggleParticipation(e.target.checked)}
          />
          <span>{t('league.participate')}</span>
        </label>
        <p className={styles.optNote}>{t('league.optionalNote')}</p>
        {saveError && <p className={styles.optNote} role="alert">{t('league.participationError')}</p>}
      </div>

      {!data.participating && (
        <Card>
          <p className={styles.loading}>{t('league.optedOut')}</p>
        </Card>
      )}

      {data.participating && top3.length >= 1 && (
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

      {data.participating && <Card>
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
      </Card>}
    </div>
  );
}
