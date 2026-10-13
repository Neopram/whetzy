// Origen del alta (D-23 del dueño, 2026-10-12): mínimo y sin terceros. Se
// guarda el PRIMER contacto (los utm_* de la URL con la que llegó) y se envía
// una vez, en el onboarding; la clasificación la hace el servidor.

const KEY = 'whetzy_attribution';

export interface SignupAttribution {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  referred?: boolean;
}

/** Guarda los utm_* de `search` si es el primer contacto. Nunca lanza. */
export function captureAttribution(search: string): void {
  try {
    if (localStorage.getItem(KEY)) return;
    const params = new URLSearchParams(search);
    const picked: SignupAttribution = {};
    for (const k of ['utm_source', 'utm_medium', 'utm_campaign'] as const) {
      const v = params.get(k)?.trim().slice(0, 64);
      if (v) picked[k] = v;
    }
    if (Object.keys(picked).length > 0) localStorage.setItem(KEY, JSON.stringify(picked));
  } catch {
    /* modo privado o almacenamiento bloqueado: el alta cuenta como directa */
  }
}

/** Lo que se envía al servidor; `referred` si llegó por un enlace /r/<código>. */
export function readAttribution(): SignupAttribution {
  try {
    const stored = JSON.parse(localStorage.getItem(KEY) ?? '{}') as SignupAttribution;
    return { ...stored, referred: Boolean(localStorage.getItem('whetzy_ref')) };
  } catch {
    return {};
  }
}
