import { useState } from 'react';

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

type Phase = 'login' | 'confirm' | 'done' | 'error';

export function DeleteAccountScreen() {
  const [phase, setPhase] = useState<Phase>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [token, setToken] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username: email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Credenciales incorrectas');
      }
      const data = await res.json();
      setToken(data.access_token);
      setPhase('confirm');
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error de red');
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(e: React.FormEvent) {
    e.preventDefault();
    if (confirm !== 'CONFIRMAR') {
      setErrorMsg('Escribe CONFIRMAR exactamente para continuar.');
      return;
    }
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await fetch(`${BASE_URL}/auth/me/account`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Error al eliminar la cuenta');
      setPhase('done');
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error de red');
      setPhase('error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.title}>Eliminar cuenta</h1>

        {phase === 'login' && (
          <form onSubmit={handleLogin} style={styles.form}>
            <p style={styles.desc}>
              Inicia sesión para continuar con la eliminación de tu cuenta y todos tus datos.
            </p>
            <label style={styles.label}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={styles.input}
              placeholder="tu@email.com"
            />
            <label style={styles.label}>Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={styles.input}
              placeholder="••••••••"
            />
            {errorMsg && <p style={styles.error}>{errorMsg}</p>}
            <button type="submit" disabled={loading} style={styles.btnPrimary}>
              {loading ? 'Verificando...' : 'Continuar'}
            </button>
          </form>
        )}

        {phase === 'confirm' && (
          <form onSubmit={handleDelete} style={styles.form}>
            <div style={styles.warning}>
              <strong>Esto eliminará permanentemente:</strong>
              <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                <li>Tu cuenta y datos de perfil</li>
                <li>Tu historial de respuestas y progreso</li>
                <li>Tus badges, ligas y rachas</li>
                <li>Todas tus estadísticas de aprendizaje</li>
              </ul>
              <p style={{ marginTop: 8 }}>La eliminación es permanente a los 30 días (RGPD).</p>
            </div>
            <label style={styles.label}>Escribe CONFIRMAR para continuar</label>
            <input
              type="text"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              style={styles.input}
              placeholder="CONFIRMAR"
            />
            {errorMsg && <p style={styles.error}>{errorMsg}</p>}
            <button type="submit" disabled={loading} style={styles.btnDanger}>
              {loading ? 'Procesando...' : 'Eliminar mi cuenta y datos'}
            </button>
            <button type="button" onClick={() => setPhase('login')} style={styles.btnSecondary}>
              Cancelar
            </button>
          </form>
        )}

        {phase === 'done' && (
          <div style={styles.form}>
            <p style={{ color: '#2ecc71', fontWeight: 700, fontSize: 16 }}>
              Solicitud recibida.
            </p>
            <p style={styles.desc}>
              Tu cuenta ha sido desactivada y será eliminada permanentemente en 30 días.
              Si cambias de opinión, contacta con soporte antes de ese plazo.
            </p>
          </div>
        )}

        {phase === 'error' && (
          <div style={styles.form}>
            <p style={styles.error}>{errorMsg || 'Error inesperado. Inténtalo de nuevo.'}</p>
            <button onClick={() => setPhase('login')} style={styles.btnPrimary}>
              Volver a intentar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100dvh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#0f0f1a',
    padding: 16,
  },
  card: {
    background: '#1a1a2e',
    borderRadius: 16,
    padding: 32,
    maxWidth: 440,
    width: '100%',
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
  },
  title: {
    color: '#fff',
    fontSize: 22,
    fontWeight: 800,
    marginBottom: 16,
    margin: '0 0 16px',
  },
  desc: {
    color: '#9ca3af',
    fontSize: 14,
    lineHeight: 1.6,
    marginBottom: 16,
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  label: {
    color: '#9ca3af',
    fontSize: 13,
    fontWeight: 600,
  },
  input: {
    padding: '12px 14px',
    borderRadius: 8,
    border: '1px solid #374151',
    background: '#111827',
    color: '#fff',
    fontSize: 15,
    outline: 'none',
  },
  warning: {
    background: 'rgba(239,68,68,0.1)',
    border: '1px solid rgba(239,68,68,0.3)',
    borderRadius: 8,
    padding: 16,
    color: '#fca5a5',
    fontSize: 14,
    lineHeight: 1.6,
  },
  error: {
    color: '#ef4444',
    fontSize: 13,
    fontWeight: 600,
    margin: 0,
  },
  btnPrimary: {
    padding: '14px 20px',
    borderRadius: 10,
    border: 'none',
    background: '#3b82f6',
    color: '#fff',
    fontWeight: 700,
    fontSize: 15,
    cursor: 'pointer',
  },
  btnDanger: {
    padding: '14px 20px',
    borderRadius: 10,
    border: 'none',
    background: '#ef4444',
    color: '#fff',
    fontWeight: 700,
    fontSize: 15,
    cursor: 'pointer',
  },
  btnSecondary: {
    padding: '12px 20px',
    borderRadius: 10,
    border: '1px solid #374151',
    background: 'transparent',
    color: '#9ca3af',
    fontWeight: 600,
    fontSize: 14,
    cursor: 'pointer',
  },
};
