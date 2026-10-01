import { Link } from '@tanstack/react-router';
import styles from './whetzy.module.css';
export function Brand() { return <Link to="/hoy" className={styles.brand} aria-label="Whetzy"><span className={styles.brandMark}>W<span>.</span></span><span>Whetzy</span></Link>; }
