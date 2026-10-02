import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { adminEconomy, type AdminReferral, type ClawbackReason } from '../../services/api';
import styles from './ReferralClawback.module.css';

const REASONS: ClawbackReason[] = ['fraud', 'refund', 'ban'];

/**
 * Admin → Economía: referidos activados o abonados y su clawback (ECONOMIA
 * §3.5). Hasta el 2026-10-02 no había forma de deshacer un referido: ni
 * endpoint ni pantalla. El clawback recupera lo que quede de los 300 créditos
 * (nunca deja saldo negativo) y retira el premio del hito si se baja de él.
 */
export function ReferralClawback() {
  const { t } = useTranslation();
  const [rows, setRows] = useState<AdminReferral[] | null>(null);
  const [reason, setReason] = useState<Record<string, ClawbackReason>>({});
  const [confirming, setConfirming] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const { referrals } = await adminEconomy.referrals('all');
      setRows(referrals.filter((r) => r.status === 'credited' || r.status === 'activated'));
    } catch {
      setError(t('admin.referrals.loadError'));
    }
  }
  useEffect(() => { void load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function run(id: string) {
    setBusy(true);
    setError(null);
    try {
      const res = await adminEconomy.clawback(id, reason[id] ?? 'fraud');
      setMessage(
        t('admin.referrals.done', { recovered: res.recovered_credits, unrecovered: res.unrecovered_credits })
        + (res.milestone_revoked ? ` ${t('admin.referrals.milestoneRevoked', { milestone: res.milestone_revoked })}` : ''),
      );
      setConfirming(null);
      await load();
    } catch {
      setError(t('admin.referrals.error'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className={styles.block} aria-labelledby="admin-referrals">
      <h3 id="admin-referrals">{t('admin.referrals.title')}</h3>
      <p className={styles.hint}>{t('admin.referrals.hint')}</p>
      {message && <p className={styles.done} role="status">{message}</p>}
      {error && <p className={styles.error} role="alert">{error}</p>}
      {rows === null ? null : rows.length === 0 ? (
        <p>{t('admin.referrals.empty')}</p>
      ) : (
        <ul className={styles.list}>
          {rows.map((r) => (
            <li key={r.id} className={styles.item}>
              <span className={styles.meta}>
                <code>{r.referrer_id.slice(0, 8)}</code> → <code>{r.referred_id.slice(0, 8)}</code> ·{' '}
                {t(`admin.referrals.status.${r.status}`)}
              </span>
              <label className={styles.field}>
                <span>{t('admin.referrals.reason')}</span>
                <select
                  value={reason[r.id] ?? 'fraud'}
                  onChange={(e) => setReason({ ...reason, [r.id]: e.target.value as ClawbackReason })}
                >
                  {REASONS.map((x) => <option key={x} value={x}>{t(`admin.referrals.reasons.${x}`)}</option>)}
                </select>
              </label>
              {confirming === r.id ? (
                <span className={styles.actions}>
                  <button type="button" className={styles.danger} disabled={busy} onClick={() => void run(r.id)}>
                    {t('admin.referrals.confirm')}
                  </button>
                  <button type="button" className={styles.secondary} onClick={() => setConfirming(null)}>
                    {t('admin.referrals.cancel')}
                  </button>
                </span>
              ) : (
                <button type="button" className={styles.secondary} onClick={() => setConfirming(r.id)}>
                  {t('admin.referrals.clawback')}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
