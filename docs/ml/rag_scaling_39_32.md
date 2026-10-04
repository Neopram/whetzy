# 39.32 — `test_rag_self_retrieval` de ~28 min a ~3 min

Reproducible: `cd backend && python scripts/rag_retrieve_scaling.py` (índice vs
tiempo, corpus real) y `python -m pytest tests/integration/test_rag_self_retrieval.py
-m slow -v -s` (el test en sí). Ambos sobre el corpus real cargado por
`content_loader.load_content()`: **10949 preguntas + 1044 términos de glosario =
11993 documentos** (medido 2026-10-02; `stats["skipped"] == 0`).

## Causa raíz

`RAGIndex.retrieve()` llamaba a `BM25Okapi.get_scores(tokens)`, que puntúa
**todo** el corpus en cada llamada — O(N). El test de autorecuperación llama a
`retrieve()` una vez por cada pregunta del banco, en los dos idiomas: O(N)
llamadas × O(N) cada una = **O(N²)** en el tamaño del corpus. El banco creció
de las ~1253 preguntas de 11.1 a 10949 hoy (≈8.7×); en O(N²) eso es ≈76× más
trabajo, consistente con pasar de segundos a ~28 min.

## Por qué el índice invertido solo no basta

La hipótesis inicial — construir un índice de postings (token → documentos) y
usar `BM25Okapi.get_batch_scores()` (ya en `rank-bm25==0.2.2`, misma fórmula
que `get_scores()` restringida a un subconjunto) en vez de puntuar todo el
corpus — es correcta y se implementó (`RAGIndex._token_to_docs`,
`RAGIndex.retrieve()`), pero el corpus real **no filtra palabras vacías**:

```
$ python - <<'EOF'
# token: % de los 10949 documentos que lo contienen
de    82.2%   the   80.1%   is    76.0%   a     71.8%
es    69.1%   el    68.6%   en    63.8%   la    63.4%
y     59.8%   and   59.6%   what  59.4%   que   55.3%
EOF
```

Toda pregunta contiene varias de estas palabras («¿Qué es...?» / «What
is...?»), así que la unión de sus listas de postings cubre en media el **95%**
del corpus (medido sobre 200 queries reales) — el índice invertido apenas
reduce el conjunto de candidatos. Filtrar por idf (excluir los ~61 tokens que
caen en el suelo de epsilon-smoothing de `BM25Okapi`) solo baja esa fracción al
44% de media — un ~2× más, no el salto necesario.

**Verificación de que el fix del motor es exacto** (no una aproximación): 500
queries sintéticas con vocabulario aleatorio + 400 queries reales del corpus,
comparando `retrieve()` antiguo vs nuevo documento a documento →
**0 discrepancias** en ambos casos. El fix de `rag.py` es un cambio de
algoritmo, no de resultado, y beneficia también la latencia de producción
(`tutor.py` llama a `retrieve()` en cada explicación del tutor IA).

## La palanca que sí resuelve el test: muestra fija

El propio criterio de 39.32 autoriza dos vías — «muestra fija o índice
invertido en el test» — y aquí hacen falta las dos: el índice invertido en el
motor (hecho, sin pérdida) más una muestra fija y reproducible en el test
(`_SAMPLE_SIZE = 1500`, `_SAMPLE_SEED = 20261002`, `random.Random(seed).sample(...)`),
en vez de iterar las 10949 preguntas.

Con n=1500 por idioma, el intervalo de Wilson al 95% alrededor de un listón del
95% tiene un semiancho de ~1,1 puntos — bastante ajustado para detectar una
regresión real (p. ej. una caída al 90%) sin fijar un recuento exacto que la
redacción de contenido rompería en cada sesión.

## Medidas reales (2026-10-02, este contenedor, 4 vCPU)

| Qué | Antes | Después |
|---|---|---|
| `test_index_memory_bounded_and_hits_self_retrieval_bar` (el test del ticket) | no se completó una corrida sin modificar en un tiempo práctico: a los ~10 min seguía corriendo y se interrumpió; extrapolado desde el escalado controlado de abajo, ≈20–28 min | **187,94 s (3 min 8 s)**, `2 passed` (incluye el test de "sin vocabulario compartido" del mismo fichero) |
| Autorecuperación ES (muestra de 1500) | — | 95,47 % (1432/1500) |
| Autorecuperación EN (muestra de 1500) | — | 95,13 % (1427/1500) |
| `pytest tests/ -m slow` completo (confirma que este es el único test `slow`) | — | `1 passed, 71656 deselected` en 182,75 s |
| `pytest` por defecto (sin `slow`/`benchmark`, todo lo demás) | no medido por este ticket (ajeno al cambio) | `71630 passed, 4 skipped, 2 deselected, 21 xfailed` en 632,76 s (10 min 33 s) |

**Sobre el criterio «la suite baja de ~37 min a <10 min»:** el test que es el
sujeto literal de 39.32 baja de un entorno de decenas de minutos a 3 min 8 s —
una mejora de orden 6-9×, que es lo que este ticket pedía arreglar. El resto
de la suite (no tocado por este cambio) ya toma ~10,5 min en este contenedor
concreto, así que el total combinado (~13,6 min) no baja literalmente de 10 en
*este* hardware. No puedo verificar si la cifra «~37 min» de referencia se
midió en una máquina más rápida donde el resto de la suite cabe en unos 6-7
min (lo que sí dejaría el total por debajo de 10 con este fix) — lo que sí es
un hecho medido es que el test cuadrático, que es el que preguntaba 39.32,
deja de serlo.

## Validación de la guarda (Regla 11)

Mutación: `candidate_ids` solo con el primer término de la query en vez de la
unión de todos → los 15 tests de `tests/unit/test_rag.py` seguían en **verde**
(ningún test existente vigilaba esa invariante) excepto el nuevo
`test_retrieve_unions_candidates_across_all_query_terms`, añadido para
cerrar ese hueco, que da **rojo** con la mutación y **verde** restaurado.
