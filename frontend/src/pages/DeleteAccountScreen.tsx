import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { API_BASE_URL as BASE_URL } from '../services/api';

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
      setPhase('done');
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : t('deleteAccount.networkError'));
      setPhase('error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.title}>{t('deleteAccount.title')}</h1>

        {phase === 'login' && (
          <form onSubmit={handleLogin} style={styles.form}>
            <p style={styles.desc}>
              {t('deleteAccount.loginDesc')}
            </p>
            <label style={styles.label}>{t('deleteAccount.email')}</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={styles.input}
              placeholder={t('deleteAccount.emailPlaceholder')}
            />
            <label style={styles.label}>{t('deleteAccount.password')}</label>
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
              {loading ? t('deleteAccount.verifying') : t('deleteAccount.continue')}
            </button>
          </form>
        )}

        {phase === 'confirm' && (
          <form onSubmit={handleDelete} style={styles.form}>
            <div style={styles.warning}>
              <strong>{t('deleteAccount.willDelete')}</strong>
              <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                <li>{t('deleteAccount.d1')}</li>
                <li>{t('deleteAccount.d2')}</li>
                <li>{t('deleteAccount.d3')}</li>
                <li>{t('deleteAccount.d4')}</li>
              </ul>
              <p style={{ marginTop: 8 }}>{t('deleteAccount.gdprNote')}</p>
            </div>
            <label style={styles.label}>{t('deleteAccount.confirmLabel', { word: confirmWord })}</label>
            <input
              type="text"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              style={styles.input}
              placeholder={confirmWord}
            />
            {errorMsg && <p style={styles.error}>{errorMsg}</p>}
            <button type="submit" disabled={loading} style={styles.btnDanger}>
              {loading ? t('deleteAccount.processing') : t('deleteAccount.deleteCta')}
            </button>
            <button type="button" onClick={() => setPhase('login')} style={styles.btnSecondary}>
              {t('deleteAccount.cancel')}
            </button>
          </form>
        )}

        {phase === 'done' && (
          <div style={styles.form}>
            <p style={{ color: 'var(--le-success-text)', fontWeight: 700, fontSize: 16 }}>
              {t('deleteAccount.doneTitle')}
            </p>
            <p style={styles.desc}>
              {t('deleteAccount.doneBody')}
            </p>
          </div>
        )}

        {phase === 'error' && (
          <div style={styles.form}>
            <p style={styles.error}>{errorMsg || t('deleteAccount.unexpected')}</p>
            <button onClick={() => setPhase('login')} style={styles.btnPrimary}>
              {t('deleteAccount.retry')}
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
    background: 'var(--le-bg)',
    padding: 16,
  },
  card: {
    background: 'var(--le-surface)', border: '1px solid var(--le-border)',
    borderRadius: 16,
    padding: 32,
    maxWidth: 440,
    width: '100%',
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
  },
  title: {
    color: 'var(--le-text)',
    fontSize: 22,
    fontWeight: 800,
    marginBottom: 16,
    margin: '0 0 16px',
  },
  desc: {
    color: 'var(--le-text-secondary)',
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
    color: 'var(--le-text-secondary)',
    fontSize: 13,
    fontWeight: 600,
  },
  input: {
    padding: '12px 14px',
    borderRadius: 8,
    border: '1px solid var(--le-border)',
    background: 'var(--le-bg)',
    color: 'var(--le-text)',
    fontSize: 15,
    outline: 'none',
  },
  warning: {
    background: 'rgba(239,68,68,0.1)',
    border: '1px solid rgba(239,68,68,0.3)',
    borderRadius: 8,
    padding: 16,
    color: 'var(--le-danger-text)',
    fontSize: 14,
    lineHeight: 1.6,
  },
  error: {
    color: 'var(--le-danger-text)',
    fontSize: 13,
    fontWeight: 600,
    margin: 0,
  },
  btnPrimary: {
    padding: '14px 20px',
    borderRadius: 10,
    border: 'none',
    background: 'var(--le-brand)',
    color: 'var(--le-text-inverse)',
    fontWeight: 700,
    fontSize: 15,
    cursor: 'pointer',
  },
  btnDanger: {
    padding: '14px 20px',
    borderRadius: 10,
    border: 'none',
    background: 'var(--le-danger)',
    color: 'var(--le-text-inverse)',
    fontWeight: 700,
    fontSize: 15,
    cursor: 'pointer',
  },
  btnSecondary: {
    padding: '12px 20px',
    borderRadius: 10,
    border: '1px solid var(--le-border)',
    background: 'transparent',
    color: 'var(--le-text-secondary)',
    fontWeight: 600,
    fontSize: 14,
    cursor: 'pointer',
  },
};
