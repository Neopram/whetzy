import type { Domain } from '../../fixtures/readiness';
import { useSettings } from '../../i18n';
import { ProgressBar } from './ProgressBar';
import styles from './whetzy.module.css';
export interface DomainBarProps { domain: Domain }
export function DomainBar({ domain }: DomainBarProps) { const { t, pick } = useSettings(); return <div className={styles.domain}><div className={styles.domainTitle}><strong>{pick(domain)}</strong><span>{Math.round(domain.p_known_mean * 100)}%</span></div><ProgressBar value={domain.p_known_mean} label={pick(domain)}/><div className={styles.domainFoot}><span>{domain.weight_pct}% {t('weight')}</span><span>{domain.skills_assessed}/{domain.skills_total} {t('assessed')}</span></div></div>; }
