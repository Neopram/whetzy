import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { auth } from '../services/api';
import { Button } from '../components/common/Button';
import btn from '../components/common/Button.module.css';
import styles from './AuthScreen.module.css';

interface Props {
  token: string;
}

/** `/verify-email?token=...` -- el enlace que manda `email.py`.
 *
 * El backend (`POST /auth/verify-email`, `POST /auth/resend-verification`)
 * ya existía y funcionaba; no había ninguna página que consumiera el
 * `token` de la URL ni llamara al endpoint (0.2) -- quien pulsara el
 * enlace del correo no llegaba a ningún sitio que lo verificara.
 */
export function VerifyEmailPage({ token }: Props) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<'checking' | 'ok' | 'error'>('checking');
  const [email, setEmail] = useState('');
  const [resendState, setResendState] = useState<'idle' | 'sending' | 'sent'>('idle');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      return;
    }
    auth
      .verifyEmail(token)
      .then(() => setStatus('ok'))
      .catch(() => setStatus('error'));
  }, [token]);

  async function handleResend(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;
    setResendState('sending');
    try {
      await auth.resendVerification(email);
    } finally {
      // Siempre 200 desde el backend, se exista o no ese email (no revela
      // nada): el mensaje de éxito es el mismo pase lo que pase.
      setResendState('sent');
    }
  }

  if (status === 'checking') {
    return <div className={styles.screen}>{t('auth.loading')}</div>;
  }

  if (status === 'ok') {
    return (
      <div className={styles.screen}>
        <p>{t('verifyEmail.success')}</p>
        {/* Un enlace con el aspecto del Button común: navegar es un <a>, no un <button>. */}
        <a className={`${btn.btn} ${btn.primary} ${btn.lg} ${btn.full} ${styles.submit}`} href="/login">
          {t('verifyEmail.continue')}
        </a>
      </div>
    );
  }

  return (
    <div className={styles.screen}>
      <p>{t('verifyEmail.invalidOrExpired')}</p>
      {resendState === 'sent' ? (
        <p>{t('verifyEmail.resendSent')}</p>
      ) : (
        <form className={styles.form} onSubmit={handleResend}>
          <label className={styles.field}>
            <span className={styles.label}>{t('verifyEmail.emailPlaceholder')}</span>
            <input
              className={styles.input}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('verifyEmail.emailPlaceholder')}
              autoComplete="email"
            />
          </label>
          <Button type="submit" size="lg" full disabled={resendState === 'sending'} className={styles.submit}>
            {resendState === 'sending' ? t('auth.loading') : t('verifyEmail.resend')}
          </Button>
        </form>
      )}
    </div>
  );
}
