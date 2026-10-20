import { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Card } from '../components/common/Card';
import { RankingTabs } from '../components/layout/RankingTabs';
import { useApi } from '../hooks/useApi';
import { ApiError, league as leagueApi, type LeagueStandingsResponse } from '../services/api';
import styles from './LeagueScreen.module.css';
import { listItemVariants, listVariants } from '../lib/motion';
import { GameIcon, type GameIconName } from '../components/common/AppIcon';
import { Loading } from '../components/common/Loading';

const TIER_META: Record<string, { icon: GameIconName }> = {
  bronze: { icon: 'bronce' }, silver: { icon: 'plata' }, gold: { icon: 'oro' },
  platinum: { icon: 'gema' }, diamond: { icon: 'corona' },
};

export function LeagueScreen() {
  const { t, i18n } = useTranslation();
  const reduce = useReducedMotion();
  // 404 = el servidor no tiene ligas sembradas: no hay liga, no es un fallo.
  // Antes cualquier error (red, 500) decía «la liga se activará cuando ganes
  // XP», que no era verdad en ninguno de los dos casos.
  const fetched = useApi(
    () => leagueApi.current().catch((e: unknown) => {
      if (e instanceof ApiError && e.status === 404) return null;
      throw e;
    }),
    [],
  );
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

  if (loading) return <div className={styles.screen}><RankingTabs /><Loading label={t('league.loading')} shape="list" /></div>;
  if (error) {
    return (
      <div className={styles.screen}>
        <RankingTabs />
        <p className={styles.loading} role="alert">{t('league.loadError')}</p>
        <button type="button" className={styles.retry} onClick={fetched.reload}>{t('league.retry')}</button>
      </div>
    );
  }
  if (!data) return <div className={styles.screen}><RankingTabs /><p className={styles.loading}>{t('league.notOpen')}</p></div>;

  const tier = TIER_META[data.league.tier] ?? { icon: 'trofeo' as const };
  // `data.league.name` is a Spanish-only internal label ("Bronce", "Platino"),
  // so rendering it directly showed "League Platino" to English users. The
  // tier key is language-neutral, so the display name comes from i18n; the
  // server name is only a fallback for a tier the client doesn't know yet.
  const leagueName = i18n.exists(`league.tiers.${data.league.tier}`)
    ? t(`league.tiers.${data.league.tier}`)
    : data.league.name;
  const top3 = data.standings.slice(0, 3);
  // 46.13: podio y filas entran escalonados; la ▲ late una vez. Sin ceremonia de
  // ascenso: el servidor aún no aplica ascensos (plan §6.2).
  const stagger = reduce
    ? {}
    : { 'data-enter': 'stagger', variants: listVariants, initial: 'initial', animate: 'animate' } as const;
  const rest = data.standings.slice(3);

  return (
    <div className={styles.screen}>
      <RankingTabs />
      <div className={styles.leagueHeader}>
        <span className={styles.leagueIcon}><GameIcon name={tier.icon} size={48} /></span>
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
        <motion.div className={styles.podium} data-testid="league-podium" {...stagger}>
          {[top3[1], top3[0], top3[2]].map((p, i) => {
            if (!p) return <div key={i} className={styles.podiumSlot} />;
            const heights = [85, 110, 70];
            const medals: GameIconName[] = ['plata', 'oro', 'bronce'];
            return (
              <motion.div key={p.user_id} className={styles.podiumSlot} variants={listItemVariants}>
                <span className={styles.podiumAvatar}>{p.avatar_emoji}</span>
                <span className={styles.podiumName}>{p.display_name.split(' ')[0]}</span>
                <span className={styles.podiumXp}>{p.xp_earned.toLocaleString()} XP</span>
                <div className={styles.podiumBar} style={{ height: heights[i] }}><span className={styles.podiumMedal}><GameIcon name={medals[i]} size={28} /></span></div>
              </motion.div>
            );
          })}
        </motion.div>
      )}

      {data.participating && <Card>
        {rest.length === 0 && top3.length <= 1 && <p className={styles.loading}>{t('league.soloWeek')}</p>}
        <motion.div data-testid="league-rows" {...stagger}>
        {rest.map((p) => (
          <motion.div key={p.user_id} className={`${styles.row} ${p.is_current_user ? styles.rowUser : ''}`} variants={listItemVariants}>
            <span className={styles.rowRank}>{p.rank}</span>
            <span className={styles.rowAvatar}>{p.avatar_emoji}</span>
            <div className={styles.rowInfo}>
              <span className={styles.rowName}>{p.display_name}{p.is_current_user ? ` (${t('league.you')})` : ''}</span>
              <span className={styles.rowXp}>{p.xp_earned.toLocaleString()} XP</span>
            </div>
            {data.promotion_zone > 0 && p.rank <= data.promotion_zone && (
              <motion.span
                className={styles.rowPromo}
                data-fx={reduce ? undefined : 'pulse-once'}
                animate={reduce ? undefined : { scale: [1, 1.3, 1] }}
                transition={{ duration: 0.4, delay: 0.5 }}
              >▲</motion.span>
            )}
            {data.demotion_zone > 0 && p.rank > data.total_members - data.demotion_zone && <span className={styles.rowDemote}>▼</span>}
          </motion.div>
        ))}
        </motion.div>
      </Card>}
    </div>
  );
}
