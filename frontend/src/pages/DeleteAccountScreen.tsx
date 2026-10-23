import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ApiError, auth } from '../services/api';
import { useAppStore } from '../stores/useAppStore';
import { Button } from '../components/common/Button';
import styles from './DeleteAccountScreen.module.css';

type Phase = 'login' | 'mfa' | 'confirm' | 'done' | 'error';

export function DeleteAccountScreen() {
  const { t } = useTranslation();
  const [phase, setPhase] = useState<Phase>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaToken, setMfaToken] = useState<string | undefined>();
  const [code, setCode] = useState('');
  const [confirm, setConfirm] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

  // Localised so an English user is not asked to type a Spanish word to
  // confirm an irreversible action. Label, placeholder and check all read it.
  const confirmWord = t('deleteAccount.confirmWord');

  // Revisión de UI del 2026-10-23: el `detail` del backend ya no se pinta tal
  // cual (un 422 es una lista y salía como texto roto); cada caso tiene su texto.
  function loginError(err: unknown): string {
    if (!(err instanceof ApiError)) return t('deleteAccount.networkError');
    return err.status === 429 ? t('auth.mfaLocked') : t('deleteAccount.badCredentials');
  }

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await auth.login(email, password);
      // Con 2FA la contraseña sola no abre sesión: el borrado fallaba después
      // sin explicación. Se pide el código, como en el login.
      if ('mfa_required' in res) {
        setMfaToken(res.mfa_token);
        setCode('');
        setPhase('mfa');
      } else {
        setPhase('confirm');
      }
    } catch (err: unknown) {
      setErrorMsg(loginError(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleMfa(e: React.FormEvent) {
    e.preventDefault();
    if (code.trim().length < 6) {
      setErrorMsg(t('auth.mfaInvalid'));
      return;
    }
    setLoading(true);
    setErrorMsg('');
    try {
      await auth.login2fa(code, mfaToken);
      setPhase('confirm');
    } catch (err: unknown) {
      const status = err instanceof ApiError ? err.status : null;
      if (status === 429) setErrorMsg(t('auth.mfaLocked'));
      else if (status === 401) {
        setErrorMsg(t('auth.mfaExpired'));
        setPhase('login');
      } else if (err instanceof ApiError) setErrorMsg(t('auth.mfaInvalid'));
      else setErrorMsg(t('deleteAccount.networkError'));
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(e: React.FormEvent) {
    e.preventDefault();
    if (confirm !== confirmWord) {
      setErrorMsg(t('deleteAccount.confirmMismatch', { word: confirmWord }));
      return;
    }
    setLoading(true);
    setErrorMsg('');
    try {
      await auth.deleteAccount();
      // La cuenta ya está desactivada: se cierra también la sesión de este
      // navegador, o «atrás» vuelve a Hoy con el usuario guardado (2026-10-17).
      useAppStore.getState().signOut();
      setPhase('done');
    } catch (err: unknown) {
      setErrorMsg(err instanceof ApiError ? t('deleteAccount.deleteFailed') : t('deleteAccount.networkError'));
      setPhase('error');
    } finally {
      setLoading(false);
    }
  }

  // Serie 34: tokens en un módulo CSS (los colores fijos no cambiaban en modo
  // claro) y cada <label> asociada a su campo por id.
  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.title}>{t('deleteAccount.title')}</h1>

        {phase === 'login' && (
          <form onSubmit={handleLogin} className={styles.form}>
            <p className={styles.desc}>{t('deleteAccount.loginDesc')}</p>
            <label htmlFor="delete-email" className={styles.label}>{t('deleteAccount.email')}</label>
            <input
              id="delete-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className={styles.input}
              placeholder={t('deleteAccount.emailPlaceholder')}
            />
            <label htmlFor="delete-password" className={styles.label}>{t('deleteAccount.password')}</label>
            <input
              id="delete-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className={styles.input}
              placeholder="••••••••"
            />
            {errorMsg && <p className={styles.error} role="alert">{errorMsg}</p>}
            <Button type="submit" disabled={loading} full>
              {loading ? t('deleteAccount.verifying') : t('deleteAccount.continue')}
            </Button>
          </form>
        )}

        {phase === 'mfa' && (
          <form onSubmit={handleMfa} className={styles.form}>
            <p className={styles.desc}>{t('auth.mfaBody')}</p>
            <label htmlFor="delete-code" className={styles.label}>{t('auth.mfaCodeLabel')}</label>
            <input
              id="delete-code"
              type="text"
              inputMode="numeric"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
              autoComplete="one-time-code"
              className={styles.input}
            />
            {errorMsg && <p className={styles.error} role="alert">{errorMsg}</p>}
            <Button type="submit" disabled={loading} full>
              {loading ? t('deleteAccount.verifying') : t('deleteAccount.verifyCode')}
            </Button>
            <Button type="button" variant="secondary" onClick={() => setPhase('login')} full>
              {t('deleteAccount.cancel')}
            </Button>
          </form>
        )}

        {phase === 'confirm' && (
          <form onSubmit={handleDelete} className={styles.form}>
            <div className={styles.warning}>
              <strong>{t('deleteAccount.willDelete')}</strong>
              <ul className={styles.warningList}>
                <li>{t('deleteAccount.d1')}</li>
                <li>{t('deleteAccount.d2')}</li>
                <li>{t('deleteAccount.d3')}</li>
                <li>{t('deleteAccount.d4')}</li>
              </ul>
              <p className={styles.warningNote}>{t('deleteAccount.gdprNote')}</p>
            </div>
            <label htmlFor="delete-confirm" className={styles.label}>
              {t('deleteAccount.confirmLabel', { word: confirmWord })}
            </label>
            <input
              id="delete-confirm"
              type="text"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              autoComplete="off"
              className={styles.input}
              placeholder={confirmWord}
            />
            {errorMsg && <p className={styles.error} role="alert">{errorMsg}</p>}
            <Button type="submit" variant="danger" disabled={loading} full>
              {loading ? t('deleteAccount.processing') : t('deleteAccount.deleteCta')}
            </Button>
            <Button type="button" variant="secondary" onClick={() => setPhase('login')} full>
              {t('deleteAccount.cancel')}
            </Button>
          </form>
        )}

        {phase === 'done' && (
          <div className={styles.form}>
            <p className={styles.done}>{t('deleteAccount.doneTitle')}</p>
            <p className={styles.desc}>{t('deleteAccount.doneBody')}</p>
            {/* La sesión ya está cerrada: sin este enlace la pantalla era un callejón. */}
            <a href="/" className={styles.homeLink}>{t('deleteAccount.goHome')}</a>
          </div>
        )}

        {phase === 'error' && (
          <div className={styles.form}>
            <p className={styles.error} role="alert">{errorMsg || t('deleteAccount.unexpected')}</p>
            <Button type="button" onClick={() => setPhase('login')} full>
              {t('deleteAccount.retry')}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
