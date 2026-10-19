/**
 * Número que cuenta desde 0 hasta su valor (46.7b, docs/PLAN_UI_AVANZADA.md
 * §6.2). Lo que se ve es decorativo (`aria-hidden`); el lector de pantalla
 * lee siempre el valor final, nunca los intermedios. `idle`: 0, esperando
 * (p. ej. detrás de una ceremonia); `run`: cuenta; `done`: el valor final.
 */
import { useEffect, useState } from 'react';
import { animate } from 'framer-motion';

export function CountUp({
  value,
  format = String,
  state,
  durationMs,
  testId,
}: {
  value: number;
  format?: (n: number) => string;
  state: 'idle' | 'run' | 'done';
  durationMs: number;
  testId?: string;
}) {
  const [shown, setShown] = useState(state === 'done' ? value : 0);

  useEffect(() => {
    if (state !== 'run') {
      setShown(state === 'done' ? value : 0);
      return;
    }
    const controls = animate(0, value, {
      duration: durationMs / 1000,
      ease: 'easeOut',
      onUpdate: (v) => setShown(Math.round(v)),
    });
    return () => controls.stop();
  }, [value, state, durationMs]);

  return (
    <span data-testid={testId}>
      <span aria-hidden="true">{format(shown)}</span>
      <span className="visually-hidden">{format(value)}</span>
    </span>
  );
}
