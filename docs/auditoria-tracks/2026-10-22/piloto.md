# Piloto de auditoría de tracks: track01, track12, track16 (2026-10-22)

Fase 2 del plan de auditoría, solo para los tres tracks del piloto. Sin escritura de contenido (ADR-62).
Estado: **PARCIAL**. Esta sección no asigna puntuaciones 0-100 donde no hay evidencia: la celda queda vacía, como exige el plan.

Procedencia de cada cifra, para leer lo que sigue:
- **[Verificado]**: lo comprobé yo con herramientas en esta sesión (curl, sqlite3, lectura del JSON o del código).
- **[Revisor]**: lo afirma un revisor adversario (Sonnet) que releyó el fichero citado. No lo he reproducido todo.
- **[Lector]**: lo afirma un lector (Haiku) desde WebFetch o búsquedas por palabra clave. Es rung 4.

## 1. Referencias

| Track | Referencia | URL | Licencia | Uso permitido |
|---|---|---|---|---|
| track01 | CS50's Introduction to Programming with Python (Harvard) | https://cs50.harvard.edu/python/ | CC BY-NC-SA 4.0 · [Verificado] en https://cs50.harvard.edu/python/license/ (curl, HTTP 200) | Solo mapa de temario. Sin copia (NC y SA: ADR-11/47). |
| track12 | CS50's Introduction to Databases with SQL (Harvard) | https://cs50.harvard.edu/sql/ | CC BY-NC-SA 4.0 · [Verificado] en https://cs50.harvard.edu/sql/license/ (curl, HTTP 200) | Idem. |
| track16 | MIT 6.006 Introduction to Algorithms, OCW (Spring 2020) | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/ | CC BY-NC-SA 4.0 · [Verificado] en el HTML de la página (curl, HTTP 200) | Idem. |

Fecha de lectura: 2026-10-22. Las tres referencias son NC-SA: **ninguna puede ser fuente de contenido**, solo mapa de temario.

Temario de semanas de CS50: [Lector] lo leyó vía WebFetch, que devuelve un resumen. Mi descarga cruda de la página SQL solo muestra «Final Project»; los títulos de semana **no quedaron verificados por mí**. La afirmación del borrador «CS50P dedica la semana 7 a expresiones regulares» queda en esa misma situación.

## 2. Cobertura frente al temario

### track01 (CS50P)
- [Revisor] De 24 temas del mapa del lector: **20 se enseñan en lección** (3 solo en texto: paquetes con `__init__.py`, archivos y `random`), **4 solo se mencionan**: `sort` con `key=lambda`, `pass`, `os` (solo una frase), `@property` (una frase). Herencia múltiple, parcial.
- [Lector] Ausentes sin ninguna skill ni lección: `match`/`case`, `statistics`, `requests` y códigos HTTP, `assert` y pruebas unitarias (`unittest`/`pytest`), comentarios `#`, introducción al entorno de trabajo. `sys.argv`, regex y decorador propio aparecen solo como frase o una pregunta.
- **Regex, corrección al borrador** [Verificado]: ninguna lección de tracks 01-03 enseña regex. Hay **una frase** en `l010802` («El módulo re permite trabajar con expresiones regulares»). Hay **una pregunta** sobre regex, `q010802006`, que pide completar `import ___`; ninguna pregunta usa `re`. El borrador dice «1 pregunta que usa re»: no es exacto.

### track12 (CS50 SQL)
- [Lector] 16 temas del mapa. Cubiertos: SELECT/LIMIT/OFFSET, WHERE, IS NULL, LIKE, BETWEEN, ORDER BY, GROUP BY, HAVING, INNER y LEFT JOIN, subconsultas, CTE básicas y recursivas, índices.
- [Revisor] Confirma esos temas; matiza que el ejemplo de `IS NULL` usa `COALESCE`, no `IS NULL`, y que la subconsulta `IN (SELECT …)` no se muestra.
- [Revisor] `EXPLAIN QUERY PLAN` solo aparece en **preguntas** de `sk120504` (`q120504mc004`, `q120504mc012`); la lección no lo menciona.
- [Lector, sin revisar] Ausentes: normalización, diagramas ER, claves foráneas, `ALTER`/`DROP`, `CHECK`, triggers, vistas, CSV, `VACUUM`, bloqueos, escalado, procedimientos, `GRANT`/`REVOKE`, inyección SQL, sentencias preparadas. La búsqueda fue por palabra clave; no hay revisión de cada uno.

### track16 (MIT 6.006)
- [Lector] 8 temas del mapa. Su resumen dice «5 cubiertos» y su tabla tiene 8 filas: **el resumen del lector es inconsistente con su propia tabla**; no lo uso.
- [Revisor] Enseñados: pilas/colas/listas enlazadas, hashing, árboles binarios, BFS, DFS, DP (dos temas, uno con matiz). **Parcial**: ordenación, donde merge y quick se enseñan, pero heap sort y los de no comparación solo se mencionan.
- [Lector, sin revisar] Ausentes: Bellman-Ford, Johnson, pseudopolinomios, APSP y paréntesis de cadena de matrices, AVL. Solo menciones: counting/radix, NP-completitud.

## 3. Defectos de contenido verificados

Muestra del revisor: 20 preguntas por track (las 20 primeras por id). **Una muestra de 20 no da una tasa de error**; los hallazgos son ejemplos concretos, no un porcentaje.

| Id | Track | Hallazgo | Evidencia | Rango | Gravedad |
|---|---|---|---|---|---|
| q120102mc003 | track12 | La respuesta marcada («No; WHERE se evalúa antes de SELECT») es falsa para SQLite, el motor del track. | [Verificado] SQLite 3.45.1: `select p*q as t from s where t>5` devuelve `[(6,)]`. El alias funciona en WHERE. | Verificado | Alta |
| l120304 | track12 | Dice que «SQLite no soporta FULL OUTER JOIN nativamente». | [Verificado] SQLite 3.45.1 ejecuta `full outer join` y devuelve filas de ambos lados. El soporte llegó en 3.39.0 según el revisor (de memoria, no verificado). | Verificado | Media |
| q160101003 | track16 | Dos opciones están en orden creciente: «O(1), O(log n), O(n), O(n log n)» y la marcada, «O(1), O(n log n), O(n²), O(2ⁿ)». La explicación dice «logarítmico O(n log n)». | [Verificado] lectura del JSON (`correct_index` 2). | Verificado | Alta (ambigua) |
| q160101ex004 | track16 | Pregunta sobre complejidad Big O; la respuesta marcada es `10`, que es el valor impreso del programa, no una complejidad. | [Verificado] `correct_answer_es: "10"` en un `fill_blank`. | Verificado | Alta |
| l160301 | track16 | El código de merge sort usa `left.pop(0)` y `right.pop(0)`, que cuestan O(n) cada uno, y el comentario dice `# Merge Sort O(n log n)`. | [Verificado] lectura del JSON. Costo no ejecutado. | Verificado | Media |
| l160203 | track16 | `def inorder(node, result=[])`: argumento mutable por defecto, que acumula entre llamadas. | [Verificado] grep del JSON. Efecto no ejecutado. | Verificado | Media |
| l011203 | track01 | La lista de funciones de `math` incluye «abs() para valor absoluto». `math.abs` no existe; `abs` es función incorporada. | [Verificado] `hasattr(math, 'abs')` es False; `math.fabs` existe. | Verificado | Baja |
| q010101005 | track01 | Enunciado sobre «no enlazada a ningún valor» con respuesta `is None`. | [Revisor] Menor, de redacción. No lo he decidido. | Revisor | Baja |
| l010103, l010105, l010603, l010803, l010902 | track01 | Imprecisiones menores: nombre de error inexistente, «únicamente» en la lista de valores falsos, `capitalize()` que no baja el resto, `write()` que no borra, `__init__.py` presentado como requisito. | [Revisor] | Revisor | Baja |

Track01: en la muestra de 20 preguntas, el revisor no encontró fallos graves.

## 4. Medidas del script (`scripts/audit_tracks.py`, [Verificado])

| Track | Preguntas | Ejecutables estrictos | % | Con código | Lecciones | Mediana palabras/lección | Proyectos |
|---|---:|---:|---:|---:|---:|---:|---:|
| track01 | 870 | 139 | 16,0 % | 466 | 52 | 216 | 0 |
| track12 | 300 | 60 | 20,0 % | 60 | 20 | 176 | 0 |
| track16 | 158 | 0 | 0,0 % | 0 | 12 | 229 | 0 |

## 5. Qué dice esto sobre la rúbrica

- **D3 (práctica que construye)**: medido y claro. Los tres tracks tienen 0 proyectos; track16 no tiene ningún ejecutable.
- **D5 (calidad del banco)**: los defectos verificados aparecen en track12 y track16, no en track01 dentro de la muestra. Con 20 preguntas por track no se puede concluir una tasa de error.
- **D2 (profundidad)**: el revisor reproduce el rango de palabras (204-235 en las primeras lecciones de track01). Los defectos factuales de lección están en los tres tracks.
- **D1 (cobertura)**: depende de un temario que no he podido verificar en crudo (semanas de CS50). **No puntúo D1 hoy.**
- **D4, D6, D7**: no evaluados en el piloto.

Respuesta a «¿la rúbrica distingue bien los tres tracks?»: en D3 sí. En D5 los fallos verificados se reparten de forma que tendría sentido, pero la muestra es demasiado pequeña para decirlo. Antes de escalar a los 32 tracks restantes hacen falta: muestreo estratificado de D5, verificar el temario de referencia en crudo, y que el dueño firme los pesos.

## 6. Correcciones al borrador

- «0 lecciones de regex y 1 pregunta que usa re»: **no exacto**. 0 lecciones que enseñen regex; 1 frase; 1 pregunta que pide el nombre del módulo, ninguna que lo use.
- Parte V dice «planificados sin construir (21)». La tabla y el script dan **19**: 35 construidos + 2 en cuarentena + 19 planificados = 56.
- «12.037 · 730 · 1.058 · 22 de 35»: **cuadra con `origin/master`** (verificado). La copia de trabajo local estaba atrasada 17 commits y daba 11.416 preguntas; la auditoría se hace sobre `origin/master`.
- Fichero suelto `track13_fix_bug_sin_codigo.json` (15 preguntas): excluido de los totales (verificado).
- Ficha de track01 con «52 skills»: el script da 52; el catálogo de forma pide 32, así que track01 es el único en la forma de aprendizaje por tener más de 32 (verificado con el mismo criterio de `catalog_coverage.py`).

## 7. Decisiones que tomé por defecto (la fase 0 pide al dueño)

El plan pedía parar en la fase 0 hasta que el dueño firmara. Me pediste ejecutarlo; tomé estas decisiones y las dejo visibles:
1. Rúbrica de 7 dimensiones con los pesos propuestos. **Sin firmar.**
2. Análisis sí, contenido no (ADR-62 en espera). No se escribió ninguna pregunta, lección ni término.
3. Piloto con track01, track12 y track16.

## 8. Qué no está hecho

- Fase 2 completa (32 + 19 tracks): no lanzada; el plan pide decisión del dueño (~70 agentes).
- Sección en `docs/competitive-teardown.md`: no añadida; los pesos no están firmados.
- Fila de ledger: no añadida; falta decidir la serie.
- Corrección de los defectos de la §3: no hecha (ADR-62, y la corrección de contenido necesita decisión del dueño).
- Las licencias de los materiales de vídeo y de los problem sets de las tres referencias: no revisadas.
