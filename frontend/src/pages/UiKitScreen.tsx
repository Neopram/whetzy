import { useState } from 'react';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorState } from '../components/common/ErrorState';
import { LoadingState } from '../components/common/LoadingState';
import { Modal } from '../components/common/Modal';
import { ProgressBar } from '../components/common/ProgressBar';
import { Sheet } from '../components/common/Sheet';
import { Skeleton, SkeletonText } from '../components/common/Skeleton';
import { TabsNav, type TabItem } from '../components/common/TabsNav';
import { showToast, Toast } from '../components/common/Toast';
import styles from './UiKitScreen.module.css';

/**
 * `/_ui` (34.3) — cada componente base de `components/common` en sus
 * variantes, para revisar el lenguaje visual de un vistazo sin tener que
 * navegar la app entera hasta encontrar dónde se usa cada uno. Solo en dev:
 * `import.meta.env.DEV` es una constante de compilación, así que Vite/Rollup
 * quita esta rama entera (y con ella el bundle de esta página) del build de
 * producción — no es una comprobación en tiempo de ejecución que alguien
 * pueda saltarse cambiando la URL en producción.
 */

const BUTTON_VARIANTS = ['primary', 'secondary', 'ghost', 'danger', 'success', 'text'] as const;
const BUTTON_SIZES = ['xs', 'sm', 'md', 'lg', 'xl'] as const;
const BADGE_VARIANTS = ['brand', 'green', 'gold', 'orange', 'muted'] as const;

const TABS: TabItem<'a' | 'b' | 'c'>[] = [
  { id: 'a', label: 'Con icono', icon: '🎯' },
  { id: 'b', label: 'Con insignia', badge: 3 },
  { id: 'c', label: 'Sin nada' },
];

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>{title}</h2>
      <div className={styles.sectionBody}>{children}</div>
    </section>
  );
}

export function UiKitScreen() {
  const [modalOpen, setModalOpen] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [tab, setTab] = useState<'a' | 'b' | 'c'>('a');

  return (
    <div className={styles.page}>
      <Toast />
      <h1 className={styles.pageTitle}>/_ui — componentes base (34.3)</h1>
      <p className={styles.pageSub}>Solo en dev (import.meta.env.DEV) — no entra en el build de producción.</p>

      <Section title="Button">
        {BUTTON_VARIANTS.map((v) => (
          <div key={v} className={styles.row}>
            <span className={styles.rowLabel}>{v}</span>
            {BUTTON_SIZES.map((s) => (
              <Button key={s} variant={v} size={s}>{s}</Button>
            ))}
            <Button variant={v} loading>loading</Button>
            <Button variant={v} disabled>disabled</Button>
          </div>
        ))}
      </Section>

      <Section title="Badge">
        <div className={styles.row}>
          {BADGE_VARIANTS.map((v) => (
            <Badge key={v} variant={v}>{v}</Badge>
          ))}
        </div>
        <div className={styles.row}>
          {BADGE_VARIANTS.map((v) => (
            <Badge key={v} variant={v} size="sm">{v} sm</Badge>
          ))}
        </div>
      </Section>

      <Section title="Card">
        <div className={styles.row}>
          <Card><p>Card simple, sin onClick.</p></Card>
          <Card onClick={() => showToast('Card pulsada')}><p>Card con onClick (pulsable).</p></Card>
        </div>
      </Section>

      <Section title="Modal / Sheet">
        <div className={styles.row}>
          <Button onClick={() => setModalOpen(true)}>Abrir Modal</Button>
          <Button onClick={() => setSheetOpen(true)}>Abrir Sheet</Button>
        </div>
        <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Título del modal" footer={<Button onClick={() => setModalOpen(false)}>Cerrar</Button>}>
          <p>Contenido del modal.</p>
        </Modal>
        <Sheet open={sheetOpen} onClose={() => setSheetOpen(false)} title="Título de la sheet">
          <p>Contenido de la sheet.</p>
        </Sheet>
      </Section>

      <Section title="Toast">
        <div className={styles.row}>
          <Button variant="success" onClick={() => showToast('Todo bien', 'success')}>success</Button>
          <Button variant="danger" onClick={() => showToast('Algo falló', 'error')}>error</Button>
          <Button variant="secondary" onClick={() => showToast('Aviso', 'info')}>info</Button>
        </div>
      </Section>

      <Section title="ProgressBar">
        <div className={styles.stack}>
          <ProgressBar value={30} max={100} label="30 de 100" showLabel />
          <ProgressBar value={80} max={100} label="80 de 100, color éxito" color="var(--le-green)" showLabel />
          <ProgressBar value={5} max={100} label="5 de 100, delgada" height={6} />
        </div>
      </Section>

      <Section title="Skeleton">
        <div className={styles.row}>
          <Skeleton width={120} height={16} />
          <Skeleton width={60} height={60} radius={30} />
        </div>
        <SkeletonText lines={3} />
      </Section>

      <Section title="EmptyState">
        <EmptyState icon="📭" title="Nada por aquí" description="Descripción opcional del estado vacío." actionLabel="Acción" onAction={() => showToast('Acción de EmptyState')} />
      </Section>

      <Section title="LoadingState">
        {/* width: 100% en .container (LoadingState.module.css) — en fila
            (flex-wrap) cada una ocupa su propia línea entera; en columna se
            ve tal cual se usa en la app (nunca dos a la vez, una detrás de
            otra mientras carga algo). */}
        <div className={styles.stack}>
          <LoadingState size="sm" message="Cargando (sm)…" />
          <LoadingState size="md" message="Cargando (md)…" />
          <LoadingState size="lg" message="Cargando (lg)…" />
        </div>
      </Section>

      <Section title="ErrorState">
        <ErrorState message="Algo salió mal de verdad." onRetry={() => showToast('Reintentando…')} />
      </Section>

      <Section title="TabsNav">
        <TabsNav tabs={TABS} activeTab={tab} onChange={setTab} />
        <p className={styles.tabResult}>Pestaña activa: {tab}</p>
      </Section>
    </div>
  );
}

export default UiKitScreen;
