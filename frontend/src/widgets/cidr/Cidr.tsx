/**
 * Subnetting CIDR (40.2). Dada una dirección con prefijo (`192.168.10.77/26`),
 * el alumno escribe la dirección de red y la de broadcast. El widget enseña la
 * dirección en binario con los bits de red resaltados. Estado y envío:
 * `{network, broadcast}` recortados (checker `exact`; el servidor no recorta).
 *
 * Teclado: dos campos de texto con su etiqueta. Alternativa textual: la
 * máscara y el número de bits de red se dicen en una frase, y el binario
 * resaltado es decoración (`aria-hidden`) con su equivalente oculto a la vista.
 */
import { useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { WidgetDefinition, WidgetRenderProps } from '../registry';
import common from '../widget.module.css';
import styles from './Cidr.module.css';

interface CidrState { network: string; broadcast: string }

/** `a.b.c.d/p` → los cuatro octetos y el prefijo, o `null` si no es una dirección válida. */
export function parseCidr(text: unknown): { octets: number[]; prefix: number } | null {
  const m = typeof text === 'string' ? /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\/(\d{1,2})$/.exec(text) : null;
  if (!m) return null;
  const octets = m.slice(1, 5).map(Number);
  const prefix = Number(m[5]);
  return octets.every((o) => o <= 255) && prefix >= 1 && prefix <= 30 ? { octets, prefix } : null;
}

const bits = (octet: number) => octet.toString(2).padStart(8, '0');

function Cidr({ params, lang, disabled, onChange }: WidgetRenderProps<CidrState>) {
  const { t } = useTranslation('producto');
  const id = useId();
  const [value, setValue] = useState<CidrState>({ network: '', broadcast: '' });
  const parsed = parseCidr(params.cidr);
  if (!parsed) return <p role="alert">{t('interactive.unavailable')}</p>;

  const tr = (key: string, o?: Record<string, unknown>) => t(`widgets.cidr.${key}`, { lng: lang, ...o });
  const { octets, prefix } = parsed;
  const mask = [0, 1, 2, 3].map((i) => Math.max(0, Math.min(8, prefix - 8 * i))).map((n) => 256 - 2 ** (8 - n));
  const set = (key: keyof CidrState, text: string) => {
    const next = { ...value, [key]: text };
    setValue(next);
    onChange(next.network.trim() && next.broadcast.trim() ? next : null);
  };

  return (
    <div className={common.area}>
      <p className={common.hint}>{tr('intro', { cidr: params.cidr, mask: mask.join('.'), prefix, hosts: 32 - prefix })}</p>
      <p className={styles.bits} aria-hidden="true">
        {octets.map((o, i) => (
          <span key={i}>
            {[...bits(o)].map((b, j) => (
              <span key={j} className={8 * i + j < prefix ? styles.net : undefined}>{b}</span>
            ))}
          </span>
        ))}
      </p>
      <p className={common.visuallyHidden}>
        {tr('binary', { bin: octets.map(bits).join('.'), prefix })}
      </p>
      <div className={styles.fields}>
        {(['network', 'broadcast'] as const).map((key) => (
          <label key={key} className={common.field} htmlFor={`${id}-${key}`}>
            {tr(key)}
            <input
              id={`${id}-${key}`}
              className={common.input}
              type="text"
              inputMode="decimal"
              autoComplete="off"
              spellCheck={false}
              placeholder="0.0.0.0"
              value={value[key]}
              disabled={disabled}
              onChange={(e) => set(key, e.target.value)}
            />
          </label>
        ))}
      </div>
    </div>
  );
}

const definition: WidgetDefinition<CidrState> = {
  render: Cidr,
  serialize: (s) => ({ network: s.network.trim(), broadcast: s.broadcast.trim() }),
};
export default definition as WidgetDefinition;
