import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { auth } from '../../services/api';
import { DEFAULT_USER_ID, useAppStore } from '../../stores/useAppStore';
import styles from './VerifyEmailBanner.module.css';

/**
 * 45.3 (ADR-66 E4): «Te enviamos un enlace a fe***@gmail.com · Reenviar · ×».
 *
 * Va en el armazón de la app (no dentro de Hoy) mientras la cuenta no esté
 * verificada. No bloquea nada (E3). «Reenviar» usa el endpoint público que ya
 * existe con el email de la cuenta y espera 60 s entre envíos; la × la oculta
 * durante esta sesión del navegador.
 */

const DISMISS_KEY = 'whetzy_verify_banner_dismissed';
const COOLDOWN_S = 60;

/** `federico@gmail.com` → `fe***@gmail.com`. Sin arroba, se deja tal cual. */
export function maskEmail(email: string): string {
  const at = email.indexOf('@');
  if (at < 1) return email;
  return `${email.slice(0, Math.min(2, at))}***${email.slice(at)}`;
}

function wasDismissed(): boolean {
  try {
    return sessionStorage.getItem(DISMISS_KEY) === '1';
  } catch {
    return false;
  }
}

export function VerifyEmailBanner() {
  const { t } = useTranslation();
  const user = useAppStore((s) => s.user);
  const [dismissed, setDismissed] = useState(wasDismissed);
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  // Hasta cuándo no se puede reenviar; el contador sale del reloj, no de sumar ticks.
  const [until, setUntil] = useState(0);
  const [now, setNow] = useState(() => Date.now());
  const wait = Math.max(0, Math.ceil((until - now) / 1000));

  useEffect(() => {
    if (until <= Date.now()) return;
    const id = setInterval(() => {
      const n = Date.now();
      setNow(n);
      if (n >= until) clearInterval(id);
    }, 1000);
    return () => clearInterval(id);
  }, [until]);

  if (dismissed || user.id === DEFAULT_USER_ID || user.emailVerified || !user.email) return null;

  const resend = async () => {
    setStatus('sending');
    try {
      await auth.resendVerification(user.email);
      setStatus('sent');
      const t0 = Date.now();
      setNow(t0);
      setUntil(t0 + COOLDOWN_S * 1000);
    } catch {
      setStatus('error');
    }
  };

  const dismiss = () => {
    try {
      sessionStorage.setItem(DISMISS_KEY, '1');
    } catch {
      // Sin almacenamiento se oculta igual hasta recargar.
    }
    setDismissed(true);
  };

  return (
    <div className={styles.banner} role="status" data-testid="verify-email-banner">
      <p className={styles.text}>
        {t('verifyBanner.text', { email: maskEmail(user.email) })}
        {status === 'sent' && <span className={styles.note}> {t('verifyBanner.sent')}</span>}
        {status === 'error' && <span className={styles.error}> {t('verifyBanner.error')}</span>}
      </p>
      <div className={styles.actions}>
        <button
          type="button"
          className={styles.resend}
          onClick={resend}
          disabled={status === 'sending' || wait > 0}
        >
          {wait > 0 ? t('verifyBanner.resendIn', { s: wait }) : t('verifyBanner.resend')}
        </button>
        <button
          type="button"
          className={styles.close}
          onClick={dismiss}
          aria-label={t('verifyBanner.dismiss')}
        >
          <span aria-hidden="true">×</span>
        </button>
      </div>
    </div>
  );
}
