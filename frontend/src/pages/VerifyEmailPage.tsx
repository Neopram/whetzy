import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import i18n from '../i18n';
import { auth } from '../services/api';
import { Button } from '../components/common/Button';
import btn from '../components/common/Button.module.css';
import styles from './AuthScreen.module.css';
import { Loading } from '../components/common/Loading';

interface Props {
  token: string;
  /** `&lang=` del enlace (45.2); otro valor se ignora. */
  lang?: string | null;
}

function linkLang(lang: string | null | undefined): 'es' | 'en' | null {
  return lang === 'es' || lang === 'en' ? lang : null;
}

/** Canjes en curso por token. El backend solo acepta el primero (45.4); sin
 *  esto, el doble efecto de StrictMode (y un remontaje) mandaba un segundo
 *  canje que daba 400 y la página decía «enlace no válido» tras verificar.
 *  Resuelve a si hay sesión en este navegador. */
const inFlight = new Map<string, Promise<boolean>>();

function redeem(token: string): Promise<boolean> {
  let pending = inFlight.get(token);
  if (!pending) {
    pending = auth.verifyEmail(token).then(() => auth.me().then(() => true, () => false));
    inFlight.set(token, pending);
    const forget = () => inFlight.delete(token);
    pending.then(forget, forget);
  }
  return pending;
}

/** `/verify-email?token=...` -- el enlace que manda `email.py`.
 *
 * El backend (`POST /auth/verify-email`, `POST /auth/resend-verification`)
 * ya existía y funcionaba; no había ninguna página que consumiera el
 * `token` de la URL ni llamara al endpoint (0.2) -- quien pulsara el
 * enlace del correo no llegaba a ningún sitio que lo verificara.
 *
 * 45.4 (ADR-66 E5): sale en el idioma del enlace y, tras verificar, con
 * sesión «Continuar» lleva a `/` (la app vuelve a pedir `/auth/me` y la
 * franja de 45.3 desaparece); sin sesión, «Iniciar sesión» a `/login?lang=`.
 */
export function VerifyEmailPage({ token, lang }: Props) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<'checking' | 'ok' | 'error'>('checking');
  const [signedIn, setSignedIn] = useState(false);
  const [email, setEmail] = useState('');
  const [resendState, setResendState] = useState<'idle' | 'sending' | 'sent'>('idle');

  useEffect(() => {
    const wanted = linkLang(lang);
    if (wanted && i18n.language !== wanted) void i18n.changeLanguage(wanted);
  }, [lang]);

  useEffect(() => {
    if (!token) {
      setStatus('error');
      return;
    }
    let alive = true;
    // ¿Hay sesión en este navegador? Decide adónde lleva el botón.
    redeem(token)
      .then((me) => {
        if (!alive) return;
        setSignedIn(me);
        setStatus('ok');
      })
      .catch(() => {
        if (alive) setStatus('error');
      });
    return () => {
      alive = false;
    };
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
    return <Loading label={t('auth.loading')} shape="card" />;
  }

  if (status === 'ok') {
    return (
      <div className={styles.screen}>
        <p>{t('verifyEmail.success')}</p>
        {/* Un enlace con el aspecto del Button común: navegar es un <a>, no un <button>. */}
        {signedIn ? (
          <a className={`${btn.btn} ${btn.primary} ${btn.lg} ${btn.full} ${styles.submit}`} href="/">
            {t('verifyEmail.continue')}
          </a>
        ) : (
          <a
            className={`${btn.btn} ${btn.primary} ${btn.lg} ${btn.full} ${styles.submit}`}
            href={`/login?lang=${linkLang(lang) ?? (i18n.language === 'en' ? 'en' : 'es')}`}
          >
            {t('verifyEmail.login')}
          </a>
        )}
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
