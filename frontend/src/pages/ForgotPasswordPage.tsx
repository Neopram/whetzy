import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { auth } from '../services/api';
import styles from './AuthScreen.module.css';

interface Props {
  onBack: () => void;
}

export function ForgotPasswordPage({ onBack }: Props) {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return setError(t('auth.errEmail'));
    }
    setLoading(true);
    try {
      await auth.requestPasswordReset(email.trim());
      setSubmitted(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : t('auth.errGeneric');
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  if (submitted) {
    return (
      <div className={styles.screen}>
        <div className={styles.brand}>
          <h1 className={styles.brandName}>✓ {t('auth.resetSent')}</h1>
        </div>
        <div className={styles.form}>
          <p style={{ textAlign: 'center', marginBottom: '1rem' }}>
            {t('auth.checkEmail')}: <strong>{email}</strong>
          </p>
          <p style={{ textAlign: 'center', fontSize: '0.9rem', opacity: 0.7, marginBottom: '2rem' }}>
            {t('auth.linkExpires')}
          </p>
          <button className={styles.submit} onClick={onBack} type="button">
            {t('auth.backToLogin')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.screen}>
      <div className={styles.brand}>
        <h1 className={styles.brandName}>{t('auth.resetPassword')}</h1>
        <p className={styles.tagline}>{t('auth.resetDescription')}</p>
      </div>

      <form className={styles.form} onSubmit={handleSubmit}>
        <label className={styles.field}>
          <span className={styles.label}>{t('auth.emailLabel')}</span>
          <input
            className={styles.input}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="tu@correo.com"
            disabled={loading}
            autoComplete="email"
            inputMode="email"
            required
          />
        </label>

        {error && <p className={styles.error}>⚠️ {error}</p>}

        <button className={styles.submit} type="submit" disabled={loading}>
          {loading ? t('auth.loading') : t('auth.sendReset')}
        </button>
      </form>

      <button
        onClick={onBack}
        type="button"
        style={{
          marginTop: '1.5rem',
          background: 'none',
          border: 'none',
          color: 'var(--le-primary)',
          cursor: 'pointer',
          fontSize: '0.95rem',
          textDecoration: 'underline',
        }}
      >
        ← {t('auth.backToLogin')}
      </button>
    </div>
  );
}