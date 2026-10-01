import { Flame } from 'lucide-react';
import { dashboard } from '../../fixtures/dashboard';
import { useSettings } from '../../i18n';
import { Brand } from './Brand';
import styles from './whetzy.module.css';
export function TopBar() { const { t } = useSettings(); return <header className={styles.topbar}><Brand/><div className={styles.topStreak} aria-label={`${dashboard.current_streak} ${t('streakDays')}`}><Flame size={16}/><strong>{dashboard.current_streak}</strong><span>{t('streakDays')}</span></div></header>; }
