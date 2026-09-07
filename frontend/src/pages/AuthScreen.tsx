import { useState } from 'react';
import { auth, type RegisterPayload } from '../services/api';
import styles from './AuthScreen.module.css';

type Mode = 'login' | 'register';

interface Props {
  onAuthed: () => void;
}

export function AuthScreen({ onAuthed }: Props) {
  const [mode, setMode] = useState<Mode>('register');
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [language, setLanguage] = useState<'es' | 'en'>('es');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const t = TEXT[language];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    // Client-side validation mirrors the backend schema constraints.
    if (mode === 'register') {
      if (displayName.trim().length < 1) return setError(t.errName);
      if (!/^[a-zA-Z0-9_.-]{3,50}$/.test(username)) return setError(t.errUsername);
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return setError(t.errEmail);
    if (password.length < 8) return setError(t.errPassword);

    setLoading(true);
    try {
      if (mode === 'register') {
        const payload: RegisterPayload = {
          email: email.trim(),
          username: username.trim(),
          display_name: displayName.trim(),
          password,
          language,
        };
        await auth.register(payload);
      } else {
        await auth.login(email.trim(), password);
      }
      onAuthed();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.errGeneric);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.screen}>
      <div className={styles.brand}>
        <div className={styles.logo}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" width="40" height="40">
            <path d="M12 12.5 12 4M12 12.5 5.5 19M12 12.5 18.5 19M12 4 5.5 19M5.5 19 18.5 19M18.5 19 12 4" opacity="0.55" />
            <circle cx="12" cy="12.5" r="2.6" fill="currentColor" stroke="none" />
            <circle cx="12" cy="4" r="1.9" fill="currentColor" stroke="none" />
            <circle cx="5.5" cy="19" r="1.9" fill="currentColor" stroke="none" />
            <circle cx="18.5" cy="19" r="1.9" fill="currentColor" stroke="none" />
          </svg>
        </div>
        <h1 className={styles.brandName}>Whetzy</h1>
        <p className={styles.tagline}>{t.tagline}</p>
      </div>

      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${mode === 'register' ? styles.tabActive : ''}`}
          onClick={() => { setMode('register'); setError(null); }}
          type="button"
        >
          {t.register}
        </button>
        <button
          className={`${styles.tab} ${mode === 'login' ? styles.tabActive : ''}`}
          onClick={() => { setMode('login'); setError(null); }}
          type="button"
        >
          {t.login}
        </button>
      </div>

      <form className={styles.form} onSubmit={handleSubmit}>
        {mode === 'register' && (
          <>
            <label className={styles.field}>
              <span className={styles.label}>{t.nameLabel}</span>
              <input
                className={styles.input}
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder={t.namePlaceholder}
                autoComplete="name"
              />
            </label>
            <label className={styles.field}>
              <span className={styles.label}>{t.usernameLabel}</span>
              <input
                className={styles.input}
                value={username}
                onChange={(e) => setUsername(e.target.value.toLowerCase())}
                placeholder={t.usernamePlaceholder}
                autoComplete="username"
              />
            </label>
          </>
        )}

        <label className={styles.field}>
          <span className={styles.label}>{t.emailLabel}</span>
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

        <label className={styles.field}>
          <span className={styles.label}>{t.passwordLabel}</span>
          <input
            className={styles.input}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t.passwordPlaceholder}
            autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
          />
        </label>

        {mode === 'register' && (
          <div className={styles.field}>
            <span className={styles.label}>{t.langLabel}</span>
            <div className={styles.langToggle}>
              <button
                type="button"
                className={`${styles.langBtn} ${language === 'es' ? styles.langActive : ''}`}
                onClick={() => setLanguage('es')}
              >
                Español
              </button>
              <button
                type="button"
                className={`${styles.langBtn} ${language === 'en' ? styles.langActive : ''}`}
                onClick={() => setLanguage('en')}
              >
                English
              </button>
            </div>
          </div>
        )}

        {error && <p className={styles.error}>⚠️ {error}</p>}

        <button className={styles.submit} type="submit" disabled={loading}>
          {loading ? t.loading : mode === 'register' ? t.registerCta : t.loginCta}
        </button>
      </form>

      <p className={styles.legal}>{t.legal}</p>
    </div>
  );
}

const TEXT = {
  es: {
    tagline: 'El motor que te aprende mientras aprendes',
    register: 'Crear cuenta',
    login: 'Iniciar sesión',
    nameLabel: 'Nombre',
    namePlaceholder: 'Cómo te llamamos',
    usernameLabel: 'Usuario',
    usernamePlaceholder: 'tu_usuario',
    emailLabel: 'Correo electrónico',
    passwordLabel: 'Contraseña',
    passwordPlaceholder: 'Mínimo 8 caracteres',
    langLabel: 'Idioma',
    registerCta: 'EMPEZAR A APRENDER',
    loginCta: 'ENTRAR',
    loading: 'Un momento…',
    legal: 'Al continuar aceptas los Términos y la Política de Privacidad.',
    errName: 'Ingresa tu nombre',
    errUsername: 'Usuario: 3-50 caracteres (letras, números, _ . -)',
    errEmail: 'Correo electrónico inválido',
    errPassword: 'La contraseña debe tener al menos 8 caracteres',
    errGeneric: 'Algo salió mal. Intenta de nuevo.',
  },
  en: {
    tagline: 'The engine that learns you while you learn',
    register: 'Sign up',
    login: 'Log in',
    nameLabel: 'Name',
    namePlaceholder: 'What we call you',
    usernameLabel: 'Username',
    usernamePlaceholder: 'your_username',
    emailLabel: 'Email',
    passwordLabel: 'Password',
    passwordPlaceholder: 'At least 8 characters',
    langLabel: 'Language',
    registerCta: 'START LEARNING',
    loginCta: 'LOG IN',
    loading: 'One moment…',
    legal: 'By continuing you accept the Terms and Privacy Policy.',
    errName: 'Enter your name',
    errUsername: 'Username: 3-50 chars (letters, numbers, _ . -)',
    errEmail: 'Invalid email address',
    errPassword: 'Password must be at least 8 characters',
    errGeneric: 'Something went wrong. Try again.',
  },
} as const;
