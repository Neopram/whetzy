import { useEffect, useState } from 'react';
import { Skeleton, SkeletonText } from './Skeleton';
import styles from './Loading.module.css';

/**
 * Estado de carga común (46.14, docs/PLAN_UI_AVANZADA.md §7.4): un esqueleto
 * con la forma de lo que viene en vez de un «Cargando…» suelto. El lector de
 * pantalla oye `label` al momento; el esqueleto espera 150 ms para no
 * parpadear cuando los datos llegan enseguida. Con movimiento reducido, el
 * brillo se apaga en `Skeleton.module.css`.
 */
export const LOADING_DELAY_MS = 150;

/** `line` dentro de una sección, donde no se sabe cuánto medirá lo que llega:
 *  ocupa lo mismo que el texto al que sustituye y no empuja nada al llegar (el
 *  esqueleto de tarjeta subía el CLS de Stats de 0,003 a 0,072, medido). Las
 *  formas grandes, solo cuando el esqueleto ocupa la pantalla entera. */
type Shape = 'line' | 'text' | 'list' | 'card';

export function Loading({ label, shape = 'text' }: { label: string; shape?: Shape }) {
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const id = window.setTimeout(() => setShown(true), LOADING_DELAY_MS);
    return () => window.clearTimeout(id);
  }, []);

  return (
    <div className={shape === 'line' ? styles.line : styles.loading} role="status" aria-busy="true" data-shape={shape}>
      <span className="visually-hidden">{label}</span>
      {shown && shape === 'line' && <span data-skeleton><Skeleton height="0.9em" width="40%" /></span>}
      {shown && shape === 'text' && <span data-skeleton><SkeletonText lines={3} /></span>}
      {shown && shape === 'list' && (
        <span className={styles.list} data-skeleton>
          {[0, 1, 2].map((i) => (
            <span key={i} className={styles.row}>
              <Skeleton width={36} height={36} radius={18} />
              <span className={styles.rowText}>
                <Skeleton height={14} width="60%" />
                <Skeleton height={12} width="35%" />
              </span>
            </span>
          ))}
        </span>
      )}
      {shown && shape === 'card' && (
        <span className={styles.card} data-skeleton>
          <Skeleton height={20} width="45%" />
          <SkeletonText lines={2} />
          <Skeleton height={40} radius={12} />
        </span>
      )}
    </div>
  );
}
