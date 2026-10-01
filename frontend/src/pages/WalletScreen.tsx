import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  economy,
  type CreditBalance,
  type CreditPrices,
  type ReferralCodeInfo,
} from '../services/api';
import styles from './WalletScreen.module.css';

export default function WalletScreen() {
  const { t, i18n } = useTranslation();
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
    return <div className={styles.screen}><p className={styles.muted} role="status">{t('common.loading')}</p></div>;
  }

  // Cada fila lleva su texto propio: el identificador del backend («module_done»,
  // «wallet.10/month»…) salía tal cual en pantalla (bug #7 de la auditoría).
  // Lo que no tenga traducción no se pinta.
  const earn = (prices?.grifos ?? []).filter((g) => i18n.exists(`wallet.earn.${g.event}`));
  const spend = (prices?.sumideros ?? []).filter((s) => i18n.exists(`wallet.spend.${s.item}`));
  // «Invitar amigos» promete créditos: solo se enseña si el backend lista el
  // referido como fuente (hoy no lo abona nadie, ver /economy/prices).
  const referralPays = earn.some((g) => g.event === 'referral_activated');

  return (
    <div className={styles.screen}>
      <h1 className={styles.title}>{t('wallet.title')}</h1>

      <section className={styles.balanceCard} aria-label={t('wallet.balance')}>
        <span className={styles.balanceAmount}>{balance?.balance ?? 0}</span>
        <span className={styles.balanceLabel}>{t('wallet.credits')}</span>
        {balance && balance.expires_in_days > 0 && (
          <span className={styles.balanceExpiry}>{t('wallet.expiresIn', { days: balance.expires_in_days })}</span>
        )}
      </section>

      {balance?.balance === 0 && <p className={styles.muted}>{t('wallet.noBalance')}</p>}

      {earn.length > 0 && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>{t('wallet.earnCredits')}</h2>
          <ul className={styles.list}>
            {earn.map((g) => (
              <li key={g.event} className={styles.row}>
                <span className={styles.rowBody}>
                  <span className={styles.rowName}>{t(`wallet.earn.${g.event}`)}</span>
                  {g.ladder && (
                    <span className={styles.rowMeta}>
                      {g.ladder.map(([from, amount]) => t('wallet.ladderStep', { from, amount })).join(' · ')}
                    </span>
                  )}
                </span>
                <span className={styles.amount}>+{g.credits}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {spend.length > 0 && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>{t('wallet.spendCredits')}</h2>
          <ul className={styles.list}>
            {spend.map((s) => (
              <li key={s.item} className={styles.row}>
                <span className={styles.rowName}>{t(`wallet.spend.${s.item}`)}</span>
                <span className={styles.amount}>−{s.cost}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {referral && referralPays && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>{t('wallet.referral')}</h2>
          <p className={styles.muted}>{t('wallet.referralDesc')}</p>
          <div className={styles.referralCode}>
            <code>{referral.code}</code>
            <button className={styles.btnSecondary} onClick={handleCopy} type="button">
              {copied ? t('wallet.copied') : t('wallet.copyCode')}
            </button>
          </div>
        </section>
      )}

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>{t('wallet.promo')}</h2>
        <form className={styles.promoForm} onSubmit={handleRedeem}>
          <label htmlFor="promo-code" className="visually-hidden">{t('wallet.promoPlaceholder')}</label>
          <input
            id="promo-code"
            className={styles.promoInput}
            type="text"
            value={promoCode}
            onChange={(e) => setPromoCode(e.target.value)}
            placeholder={t('wallet.promoPlaceholder')}
            autoComplete="off"
          />
          <button className={styles.btnSecondary} type="submit" disabled={promoLoading || !promoCode.trim()}>
            {t('wallet.redeem')}
          </button>
        </form>
        {promoMsg && (
          <p className={promoMsg.ok ? styles.promoSuccess : styles.promoError} role="status">
            {promoMsg.text}
          </p>
        )}
      </section>
    </div>
  );
}
