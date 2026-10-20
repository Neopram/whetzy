import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ApiError, adminUsers, type AdminLogItem } from '../../services/api';
import { Button } from '../common/Button';
import styles from './UsersPanel.module.css';

/**
 * Admin → Registro (44.3, docs/PLAN_BACKOFFICE.md B6): quién abrió qué ficha y
 * qué hizo, con su motivo. Solo se lee: nada aquí lo edita ni lo borra.
 */
export function ActionLogPanel() {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState<AdminLogItem[] | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    adminUsers.log(page).then(
      (p) => { if (!cancelled) { setItems(p.items); setTotal(p.total); } },
      (err) => {
        if (cancelled) return;
        setError(t(err instanceof ApiError && err.message === '2fa_required' ? 'admin.users.errors.twoFactor' : 'admin.users.errors.generic'));
      },
    );
    return () => { cancelled = true; };
  }, [page, t]);

  if (error) return <p className={styles.error} role="alert">{error}</p>;
  if (!items) return <p className={styles.hint}>{t('admin.users.loading')}</p>;
  if (items.length === 0) return <p className={styles.hint}>{t('admin.log.empty')}</p>;

  const pages = Math.max(1, Math.ceil(total / 20));
  return (
    <div className={styles.panel}>
      <ul className={styles.list} aria-label={t('admin.log.title')}>
        {items.map((it) => (
          <li key={it.id} className={`${styles.row} ${styles.static}`}>
            <span className={styles.muted}>{new Date(it.created_at).toLocaleString(i18n.language)}</span>
            <span className={styles.username}>{t(`admin.log.actions.${it.action}`, { defaultValue: it.action })}</span>
            <span>{it.actor_username ?? '—'} → {it.target_username ?? '—'}</span>
            <span className={styles.muted}>{it.reason ?? ''}</span>
          </li>
        ))}
      </ul>
      {pages > 1 && (
        <div className={styles.actions}>
          <Button type="button" variant="ghost" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>{t('admin.log.prev')}</Button>
          <span className={styles.muted}>{t('admin.log.page', { page, pages })}</span>
          <Button type="button" variant="ghost" size="sm" disabled={page >= pages} onClick={() => setPage(page + 1)}>{t('admin.log.next')}</Button>
        </div>
      )}
    </div>
  );
}
