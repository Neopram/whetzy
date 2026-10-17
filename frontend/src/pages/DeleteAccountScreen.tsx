import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { API_BASE_URL as BASE_URL } from '../services/api';
import { useAppStore } from '../stores/useAppStore';
import { Button } from '../components/common/Button';
import styles from './DeleteAccountScreen.module.css';

type Phase = 'login' | 'confirm' | 'done' | 'error';

export function DeleteAccountScreen() {
  const { t } = useTranslation();
  const [phase, setPhase] = useState<Phase>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

  // Localised so an English user is not asked to type a Spanish word to
  // confirm an irreversible action. Label, placeholder and check all read it.
  const confirmWord = t('deleteAccount.confirmWord');

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        credentials: 'include',
        body: new URLSearchParams({ username: email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || t('deleteAccount.badCredentials'));
      }
      await res.json();
      setPhase('confirm');
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : t('deleteAccount.networkError'));
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
      const res = await fetch(`${BASE_URL}/auth/me/account`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!res.ok) throw new Error(t('deleteAccount.deleteFailed'));
      // La cuenta ya está desactivada: se cierra también la sesión de este
      // navegador, o «atrás» vuelve a Hoy con el usuario guardado (2026-10-17).
      useAppStore.getState().signOut();
      setPhase('done');
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : t('deleteAccount.networkError'));
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
