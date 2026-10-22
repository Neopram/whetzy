/**
 * 40.2: contrato de los tres widgets del piloto. Para cada uno: se pinta desde
 * `params`, se manipula como lo haría el alumno (clic, casilla, escribir), se
 * serializa y se corrige con el checker del cliente. Los estados y veredictos
 * salen de `backend/tests/fixtures/widget_pilot_cases.json`, el mismo fichero
 * que lee `test_widget_pilot.py`: cliente y servidor dan el mismo veredicto
 * sobre el mismo estado.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { check } from '../widgets/checkers';
import { loadWidget, WIDGETS } from '../widgets/registry';

interface Caso { state: unknown; expected: boolean; why: string }
interface Item { widget: string; params: Record<string, unknown>; checker: string; target: unknown; cases: Caso[] }
const ITEMS = (JSON.parse(
  readFileSync(resolve(__dirname, '../../../backend/tests/fixtures/widget_pilot_cases.json'), 'utf-8'),
) as { items: Item[] }).items;

/** Lo que el alumno hace en pantalla para dejar el widget en `state`. */
const DRIVE: Record<string, (state: never) => void> = {
  binarySearch: (probes: number[]) => {
    for (const v of probes) fireEvent.click(screen.getByRole('button', { name: new RegExp(`valor ${v},`) }));
  },
  cidr: (s: { network: string; broadcast: string }) => {
    fireEvent.change(screen.getByLabelText('Dirección de red'), { target: { value: s.network } });
    fireEvent.change(screen.getByLabelText('Dirección de broadcast'), { target: { value: s.broadcast } });
  },
  sqlJoin: (pairs: number[][]) => {
    for (const [l, r] of pairs) {
      const box = screen.getAllByRole('checkbox').find((c) => {
        const text = c.closest('label')!.textContent!;
        return text.startsWith(`users(id=${l},`) && text.includes(`con orders(id=${r},`);
      });
      fireEvent.click(box!);
    }
  },
};

async function mount(item: Item, lang: 'es' | 'en' = 'es') {
  const widget = (await loadWidget(item.widget))!;
  const onChange = vi.fn();
  const Widget = widget.render;
  const view = render(<Widget params={item.params} lang={lang} disabled={false} onChange={onChange} />);
  const last = () => onChange.mock.calls.at(-1)?.[0];
  return { widget, onChange, last, view };
}

beforeEach(async () => { await i18n.changeLanguage('es'); });
afterEach(cleanup);

describe('widgets del piloto (40.2)', () => {
  it('el registro tiene exactamente los tres widgets del piloto, cargados perezosos', () => {
    expect(Object.keys(WIDGETS).sort()).toEqual(ITEMS.map((i) => i.widget).sort());
  });

  describe.each(ITEMS)('$widget', (item) => {
    it.each(item.cases.map((c) => [c.why, c] as const))('%s', async (_why, caso) => {
      const { widget, last } = await mount(item);
      expect(last()).toBeUndefined(); // nada que enviar mientras no se toque nada
      DRIVE[item.widget](caso.state as never);
      const serialized = widget.serialize(last());
      // Lo que se envía es lo que el caso describe (en un JOIN, el orden de las filas no cuenta).
      expect(check(item.checker === 'unordered' ? 'unordered' : 'exact', serialized, caso.state)).toBe(true);
      expect(check(item.checker, serialized, item.target)).toBe(caso.expected);
    });

    it('tiene alternativa textual y se opera con controles nativos', async () => {
      const { view } = await mount(item);
      const text = view.container.textContent ?? '';
      expect(text.length).toBeGreaterThan(40);
      for (const el of view.container.querySelectorAll('button, input')) {
        expect(el.getAttribute('tabindex')).not.toBe('-1');
      }
      expect(view.container.querySelector('button, input')).not.toBeNull();
    });

    it('en inglés usa las cadenas inglesas', async () => {
      const { view } = await mount(item, 'en');
      expect(view.container.textContent).not.toMatch(/Dirección|Busca|Marca las|Sondeos|Aún no/);
    });

    it('con params que no son los suyos avisa en vez de romper', async () => {
      const widget = (await loadWidget(item.widget))!;
      const Widget = widget.render;
      render(<Widget params={{}} lang="es" disabled={false} onChange={() => {}} />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('búsqueda binaria: descarta lo que ya no puede contener el objetivo y se puede empezar de nuevo', async () => {
    const item = ITEMS[0];
    const { last } = await mount(item);
    DRIVE.binarySearch([7] as never);
    expect(screen.getByRole('button', { name: /valor 9,/ })).toBeDisabled();
    expect(screen.getByRole('button', { name: /valor 3,/ })).toBeEnabled();
    expect(screen.getByRole('status')).toHaveTextContent('Quedan las posiciones 1 a 3');
    fireEvent.click(screen.getByRole('button', { name: 'Empezar de nuevo' }));
    expect(last()).toBeNull();
    expect(screen.getByRole('button', { name: /valor 9,/ })).toBeEnabled();
  });

  it('CIDR: serializa recortado, porque el servidor no recorta', async () => {
    const item = ITEMS[1];
    const { widget, last } = await mount(item);
    DRIVE.cidr({ network: ' 192.168.10.64 ', broadcast: '192.168.10.127\n' } as never);
    expect(check('exact', widget.serialize(last()), item.target)).toBe(true);
    fireEvent.change(screen.getByLabelText('Dirección de broadcast'), { target: { value: '  ' } });
    expect(last()).toBeNull();
  });

  it('JOIN: desmarcar la última fila deja el estado en null', async () => {
    const { last } = await mount(ITEMS[2]);
    DRIVE.sqlJoin([[1, 10]] as never);
    expect(last()).toEqual([[1, 10]]);
    DRIVE.sqlJoin([[1, 10]] as never); // segundo clic: desmarca
    expect(last()).toBeNull();
  });

  it('ya respondida, los controles quedan quietos', async () => {
    const widget = (await loadWidget('cidr'))!;
    const Widget = widget.render;
    render(<Widget params={ITEMS[1].params} lang="es" disabled onChange={() => {}} />);
    for (const input of screen.getAllByRole('textbox')) expect(input).toBeDisabled();
  });
});
