import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { auth } from '../services/api';
import { Button } from '../components/common/Button';
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
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return setError(t('auth.errEmail'));
    setLoading(true);
    try {
      await auth.requestPasswordReset(email.trim());
      setSubmitted(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : t('auth.errGeneric');
      setError(msg === 'email_not_configured' ? t('forgotPassword.emailNotConfigured') : msg);
    } finally {
      setLoading(false);
    }
  }

  if (submitted) {
    return (
      <div className={styles.screen}>
        <div className={styles.brand}>
          <h1 className={styles.brandName}>{t('forgotPassword.checkEmailTitle')}</h1>
          <p className={styles.tagline}>{t('forgotPassword.checkEmailBody', { email })}</p>
        </div>
        <Button type="button" size="lg" full onClick={onBack} className={styles.submit}>{t('forgotPassword.back')}</Button>
      </div>
    );
  }

  return (
    <div className={styles.screen}>
      <div className={styles.brand}>
        <h1 className={styles.brandName}>{t('forgotPassword.title')}</h1>
        <p className={styles.tagline}>{t('forgotPassword.tagline')}</p>
      </div>

      <form className={styles.form} onSubmit={handleSubmit}>
        <label className={styles.field}>
          <span className={styles.label}>{t('auth.emailLabel')}</span>
          <input
            className={styles.input}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t('forgotPassword.emailPlaceholder')}
            autoComplete="email"
            inputMode="email"
          />
        </label>
        {error && <p className={styles.error}>⚠️ {error}</p>}
        <Button type="submit" size="lg" full disabled={loading} className={styles.submit}>{loading ? t('auth.loading') : t('forgotPassword.submit')}</Button>
      </form>
      <button type="button" className={styles.forgotLink} onClick={onBack}>{t('forgotPassword.back')}</button>
    </div>
  );
}
