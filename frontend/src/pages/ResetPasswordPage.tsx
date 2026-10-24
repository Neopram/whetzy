import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { auth } from '../services/api';
import { Button } from '../components/common/Button';
import styles from './AuthScreen.module.css';
import { FormError } from '../components/common/FormError';
import { DrawnCheck } from '../components/common/DrawnCheck';

interface Props {
  token: string;
  onSuccess: () => void;
}

export function ResetPasswordPage({ token, onSuccess }: Props) {
  const { t } = useTranslation();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) return setError(t('resetPassword.minLength'));
    if (password !== confirm) return setError(t('resetPassword.mismatch'));
    setLoading(true);
    try {
      await auth.resetPassword(token, password);
      setDone(true);
      setTimeout(onSuccess, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('auth.errGeneric'));
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <div className={styles.screen}>
        {/* 46.15 A: el servidor aceptó el cambio; en un segundo pasa al login. */}
        <DrawnCheck />
        <p role="status">{t('resetPassword.success')}</p>
      </div>
    );
  }

  return (
    <div className={styles.screen}>
      {/* Sin encabezado, un lector de pantalla no sabía en qué página estaba
          (axe por ruta, 34.8). Mismo bloque que Olvidé la contraseña. */}
      <div className={styles.brand}>
        <h1 className={styles.brandName}>{t('resetPassword.title')}</h1>
      </div>
      <form className={styles.form} onSubmit={handleSubmit}>
        <label className={styles.field}>
          <span className={styles.label}>{t('resetPassword.newPasswordPlaceholder')}</span>
          <input
            className={styles.input}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t('resetPassword.newPasswordPlaceholder')}
            autoComplete="new-password"
          />
        </label>
        <label className={styles.field}>
          <span className={styles.label}>{t('resetPassword.confirmPlaceholder')}</span>
          <input
            className={styles.input}
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder={t('resetPassword.confirmPlaceholder')}
            autoComplete="new-password"
          />
        </label>
        {error && <FormError className={styles.error} message={error}>⚠️ {error}</FormError>}
        <Button type="submit" size="lg" full disabled={loading} className={styles.submit}>{loading ? t('auth.loading') : t('resetPassword.submit')}</Button>
      </form>
    </div>
  );
}
