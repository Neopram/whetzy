import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Capacitor } from '@capacitor/core';
import { useReducedMotion } from 'framer-motion';

import {
  economy,
  masteryReports,
  type CreditBalance,
  type CreditPrices,
  type ReferralCodeInfo,
} from '../services/api';
import { StaggerItem, StaggerList } from '../components/common/Stagger';
import styles from './WalletScreen.module.css';
import { Loading } from '../components/common/Loading';
import { ErrorState } from '../components/common/ErrorState';
import { CountUp } from '../components/quiz/CountUp';
import { DUR } from '../lib/motion';

export default function WalletScreen() {
  const { t, i18n } = useTranslation();
  // Las tiendas (App Store / Google Play) no permiten comprar ni canjear valor
  // fuera de su propio pago: en la app nativa no se enseña el canje (24.6).
  const native = Capacitor.isNativePlatform();
  const [balance, setBalance] = useState<CreditBalance | null>(null);
  const [prices, setPrices] = useState<CreditPrices | null>(null);
  const [referral, setReferral] = useState<ReferralCodeInfo | null>(null);
  const [loading, setLoading] = useState(true);
  // 2026-10-24: un fallo se tragaba y la pantalla decía «0 créditos».
  const [loadFailed, setLoadFailed] = useState(false);
  const [copied, setCopied] = useState(false);

  const [promoCode, setPromoCode] = useState('');
  const [promoLoading, setPromoLoading] = useState(false);
  const [promoMsg, setPromoMsg] = useState<{ ok: boolean; text: string } | null>(null);

  // Informe de dominio (§2.3): un request_id por intento, para que reintentar
  // tras un corte no cobre dos veces.
  const [reportBusy, setReportBusy] = useState(false);
  const [reportCode, setReportCode] = useState<string | null>(null);
  const [reportError, setReportError] = useState(false);

  // §7.5 bloque D: el saldo cuenta cuando cambia (canjear, comprar), no al
  // entrar. `countFrom` es el saldo de antes del cambio; null, nada que contar.
  const reduce = useReducedMotion() ?? false;
  const [countFrom, setCountFrom] = useState<number | null>(null);
  const balanceNow = useRef<number | null>(null);
  useEffect(() => { balanceNow.current = balance?.balance ?? null; }, [balance]);

  const load = useCallback(async () => {
    try {
      const [b, p, r] = await Promise.all([
        economy.balance(),
        economy.prices(),
        economy.referralCode(),
      ]);
      if (balanceNow.current !== null) setCountFrom(balanceNow.current);
      setBalance(b);
      setPrices(p);
      setReferral(r);
      setLoadFailed(false);
    } catch {
      // Un fallo no es un saldo vacío: se dice y se puede reintentar.
      setLoadFailed(true);
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

  const [reportRequest, setReportRequest] = useState(() => crypto.randomUUID());
  async function buyReport() {
    setReportBusy(true);
    setReportError(false);
    try {
      const report = await masteryReports.buy(reportRequest);
      setReportCode(report.code);
      setReportRequest(crypto.randomUUID()); // el siguiente es otra compra
      await load();
    } catch {
      setReportError(true); // el mismo request_id: reintentar no cobra dos veces
    } finally {
      setReportBusy(false);
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
      if (balance) setCountFrom(balance.balance);
      setBalance((prev) => prev ? { ...prev, balance: result.balance } : prev);
      setPromoCode('');
    } catch {
      setPromoMsg({ ok: false, text: t('wallet.redeemError') });
    } finally {
      setPromoLoading(false);
    }
  }

  if (loading) {
    return <div className={styles.screen}><Loading label={t('common.loading')} shape="list" /></div>;
  }

  if (loadFailed) {
    return (
      <div className={styles.screen}>
        <h1 className={styles.title}>{t('wallet.title')}</h1>
        <ErrorState message={t('common.loadError')} onRetry={() => { setLoading(true); void load(); }} />
      </div>
    );
  }

  // Cada fila lleva su texto propio: el identificador del backend («module_done»,
  // «wallet.10/month»…) salía tal cual en pantalla (bug #7 de la auditoría).
  // Lo que no tenga traducción no se pinta.
  const earn = (prices?.grifos ?? []).filter((g) => i18n.exists(`wallet.earn.${g.event}`));
  const spend = (prices?.sumideros ?? []).filter((s) => i18n.exists(`wallet.spend.${s.item}`));
  // «Invitar amigos» promete créditos: solo se enseña si el backend lista el
  // referido como fuente (ADR-35; /economy/prices solo lista lo cableado).
  const referralPays = earn.some((g) => g.event === 'referral_activated');

  return (
    <div className={styles.screen}>
      <h1 className={styles.title}>{t('wallet.title')}</h1>

      <section className={styles.balanceCard} aria-label={t('wallet.balance')}>
        {(() => {
          const value = balance?.balance ?? 0;
          const counts = !reduce && countFrom !== null && countFrom !== value;
          return (
            <span className={styles.balanceAmount} data-testid="wallet-balance" data-fx={counts ? 'count' : undefined}>
              <CountUp value={value} from={countFrom ?? value} state={counts ? 'run' : 'done'} durationMs={DUR.response * 1000} />
            </span>
          );
        })()}
        <span className={styles.balanceLabel}>{t('wallet.credits')}</span>
        {balance && balance.expires_in_days > 0 && (
          <span className={styles.balanceExpiry}>{t('wallet.expiresIn', { days: balance.expires_in_days })}</span>
        )}
      </section>

      {balance?.balance === 0 && <p className={styles.muted}>{t('wallet.noBalance')}</p>}

      {earn.length > 0 && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>{t('wallet.earnCredits')}</h2>
          <StaggerList className={styles.list}>
            {earn.map((g) => (
              <StaggerItem key={g.event} className={styles.row}>
                <span className={styles.rowBody}>
                  <span className={styles.rowName}>{t(`wallet.earn.${g.event}`)}</span>
                  {g.event === 'referral_activated' && (
                    <span className={styles.rowMeta}>{t('wallet.activationRule')}</span>
                  )}
                  {g.event === 'referral_welcome' && (
                    <span className={styles.rowMeta}>{t('wallet.welcomeRule')}</span>
                  )}
                  {i18n.exists(`wallet.earnRule.${g.event}`) && (
                    <span className={styles.rowMeta}>{t(`wallet.earnRule.${g.event}`)}</span>
                  )}
                  {g.milestones && (
                    <span className={styles.rowMeta}>
                      {g.milestones
                        .filter((m) => i18n.exists(`wallet.milestone.${m.reward}`))
                        .map((m) => t(`wallet.milestone.${m.reward}`, { at: m.at }))
                        .join(' · ')}
                    </span>
                  )}
                </span>
                <span className={styles.amount}>+{g.credits}</span>
              </StaggerItem>
            ))}
          </StaggerList>
          {prices?.learning_monthly_cap ? (
            <p className={styles.muted}>{t('wallet.learningCap', { cap: prices.learning_monthly_cap })}</p>
          ) : null}
        </section>
      )}

      {spend.length > 0 && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>{t('wallet.spendCredits')}</h2>
          <StaggerList className={styles.list}>
            {spend.map((s) => (
              <StaggerItem key={s.item} className={styles.row}>
                <span className={styles.rowBody}>
                  <span className={styles.rowName}>{t(`wallet.spend.${s.item}`)}</span>
                  {s.item === 'mastery_report' && (
                    <span className={styles.rowMeta}>{t('wallet.reportRule')}</span>
                  )}
                </span>
                <span className={styles.amount}>−{s.cost}</span>
                {s.item === 'mastery_report' && !native && (
                  <button
                    type="button"
                    className={styles.btnSecondary}
                    disabled={reportBusy || (balance?.balance ?? 0) < s.cost}
                    onClick={() => void buyReport()}
                  >
                    {t('wallet.reportCta')}
                  </button>
                )}
              </StaggerItem>
            ))}
          </StaggerList>
          {reportCode && (
            <p className={styles.muted} role="status">
              {t('wallet.reportReady')}{' '}
              <a className={styles.reportLink} href={`/report/${reportCode}`}>{`${window.location.host}/report/${reportCode}`}</a>
            </p>
          )}
          {reportError && <p className={styles.muted} role="alert">{t('wallet.reportError')}</p>}
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

      {!native && (
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
      )}
    </div>
  );
}
