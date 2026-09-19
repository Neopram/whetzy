import { useEffect, useState } from 'react';
import styles from './AdminScreen.module.css';

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
  const [activeTab, setActiveTab] = useState<Tab>('metrics');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [metricsData, setMetricsData] = useState<Metrics>({});
  const [securityData, setSecurityData] = useState<any>({});
  const [contentData, setContentData] = useState<any>({});
  const [opsData, setOpsData] = useState<any>({});
  const [gdprData, setGDPRData] = useState<any>({});
  const [revenueData, setRevenueData] = useState<any>({});
  const [economyData, setEconomyData] = useState<any>({});

  const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiBase}/admin/metrics/users?range_days=7`);
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      setMetricsData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error');
    } finally {
      setLoading(false);
    }
  };

  const fetchSecurity = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiBase}/admin/security/auth-events?limit=10`);
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      setSecurityData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error');
    } finally {
      setLoading(false);
    }
  };

  const fetchContent = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiBase}/admin/content/gaps?language=es`);
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      setContentData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error');
    } finally {
      setLoading(false);
    }
  };

  const fetchOps = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiBase}/admin/ops/health`);
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      setOpsData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error');
    } finally {
      setLoading(false);
    }
  };

  const fetchGDPR = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiBase}/admin/gdpr/exports?status=pending`);
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      setGDPRData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error');
    } finally {
      setLoading(false);
    }
  };

  const fetchRevenue = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiBase}/admin/revenue/mrr?month=2026-09`);
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      setRevenueData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error');
    } finally {
      setLoading(false);
    }
  };

  const fetchEconomy = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiBase}/admin/economy/credits?limit=10`);
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      setEconomyData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error');
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
    { id: 'metrics', label: 'Metrics' },
    { id: 'security', label: 'Security' },
    { id: 'content', label: 'Content' },
    { id: 'ops', label: 'Ops' },
    { id: 'gdpr', label: 'GDPR' },
    { id: 'revenue', label: 'Revenue' },
    { id: 'economy', label: 'Economy' },
  ];

  return (
    <div className={styles.admin}>
      <div className={styles.header}>
        <h1>Admin Panel</h1>
        <p className={styles.subtitle}>Platform analytics & operations</p>
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
        {loading && <div className={styles.loading}>Loading...</div>}
        {error && <div className={styles.error}>{error}</div>}

        {!loading && !error && activeTab === 'metrics' && (
          <div className={styles.panel}>
            <h2>Metrics</h2>
            <div className={styles.grid}>
              <StatCard label="DAU" value={metricsData.dau} />
              <StatCard label="WAU" value={metricsData.wau} />
              <StatCard label="MAU" value={metricsData.mau} />
              <StatCard label="Total Users" value={metricsData.total_users} />
              <StatCard label="Retention D1" value={`${metricsData.retention_d1}%`} />
              <StatCard label="Retention D7" value={`${metricsData.retention_d7}%`} />
            </div>
          </div>
        )}

        {!loading && !error && activeTab === 'security' && (
          <div className={styles.panel}>
            <h2>Security</h2>
            <p>Auth events: {securityData.events?.length || 0}</p>
            <p>Lockouts: {securityData.lockouts?.length || 0}</p>
          </div>
        )}

        {!loading && !error && activeTab === 'content' && (
          <div className={styles.panel}>
            <h2>Content</h2>
            <div className={styles.grid}>
              <StatCard label="Total Skills" value={contentData.total_skills} />
              <StatCard label="ES Count" value={contentData.es_count} />
              <StatCard label="EN Count" value={contentData.en_count} />
              <StatCard label="Parity %" value={contentData.parity_percent} />
            </div>
          </div>
        )}

        {!loading && !error && activeTab === 'ops' && (
          <div className={styles.panel}>
            <h2>Operations</h2>
            <div className={styles.grid}>
              <StatCard label="Status" value={opsData.status} />
              <StatCard label="Database" value={opsData.database} />
            </div>
          </div>
        )}

        {!loading && !error && activeTab === 'gdpr' && (
          <div className={styles.panel}>
            <h2>GDPR Requests</h2>
            <p>Exports: {gdprData.exports?.length || 0}</p>
            <p>Deletions: {gdprData.deletions?.length || 0}</p>
          </div>
        )}

        {!loading && !error && activeTab === 'revenue' && (
          <div className={styles.panel}>
            <h2>Revenue</h2>
            <div className={styles.grid}>
              <StatCard label="MRR" value={`$${revenueData.mrr || 0}`} />
              <StatCard label="Status" value={revenueData.status} />
            </div>
          </div>
        )}

        {!loading && !error && activeTab === 'economy' && (
          <div className={styles.panel}>
            <h2>Economy</h2>
            <div className={styles.grid}>
              <StatCard label="K-Factor" value={economyData.k_factor?.toFixed(4)} />
              <StatCard label="Total Users" value={economyData.total_users} />
              <StatCard label="Referrals" value={economyData.successful_referrals} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className={styles.card}>
      <div className={styles.cardLabel}>{label}</div>
      <div className={styles.cardValue}>{value ?? '-'}</div>
    </div>
  );
}
