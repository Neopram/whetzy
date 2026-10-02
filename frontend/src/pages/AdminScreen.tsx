import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { ReferralClawback } from '../components/admin/ReferralClawback';
import styles from './AdminScreen.module.css';
import { API_BASE_URL } from '../services/api';

interface Metrics {
  dau?: number;
  wau?: number;
  mau?: number;
  total_users?: number;
  active_7d?: number;
  retention_d1?: number;
  retention_d7?: number;
  p50?: number;
  p90?: number;
  p95?: number;
  p99?: number;
  count?: number;
}

type Tab = 'metrics' | 'security' | 'content' | 'ops' | 'gdpr' | 'revenue' | 'economy';

export function AdminScreen() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<Tab>('metrics');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [metricsData, setMetricsData] = useState<Metrics>({});
  const [securityData, setSecurityData] = useState<any>({});
  const [contentData, setContentData] = useState<any>({});
  const [recentReports, setRecentReports] = useState<{ id: string; question_id: string; reason: string; notes: string | null; created_at: string | null }[]>([]);
  const [opsData, setOpsData] = useState<any>({});
  const [gdprData, setGDPRData] = useState<any>({});
  const [revenueData, setRevenueData] = useState<any>({});
  const [economyData, setEconomyData] = useState<any>({});

  const apiBase = API_BASE_URL;
  const fetchOpts = (): RequestInit => ({
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });


  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiBase}/admin/metrics/users?range_days=7`, fetchOpts());
      if (!res.ok) throw new Error(t('admin.errors.fetchFailed'));
      const data = await res.json();
      setMetricsData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('admin.errors.generic'));
    } finally {
      setLoading(false);
    }
  };

  const fetchSecurity = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiBase}/admin/security/auth-events?limit=10`, fetchOpts());
      if (!res.ok) throw new Error(t('admin.errors.fetchFailed'));
      const data = await res.json();
      setSecurityData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('admin.errors.generic'));
    } finally {
      setLoading(false);
    }
  };

  const fetchContent = async () => {
    try {
      setLoading(true);
      setError(null);
      const [res, rep] = await Promise.all([
        fetch(`${apiBase}/admin/content/gaps?language=es`, fetchOpts()),
        fetch(`${apiBase}/admin/reports/recent?limit=50`, fetchOpts()),
      ]);
      if (!res.ok || !rep.ok) throw new Error(t('admin.errors.fetchFailed'));
      setContentData(await res.json());
      setRecentReports((await rep.json()).reports ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('admin.errors.generic'));
    } finally {
      setLoading(false);
    }
  };

  const fetchOps = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiBase}/admin/ops/health`, fetchOpts());
      if (!res.ok) throw new Error(t('admin.errors.fetchFailed'));
      const data = await res.json();
      setOpsData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('admin.errors.generic'));
    } finally {
      setLoading(false);
    }
  };

  const fetchGDPR = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiBase}/admin/gdpr/exports?status=pending`, fetchOpts());
      if (!res.ok) throw new Error(t('admin.errors.fetchFailed'));
      const data = await res.json();
      setGDPRData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('admin.errors.generic'));
    } finally {
      setLoading(false);
    }
  };

  const fetchRevenue = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiBase}/admin/revenue/mrr?month=2026-09`, fetchOpts());
      if (!res.ok) throw new Error(t('admin.errors.fetchFailed'));
      const data = await res.json();
      setRevenueData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('admin.errors.generic'));
    } finally {
      setLoading(false);
    }
  };

  const fetchEconomy = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiBase}/admin/economy/credits?limit=10`, fetchOpts());
      if (!res.ok) throw new Error(t('admin.errors.fetchFailed'));
      const data = await res.json();
      setEconomyData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('admin.errors.generic'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    switch (activeTab) {
      case 'metrics':
        fetchMetrics();
        break;
      case 'security':
        fetchSecurity();
        break;
      case 'content':
        fetchContent();
        break;
      case 'ops':
        fetchOps();
        break;
      case 'gdpr':
        fetchGDPR();
        break;
      case 'revenue':
        fetchRevenue();
        break;
      case 'economy':
        fetchEconomy();
        break;
    }
  }, [activeTab]);

  const tabs: { id: Tab; label: string }[] = [
    { id: 'metrics', label: t('admin.tabs.metrics') },
    { id: 'security', label: t('admin.tabs.security') },
    { id: 'content', label: t('admin.tabs.content') },
    { id: 'ops', label: t('admin.tabs.ops') },
    { id: 'gdpr', label: t('admin.tabs.gdpr') },
    { id: 'revenue', label: t('admin.tabs.revenue') },
    { id: 'economy', label: t('admin.tabs.economy') },
  ];

  return (
    <div className={styles.admin}>
      <div className={styles.header}>
        <h1>{t('admin.title')}</h1>
        <p className={styles.subtitle}>{t('admin.subtitle')}</p>
      </div>

      <div className={styles.tabs}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`${styles.tab} ${activeTab === tab.id ? styles.active : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className={styles.content}>
        {loading && <LoadingState message={t('admin.loading', 'Cargando datos del panel...')} />}
        {error && <ErrorState message={error} onRetry={() => {}} />}

        {!loading && !error && activeTab === 'metrics' && (
          <div className={styles.panel}>
            <h2>{t('admin.panel.metrics')}</h2>
            <div className={styles.grid}>
              <StatCard label={t('admin.metrics.dau')} value={metricsData.dau} />
              <StatCard label={t('admin.metrics.wau')} value={metricsData.wau} />
              <StatCard label={t('admin.metrics.mau')} value={metricsData.mau} />
              <StatCard label={t('admin.metrics.totalUsers')} value={metricsData.total_users} />
              <StatCard label={t('admin.metrics.retentionD1')} value={t('admin.metrics.percent', { value: metricsData.retention_d1 })} />
              <StatCard label={t('admin.metrics.retentionD7')} value={t('admin.metrics.percent', { value: metricsData.retention_d7 })} />
            </div>
          </div>
        )}

        {!loading && !error && activeTab === 'security' && (
          <div className={styles.panel}>
            <h2>{t('admin.panel.security')}</h2>
            <p>{t('admin.security.authEvents')}: {securityData.events?.length || 0}</p>
            <p>{t('admin.security.lockouts')}: {securityData.lockouts?.length || 0}</p>
          </div>
        )}

        {!loading && !error && activeTab === 'content' && (
          <div className={styles.panel}>
            <h2>{t('admin.panel.content')}</h2>
            <div className={styles.grid}>
              <StatCard label={t('admin.metrics.totalSkills')} value={contentData.total_skills} />
              <StatCard label={t('admin.metrics.esCount')} value={contentData.es_count} />
              <StatCard label={t('admin.metrics.enCount')} value={contentData.en_count} />
              <StatCard label={t('admin.metrics.parity')} value={contentData.parity_percent} />
            </div>
            <h3>{t('admin.reports.title')}</h3>
            {recentReports.length === 0 ? (
              <p>{t('admin.reports.empty')}</p>
            ) : (
              <ul className={styles.reportList}>
                {recentReports.map((r) => (
                  <li key={r.id} className={styles.reportItem}>
                    <code>{r.question_id}</code> · {t(`admin.reports.reasons.${r.reason}`, { defaultValue: r.reason })}
                    {r.created_at && <> · {new Date(r.created_at).toLocaleString()}</>}
                    {r.notes && <p className={styles.reportNotes}>{r.notes}</p>}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {!loading && !error && activeTab === 'ops' && (
          <div className={styles.panel}>
            <h2>{t('admin.panel.ops')}</h2>
            <div className={styles.grid}>
              <StatCard label={t('admin.metrics.status')} value={opsData.status} />
              <StatCard label={t('admin.metrics.database')} value={opsData.database} />
            </div>
          </div>
        )}

        {!loading && !error && activeTab === 'gdpr' && (
          <div className={styles.panel}>
            <h2>{t('admin.panel.gdpr')}</h2>
            <p>{t('admin.gdpr.exports')}: {gdprData.exports?.length || 0}</p>
            <p>{t('admin.gdpr.deletions')}: {gdprData.deletions?.length || 0}</p>
          </div>
        )}

        {!loading && !error && activeTab === 'revenue' && (
          <div className={styles.panel}>
            <h2>{t('admin.panel.revenue')}</h2>
            <div className={styles.grid}>
              <StatCard label={t('admin.metrics.mrr')} value={t('admin.metrics.money', { value: revenueData.mrr || 0 })} />
              <StatCard label={t('admin.metrics.status')} value={revenueData.status} />
            </div>
          </div>
        )}

        {!loading && !error && activeTab === 'economy' && (
          <div className={styles.panel}>
            <h2>{t('admin.panel.economy')}</h2>
            <div className={styles.grid}>
              <StatCard label={t('admin.metrics.kFactor')} value={economyData.k_factor?.toFixed(4)} />
              <StatCard label={t('admin.metrics.totalUsers')} value={economyData.total_users} />
              <StatCard label={t('admin.metrics.referrals')} value={economyData.successful_referrals} />
            </div>
            <ReferralClawback />
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value?: string | number | null }) {
  const { t } = useTranslation();
  return (
    <div className={styles.card}>
      <div className={styles.cardLabel}>{label}</div>
      <div className={styles.cardValue}>{value ?? t('admin.noValue')}</div>
    </div>
  );
}
