import { useState } from 'react';
import { auth } from '../services/api';
import styles from './AuthScreen.module.css';

interface Props {
  token: string;
  onSuccess: () => void;
}

export function ResetPasswordPage({ token, onSuccess }: Props) {
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) return setError('Mínimo 8 caracteres');
    if (password !== confirm) return setError('No coinciden');
    setLoading(true);
    try {
      await auth.resetPassword(token, password);
      setTimeout(onSuccess, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.screen}>
      <form className={styles.form} onSubmit={handleSubmit}>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Nueva contraseña" />
        <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="Confirmar" />
        {error && <p className={styles.error}>⚠️ {error}</p>}
        <button className={styles.submit} type="submit" disabled={loading}>{loading ? 'Cargando...' : 'Cambiar'}</button>
      </form>
    </div>
  );
}
