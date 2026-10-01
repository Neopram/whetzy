import { Link } from '@tanstack/react-router';
import { useSettings } from '../../i18n';
import { Brand } from './Brand';
import { navItems } from './nav';
import styles from './whetzy.module.css';
export function SideNav() { const { t } = useSettings(); return <aside className={styles.sidebar}><Brand/><nav aria-label={t('navigation')}>{navItems.map(({ to, key, icon: Icon }) => <Link key={to} to={to} className={styles.sideLink} activeProps={{ className: styles.sideActive }}><Icon size={19} strokeWidth={1.8}/><span>{t(key)}</span></Link>)}</nav><Link to="/design" className={styles.designLink}>{t('design')}</Link></aside>; }
