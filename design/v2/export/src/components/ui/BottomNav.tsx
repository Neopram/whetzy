import { Link } from '@tanstack/react-router';
import { useSettings } from '../../i18n';
import { navItems } from './nav';
import styles from './whetzy.module.css';
export function BottomNav() { const { t } = useSettings(); return <nav className={styles.bottomNav} aria-label={t('navigation')}>{navItems.map(({ to, key, icon: Icon }) => <Link key={to} to={to} className={styles.navLink} activeProps={{ className: styles.navActive }}><Icon size={20} strokeWidth={1.8}/><span>{t(key)}</span></Link>)}</nav>; }
