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
      setError(err instanceof Error ? err.message : 'Error');
    } finally {
      setLoading(false);
    }
  }

  if (submitted) {
    return (
      <div className={styles.screen}>
        <h2>✓ Email enviado</h2>
        <p>Revisa: {email}</p>
        <button className={styles.submit} onClick={onBack}>Volver</button>
      </div>
    );
  }

  return (
    <div className={styles.screen}>
      <form className={styles.form} onSubmit={handleSubmit}>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="tu@correo.com" />
        {error && <p className={styles.error}>⚠️ {error}</p>}
        <button className={styles.submit} type="submit" disabled={loading}>{loading ? 'Cargando...' : 'Enviar'}</button>
      </form>
      <button onClick={onBack} style={{ marginTop: '1rem', background: 'none', border: 'none', color: 'var(--le-brand)', cursor: 'pointer' }}>Volver</button>
    </div>
  );
}
