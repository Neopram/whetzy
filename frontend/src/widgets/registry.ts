/**
 * Registro de widgets de las preguntas `interactive` (40.1; los primeros llegan
 * con el piloto 40.2: búsqueda binaria, CIDR y JOIN).
 *
 * Contrato común (docs/PLAN_EXPERIENCIA.md §1): `render` pinta el widget a
 * partir de `params`, operable solo con teclado y con alternativa textual;
 * `serialize` convierte su estado en el JSON que viaja como `widget_state`; la
 * corrección (`check`) es la de `widgets/checkers.ts`, la misma que el servidor.
 *
 * Cada widget se carga perezoso, en su propio chunk. `scripts/check_question_bank.py`
 * lee las claves de `WIDGETS`: una pregunta que nombra un widget que no está
 * aquí no entra en el banco, porque el alumno no podría contestarla.
 */
import type { ComponentType } from 'react';
import type { Json } from './checkers';

export interface WidgetRenderProps<S> {
  params: Record<string, unknown>;
  lang: 'es' | 'en';
  /** Ya respondida: el widget se queda quieto con el estado que se envió. */
  disabled: boolean;
  /** Estado actual; `null` mientras no haya nada que enviar. */
  onChange: (state: S | null) => void;
}

export interface WidgetDefinition<S = unknown> {
  render: ComponentType<WidgetRenderProps<S>>;
  serialize: (state: S) => Json;
}

type WidgetLoader = () => Promise<{ default: WidgetDefinition }>;

export const WIDGETS: Record<string, WidgetLoader> = {};

export async function loadWidget(name: string): Promise<WidgetDefinition | null> {
  const loader = Object.hasOwn(WIDGETS, name) ? WIDGETS[name] : undefined;
  if (!loader) return null;
  return (await loader()).default;
}
