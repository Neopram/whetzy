import { useState } from 'react';
import { auth } from '../services/api';
import styles from './AuthScreen.module.css';

interface Props {
  onBack: () => void;
}

export function ForgotPasswordPage({ onBack }: Props) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return setError('Email inválido');
    setLoading(true);
    try {
      await auth.requestPasswordReset(email.trim());
      setSubmitted(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error';
      setError(
        msg === 'email_not_configured'
          ? 'El envío de correos no está disponible ahora mismo, así que no podemos mandarte el enlace. Escríbenos a soporte para recuperar tu cuenta.'
          : msg,
      );
    } finally {
      setLoading(false);
    }
  }

  if (submitted) {
    return (
      <div className={styles.screen}>
        <div className={styles.brand}>
          <h1 className={styles.brandName}>Revisa tu correo</h1>
          <p className={styles.tagline}>
            Si {email} tiene una cuenta, te llegará un enlace para restablecer la contraseña.
          </p>
        </div>
        <button className={styles.submit} onClick={onBack}>Volver</button>
      </div>
    );
  }

  return (
    <div className={styles.screen}>
      <div className={styles.brand}>
        <h1 className={styles.brandName}>¿Olvidaste tu contraseña?</h1>
        <p className={styles.tagline}>Te mandamos un enlace para restablecerla.</p>
      </div>

      <form className={styles.form} onSubmit={handleSubmit}>
        <label className={styles.field}>
          <span className={styles.label}>Correo electrónico</span>
          <input
            className={styles.input}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="tu@correo.com"
            autoComplete="email"
            inputMode="email"
          />
        </label>
        {error && <p className={styles.error}>⚠️ {error}</p>}
        <button className={styles.submit} type="submit" disabled={loading}>{loading ? 'Cargando...' : 'Enviar'}</button>
      </form>
      <button type="button" className={styles.forgotLink} onClick={onBack}>Volver</button>
    </div>
  );
}
