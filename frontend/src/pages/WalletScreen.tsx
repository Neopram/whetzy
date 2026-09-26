import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  economy,
  type CreditBalance,
  type CreditPrices,
  type ReferralCodeInfo,
} from '../services/api';
import styles from './WalletScreen.module.css';

const CAP_LABELS: Record<string, string> = {
  once: 'once',
  per_module: 'perModule',
  per_week: 'perWeek',
  per_month: 'perMonth',
};

export default function WalletScreen() {
  const { t } = useTranslation();
  const [balance, setBalance] = useState<CreditBalance | null>(null);
  const [prices, setPrices] = useState<CreditPrices | null>(null);
  const [referral, setReferral] = useState<ReferralCodeInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  const [promoCode, setPromoCode] = useState('');
  const [promoLoading, setPromoLoading] = useState(false);
  const [promoMsg, setPromoMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const load = useCallback(async () => {
    try {
      const [b, p, r] = await Promise.all([
        economy.balance(),
        economy.prices(),
        economy.referralCode(),
      ]);
      setBalance(b);
      setPrices(p);
      setReferral(r);
    } catch {
      // API error — show empty state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleCopy() {
    if (!referral) return;
    try {
      await navigator.clipboard.writeText(referral.share_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard API blocked
    }
  }

  async function handleRedeem(e: React.FormEvent) {
    e.preventDefault();
    const code = promoCode.trim();
    if (!code) return;
    setPromoLoading(true);
    setPromoMsg(null);
    try {
      const result = await economy.redeemPromo(code);
      setPromoMsg({ ok: true, text: t('wallet.redeemSuccess', { credits: result.credits }) });
      setBalance((prev) => prev ? { ...prev, balance: result.balance } : prev);
      setPromoCode('');
    } catch {
      setPromoMsg({ ok: false, text: t('wallet.redeemError') });
    } finally {
      setPromoLoading(false);
    }
  }

  if (loading) {
    return <div className={styles.screen}><p className={styles.loading}>{t('common.loading')}</p></div>;
  }

  return (
    <div className={styles.screen}>
      {/* Balance */}
      <div className={styles.balanceCard}>
        <div className={styles.balanceAmount}>{balance?.balance ?? 0}</div>
        <div className={styles.balanceLabel}>{t('wallet.credits')}</div>
        {balance && balance.expires_in_days > 0 && (
          <div className={styles.balanceExpiry}>
            {t('wallet.expiresIn', { days: balance.expires_in_days })}
          </div>
        )}
      </div>

      {balance?.balance === 0 && (
        <p className={styles.empty}>{t('wallet.noBalance')}</p>
      )}

      {/* Earn credits */}
      {prices && prices.grifos.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>{t('wallet.earnCredits')}</h3>
          {prices.grifos.map((g) => (
            <div key={g.event} className={styles.creditRow}>
              <div>
                <div className={styles.creditEvent}>{g.event.replace(/_/g, ' ')}</div>
                <div className={styles.creditCap}>{t(`wallet.${CAP_LABELS[g.cap] ?? g.cap}`)}</div>
              </div>
              <div className={`${styles.creditAmount} ${styles.earn}`}>+{g.credits}</div>
            </div>
          ))}
        </div>
      )}

      {/* Spend credits */}
      {prices && prices.sumideros.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>{t('wallet.spendCredits')}</h3>
          {prices.sumideros.map((s) => (
            <div key={s.item} className={styles.creditRow}>
              <div className={styles.creditEvent}>{s.item.replace(/_/g, ' ')}</div>
              <div className={`${styles.creditAmount} ${styles.spend}`}>-{s.cost}</div>
            </div>
          ))}
        </div>
      )}

      {/* Referral */}
      {referral && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>{t('wallet.referral')}</h3>
          <div className={styles.referralBox}>
            <p className={styles.referralDesc}>{t('wallet.referralDesc')}</p>
            <div className={styles.referralCode}>
              <span>{referral.code}</span>
              <button className={styles.copyBtn} onClick={handleCopy} type="button">
                {copied ? t('wallet.copied') : t('wallet.copyCode')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Promo */}
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>{t('wallet.promo')}</h3>
        <form className={styles.promoForm} onSubmit={handleRedeem}>
          <input
            className={styles.promoInput}
            type="text"
            value={promoCode}
            onChange={(e) => setPromoCode(e.target.value)}
            placeholder={t('wallet.promoPlaceholder')}
          />
          <button className={styles.promoBtn} type="submit" disabled={promoLoading || !promoCode.trim()}>
            {t('wallet.redeem')}
          </button>
        </form>
        {promoMsg && (
          <p className={`${styles.promoMsg} ${promoMsg.ok ? styles.promoSuccess : styles.promoError}`}>
            {promoMsg.text}
          </p>
        )}
      </div>
    </div>
  );
}
