# 37.24 — banco reservado de simulacro: estado al cierre del 2026-10-10

**Estado: PARCIAL. 146 de 1.040 integradas. `MOCK_EXAM_RESERVED_POOL_ENABLED` sigue en `False`
y debe seguir así**: con este banco, ninguna certificación llega a 2 × su examen, y encender el flag
dejaría simulacros cortos o vacíos.

La tanda se paró a propósito: tres reanudaciones seguidas chocaron con el límite de uso de la cuenta
(el dueño iba por el 61 % del límite semanal). Aquí queda guardado todo lo producido, para retomarlo
sin volver a pagar lo ya hecho.

## Qué entró al banco

`content/questions/<track>/reservadas_<módulo>.json`, `"pool": "simulacro"`, 146 preguntas.
Solo entra lo que cumple **las dos** condiciones:

1. Revisor adversario Sonnet **sin ningún defecto**, o corrector Sonnet aplicado (ADR-59).
2. La puerta de `integ3724.py`: slot, `fragment_id` y `correct_index` iguales a los asignados en
   `chunks.json`, cita literal dentro del fragmento, 4 + 4 opciones, ningún campo publicado copia
   más de 8 palabras seguidas de la fuente, y la correcta no es la opción más larga.

De 155 preguntas limpias o corregidas, la puerta rechazó 7 (4 por copia de más de 8 palabras,
1 por índice cambiado, 2 porque la correcta era la más larga, quitadas con `--skip-longest`).
`post3724.py` quitó otras 2 que rechazan las guardas de `tests/content`: `q110205_r010`
(`voz_de_asistente`, falso positivo con «como modelo de lenguaje») y `q110202_r001` (final de
relleno en una opción EN). Además ordena cada fichero por hash del id, porque el orden por slot
heredaba la rotación 0-1-2-3 de la clave de respuestas.

## Estado por certificación

| Cert | Meta | Integradas | Escritas | Revisada limpia | Corregida | Solo defectos menores, sin corregir | Defecto grave, sin corregir | Sin revisar | Descartada | Sin escribir |
|---|---|---|---|---|---|---|---|---|---|---|
| AIF-C01 | 130 | 97 | 130 | 13 | 89 | 11 | 13 | 0 | 4 | 0 |
| CC | 200 | 0 | 200 | 0 | 0 | 0 | 0 | 200 | 0 | 0 |
| CLF-C02 | 130 | 42 | 130 | 36 | 10 | 46 | 37 | 0 | 1 | 0 |
| MLA-C01 | 130 | 3 | 130 | 3 | 0 | 99 | 28 | 0 | 0 | 0 |
| PCAP-31-03 | 80 | 0 | 80 | 0 | 0 | 2 | 31 | 47 | 0 | 0 |
| PCEP-30-02 | 60 | 2 | 60 | 2 | 0 | 26 | 32 | 0 | 0 | 0 |
| SAA-C03 | 130 | 2 | 130 | 2 | 0 | 81 | 47 | 0 | 0 | 0 |
| SY0-701 | 180 | 0 | 126 | 0 | 0 | 0 | 0 | 126 | 0 | 54 |
| **Total** | **1.040** | **146** | **986** | 56 | 99 | 265 | 188 | 373 | 5 | 54 |

«Escritas» cuenta por certificación (AIF-C01 integra 97 de 130 escritas: 13 + 89 pasaron el
revisor o el corrector y la puerta tiró 5).

## Qué hay en esta carpeta

| Fichero | Qué es |
|---|---|
| `wip/G1.json`, `wip/G2.json`, `wip/G3.json` | Las 986 escritas con su revisión y su corrección, en el formato `{"result": [{sk, q, review, corrected}]}` que lee `integ3724.py`. **Sin el campo `fragment`** y con todo tramo de ≥ 9 palabras de cualquier fragmento de fuente sustituido por `[cita de la fuente omitida]` (ADR-46: el corpus no entra al repo). Comprobado: 0 cadenas con un 9-grama de fuente. |
| `chunks.json` | Los 238 bloques: skill, certificación y por slot `fragment_id` + `correct_index` asignado. Sin texto de fuente. |
| `items_g1.json` … `items_g3.json` | Los ids de bloque de cada grupo (args del Workflow como `{"items": [...]}`; un array suelto rompe `args.items.map`). |
| `wf37_24.js` | El Workflow (escritor → revisor por pregunta → corrector). |
| `integ3724.py` | La puerta e integración; `--write` escribe, `--skip-longest` deja fuera en vez de abortar. |
| `post3724.py` | Exclusiones por guardas de `tests/content` y orden por hash. |
| `extract_journals.py`, `journal2wf.py` | Sacan los resultados del `journal.jsonl` de un run de Workflow. |
| `frags.py`, `alloc.py`, `plan.py` | Construyen `frag/<id>.txt` desde las fuentes y asignan slots. |

Los scripts traen la ruta del scratchpad de la sesión del 2026-10-10 (`RES = ...`); en otra
sesión hay que cambiarla. `frag/` **no** está en el repo: se regenera con `frags.py`.

## Por hacer (en este orden, de lo más barato a lo más caro)

1. **265 con solo defectos menores**: pasar el corrector Sonnet (1 agente por pregunta; sin
   reescribir ni re-revisar). Es lo que más rinde: 81 de SAA-C03, 99 de MLA-C01, 46 de CLF-C02.
2. **188 con defecto grave**: corrector Sonnet; si el corrector descarta, la pregunta se reescribe
   en su slot.
3. **373 sin revisar** (CC 200, SY0-701 126, PCAP 47): revisor y, donde haga falta, corrector.
4. **54 de SY0-701 sin escribir**: bloques `sk420102-b174` en adelante que nunca terminaron.
5. **Reintegrar**: hay que recuperar el campo `fragment` (la puerta comprueba la cita literal), y
   para eso hay que regenerar `frag/` y pedir la cita al corrector o al escritor. Después:
   `integ3724.py ... --skip-longest --write` (aborta si ya existe el fichero: borra los
   `reservadas_*.json` y reintegra todo de una vez), `post3724.py`, `pytest tests/content`,
   `check_question_bank.py`, `check_docs.py` (y actualizar las cifras que pida).
6. Encender `MOCK_EXAM_RESERVED_POOL_ENABLED` solo cuando cada certificación llegue a
   2 × `exam_question_count` (es un cambio de producción: lo hace el dueño, ADR-45).

**Coste estimado de lo que falta**: unos 880 agentes Sonnet (265 + 188 + 373 + 54 escritores y sus
revisiones). Una reanudación duró ~88 min antes de chocar con el límite. Recomendación: un grupo cada
vez y empezar por el punto 1.

## 2026-10-13: primera reanudación (corrector + re-revisión)

`wf37_24_corregir.js`: un corrector Sonnet por pregunta con defectos y, encima de su versión, un
revisor adversario Sonnet nuevo. Entra al banco solo si la re-revisión deja como mucho defectos
`minor` y pasa la puerta de `integ3724.py`.

- Piloto de 10 de AIF-C01 (9 de ellas con defecto grave de partida): 7 limpias o menores, 1 grave,
  2 descartadas. Umbral de parada (> 3 graves de 10) no alcanzado.
- Bloque 1 (14 AIF-C01 + 83 CLF-C02): 67 limpias o menores, 25 graves, 5 descartadas.
- Reintegración completa: **219 reservadas** (AIF-C01 116/130, CLF-C02 96/130, MLA-C01 3,
  PCEP-30-02 2, SAA-C03 2). `post3724.py` quita las mismas 2 de antes (los ids son estables por
  skill y slot; comprobado contra las guardas de `tests/content`).
- Las graves que quedan van a una segunda ronda junto con MLA-C01.

El flag sigue apagado: ninguna certificación llega aún a 2 × su examen.
