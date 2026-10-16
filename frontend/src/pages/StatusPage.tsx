import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { API_BASE_URL } from '../services/api';
import styles from './StatusPage.module.css';

/** `API_BASE_URL` ends in the api/v1 path; the health check lives at the API's
 *  origin instead, so this strips exactly that suffix rather than assuming
 *  a fixed number of path segments. */
const HEALTH_URL = `${API_BASE_URL.replace(/\/api\/v1\/?$/, '')}/health/ready`;

const POLL_INTERVAL_MS = 30_000;

export type ComponentStatus = 'up' | 'down' | 'unknown';
export type OverallStatus = 'operational' | 'degraded' | 'down' | 'checking';

export interface HealthState {
  overall: OverallStatus;
  api: ComponentStatus;
  db: ComponentStatus;
  lastChecked: Date | null;
}

/** `/health/ready` (backend/app/main.py) solo devuelve `{"status": "ready"}`
 *  en éxito y un 503 con `{"detail": "Database not ready"}` en fallo — nunca
 *  un campo `database`/`db`/`checks` que leer del cuerpo. La versión anterior
 *  de esta página buscaba exactamente eso, así que `db` se quedaba en
 *  `'unknown'` para siempre (el candidato que buscaba nunca existía) y el
 *  estado `'degraded'` era código muerto: ninguna respuesta real lo
 *  alcanzaba. Una base de datos caída se veía indistinguible de la API
 *  entera caída (0.16).
 *
 *  La única comprobación que hace `/health/ready` es un `SELECT 1`: su único
 *  modo de fallo es la base de datos. Así que el propio código HTTP ya dice
 *  todo lo que hay que saber — un 503 significa que el proceso respondió
 *  (la API está viva) pero la base de datos no, exactamente "degraded"; que
 *  `fetch` ni siquiera consiga una respuesta sí significa que no hay nada
 *  vivo al otro lado. */
export async function checkHealth(): Promise<HealthState> {
  const now = new Date();
  try {
    const res = await fetch(HEALTH_URL, { credentials: 'omit' });
    if (res.ok) {
      return { overall: 'operational', api: 'up', db: 'up', lastChecked: now };
    }
    return { overall: 'degraded', api: 'up', db: 'down', lastChecked: now };
  } catch {
    return { overall: 'down', api: 'down', db: 'unknown', lastChecked: now };
  }
}

/** Public `/status` page (no auth). Polls the backend's health endpoint every
 *  30s so anyone — including someone locked out of the app — can see whether
 *  Whetzy is up without opening a support ticket. */
export default function StatusPage() {
  const { t } = useTranslation();
  const [state, setState] = useState<HealthState>({
    overall: 'checking',
    api: 'unknown',
    db: 'unknown',
    lastChecked: null,
  });
  const mounted = useRef(true);

  const poll = useCallback(async () => {
    const result = await checkHealth();
    if (mounted.current) setState(result);
  }, []);

  useEffect(() => {
    mounted.current = true;
    poll();
    const id = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      mounted.current = false;
      clearInterval(id);
    };
  }, [poll]);

  const overallLabel = {
    checking: t('statusChecking'),
    operational: t('statusOperational'),
    degraded: t('statusDegraded'),
    down: t('statusDown'),
  }[state.overall];

  const overallDot = {
    checking: styles.dotUnknown,
    operational: styles.dotUp,
    degraded: styles.dotDegraded,
    down: styles.dotDown,
  }[state.overall];

  const componentDot: Record<ComponentStatus, string> = {
    up: styles.dotUp,
    down: styles.dotDown,
    unknown: styles.dotUnknown,
  };

  return (
    <div className={styles.screen}>
      <h1 className={styles.title}>Whetzy · {t('statusTitle')}</h1>

      <div className={styles.overallCard}>
        <span className={`${styles.dot} ${overallDot}`} aria-hidden="true" />
        <span className={styles.overallLabel}>{overallLabel}</span>
      </div>

      <div className={styles.section}>
        <div className={styles.row}>
          <span className={styles.rowLabel}>{t('statusApi')}</span>
          <span className={styles.rowValue}>
            <span className={`${styles.dot} ${componentDot[state.api]}`} aria-hidden="true" />
            {t(state.api === 'up' ? 'statusOperational' : state.api === 'down' ? 'statusDown' : 'statusChecking')}
          </span>
        </div>
        <div className={styles.row}>
          <span className={styles.rowLabel}>{t('statusDb')}</span>
          <span className={styles.rowValue}>
            <span className={`${styles.dot} ${componentDot[state.db]}`} aria-hidden="true" />
            {t(state.db === 'up' ? 'statusOperational' : state.db === 'down' ? 'statusDown' : 'statusChecking')}
          </span>
        </div>
      </div>

      <p className={styles.lastChecked}>
        {t('statusLastChecked')}: {state.lastChecked ? state.lastChecked.toLocaleTimeString() : t('statusChecking')}
      </p>
    </div>
  );
}
