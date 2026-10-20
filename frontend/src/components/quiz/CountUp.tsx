/**
 * Número que cuenta desde 0 hasta su valor (46.7b, docs/PLAN_UI_AVANZADA.md
 * §6.2). Lo que se ve es decorativo (`aria-hidden`); el lector de pantalla
 * lee siempre el valor final, nunca los intermedios. `idle`: 0, esperando
 * (p. ej. detrás de una ceremonia); `run`: cuenta; `done`: el valor final.
 * `from` (46.12): desde dónde cuenta; Hoy cuenta desde la última foto, no desde 0.
 */
import { useEffect, useState } from 'react';
import { animate } from 'framer-motion';

export function CountUp({
  value,
  from = 0,
  format = String,
  state,
  durationMs,
  testId,
}: {
  value: number;
  from?: number;
  format?: (n: number) => string;
  state: 'idle' | 'run' | 'done';
  durationMs: number;
  testId?: string;
}) {
  const [shown, setShown] = useState(state === 'done' ? value : from);

  useEffect(() => {
    if (state !== 'run') {
      setShown(state === 'done' ? value : from);
      return;
    }
    const controls = animate(from, value, {
      duration: durationMs / 1000,
      ease: 'easeOut',
      onUpdate: (v) => setShown(Math.round(v)),
    });
    return () => controls.stop();
  }, [value, from, state, durationMs]);

  return (
    <span data-testid={testId}>
      <span aria-hidden="true">{format(shown)}</span>
      <span className="visually-hidden">{format(value)}</span>
    </span>
  );
}
