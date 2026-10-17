# 32.2 — A/B BKT vs DKT: diseño y análisis de potencia (sin activar)

**Estado: preparado, NO activado.** Bloqueado por H.10 (cohorte beta ≥ 30
usuarios reales) igual que 11.8, del que depende directamente. Nada en este
documento ni en `backend/scripts/power_analysis_bkt_vs_dkt.py` crea un
experimento, escribe en la base de datos ni cambia ningún flag — es diseño y
aritmética, para tenerlo listo el día que H.10 se levante.

Reproducible: `cd backend && python scripts/power_analysis_bkt_vs_dkt.py`
(semilla fija `20261002`).

## Regla de adopción (literal del ledger, fila 32.2)

> DKT se adopta solo si AUC ≥ 0,70, supera a BKT y no empeora D7 ni la
> latencia p95.

Tres condiciones, tres chequeos distintos — no una sola métrica resumen:

1. **AUC ≥ 0,70 Y DKT > BKT**: comparación de dos AUCs independientes (una
   por cohorte, no la misma gente medida dos veces) — una pregunta de
   **superioridad**: ¿DKT es mejor?
2. **No empeora D7**: una pregunta de **no inferioridad**, no de
   superioridad ni de "detectar cualquier diferencia" — corrección de la
   revisión adversaria del `[COORD]` (2026-10-03 17:21 en el #89). Ver la
   sección dedicada más abajo.
3. **No empeora la latencia p95**: un umbral de ingeniería, no una hipótesis
   estadística — se vigila como gate absoluto (p95 de `/quiz/answer` bajo el
   mismo presupuesto en ambas cohortes), no con un cálculo de potencia. Una
   regresión de latencia se detecta con monitorización normal (Sentry/
   `/metrics`, ya en producción), no necesita una cohorte de tamaño
   calculado — no tiene sentido una pregunta de la forma "¿cuántos usuarios
   hacen falta para detectar que la p95 subió 50 ms?": eso ya lo contesta el
   dashboard existente con cualquier volumen.

Este documento y el script de potencia solo cubren las condiciones 1 y 2, que
sí son preguntas de "cuántos usuarios/respuestas hacen falta".

## Diseño del experimento (cuando H.10 se levante)

**Asignación**: estable por usuario, vía el framework genérico ya existente
`app.services.experiments.get_user_variant` (24.14) — no el atajo
`ab_harness.get_cohort` que ya usa `quiz.py` en producción para una decisión
más simple (qué modelo usar para seleccionar la siguiente skill). La fila
32.2 pide explícitamente "con el framework 24.14": usar el genérico permite
registrar la asignación en `ExperimentAssignment` y analizarla después por
cohorte sin tener que reconstruirla a partir de hashes.

**Arranque**: crear una fila `Experiment` con `status="draft"` (nunca
`"active"` hasta que un humano decida lanzarlo) — `get_active_experiments()`
ya filtra por `status == "active"`, así que una fila en `draft` no afecta a
ningún usuario real aunque exista en la base de datos. Esta fila NO se crea
en este PR: queda como el primer paso de activación, documentado aquí, no
ejecutado.

**Duración**: hasta alcanzar el `n` que exija el análisis de potencia de
abajo para el efecto mínimo que importa detectar, no un número de días fijo
de antemano.

## Por qué el análisis de potencia necesita simulación, no solo una fórmula

Las dos métricas (AUC, D7) tienen fórmulas de potencia estándar en los
libros, pero una fórmula copiada sin comprobar es exactamente el tipo de
afirmación que esta sesión no hace sin verificarla. El script:

- **D7 (dos proporciones, NO INFERIORIDAD)**: calcula el tamaño de muestra
  por la fórmula cerrada de no inferioridad (un lado, ver sección dedicada
  más abajo) **y** lo cruza con una simulación Monte Carlo (2000
  repeticiones por celda) de un test de no inferioridad real, simulando los
  dos brazos con la MISMA tasa verdadera (DKT realmente equivalente a BKT,
  el escenario que la regla de adopción necesita poder detectar). Las dos
  caen en el mismo orden de magnitud siempre — la fórmula cerrada queda
  verificada contra una simulación independiente, no solo citada de un
  libro.
- **AUC (dos AUCs independientes, no pareadas)**: no hay una fórmula cerrada
  tan simple y fiable como la de proporciones para este caso, así que es
  simulación de principio a fin: genera puntuaciones de un modelo binormal
  calibrado para que el AUC resultante sea el objetivo exacto (Hanley &
  McNeil 1982), calcula el AUC de cada cohorte con `sklearn.roc_auc_score`
  (la misma función que ya usa `docs/ml/kt-benchmark.json`, 11.3) y decide
  significación con un test de permutación sobre la diferencia observada —
  no con un supuesto de normalidad adicional.

## Resultados (semilla `20261002`, α=0,05, potencia objetivo 80%)

### D7: NO INFERIORIDAD — usuarios por brazo para poder afirmar "no empeora" (criterio 11.8)

**Corrección de la revisión adversaria del `[COORD]` (2026-10-03 17:21 en el
#89): "no empeora D7" es una pregunta de no inferioridad (de un lado), no
"¿podemos detectar que cambió?" (de dos lados).** La diferencia no es solo de
vocabulario: H0 pasa a ser "DKT es `margen` peor que BKT de verdad" y se
necesita potencia para RECHAZAR eso cuando DKT es en realidad equivalente —
no para detectar una caída hipotética de ese tamaño. Esto necesita menos
usuarios que la pregunta de dos lados para el mismo margen, porque solo
importa una dirección (que empeore) y asume equivalencia real bajo H1, no
una tasa peor específica:

| Margen de "no empeora" | n/brazo (fórmula cerrada, no inf.) | n/brazo (Monte Carlo, confirma) | n/brazo (de dos lados, para comparar) |
|---|---|---|---|
| 5 pp (DKT no más de 5pp peor que 20%) | 792 | 990 | 906 |
| 8 pp | 310 | 387 | 329 |
| 12 pp | 138 | 138 | 131 |

(La columna de Monte Carlo a veces sale un escalón por encima de la fórmula
cerrada por el redondeo de la tabla de candidatos probados —p. ej. a 5pp la
potencia empírica en n=792 ya mostraba 0,80 redondeado pero por debajo del
80% exacto, así que el script sigue al siguiente candidato, 990— no porque
las dos fórmulas discrepen de fondo; que caigan en el mismo orden de
magnitud es la confirmación que importa, igual que antes.)

Reproducible: `cd backend && python scripts/power_analysis_bkt_vs_dkt.py`
(las dos primeras columnas son la salida real del script; la de dos lados es
`two_proportion_n_closed_form(0.20, 0.20 - margen)`, definida en el script pero no impresa).

### AUC: SUPERIORIDAD — respuestas y usuarios por brazo para detectar el margen BKT→DKT (criterio 11.3)

A diferencia de D7, el criterio de AUC («AUC ≥ 0,70 **y** DKT > BKT») sí es
una pregunta de superioridad — sigue siendo un test de detección, de dos
lados, sin cambios de planteamiento.

Base real medida: BKT AUC = 0,7983, DKT AUC = 0,8294 (margen 0,0311) —
`docs/ml/kt-benchmark.json`, no un número inventado para este documento.

| Margen de AUC | Respuestas/brazo para 80% de potencia |
|---|---|
| 0,0311 (el margen medido) | 6000 |
| 0,08 (margen mayor, hipotético) | 1000 |

**Esto es en respuestas, no en usuarios** — el experimento vive el tiempo que
tarde en acumularse ese volumen, no un número fijo de personas. El propio
script traduce a usuarios/brazo, según cuántas respuestas registre cada uno
durante la ventana del experimento (antes era aritmética hecha a mano en
este documento; ahora es la salida real del script, para que las dos no
puedan desincronizarse):

| Respuestas por usuario | Usuarios/brazo (margen medido, 6000 respuestas) | Usuarios/brazo (margen 0,08, 1000 respuestas) |
|---|---|---|
| 10 | 600 | 100 |
| 30 | 200 | 34 |
| 50 | 120 | 20 |
| 100 | 60 | 10 |

## La pregunta que esto NO contesta todavía

¿Cuántas respuestas genera un usuario real por semana en este producto? No
hay datos de uso real (H.10) para fijar esa cifra — es la misma razón por la
que 11.8 sigue bloqueada. La tabla de arriba da la sensibilidad (cuántos
usuarios hacen falta *si* generan X respuestas), no una única respuesta; en
cuanto exista la cohorte de H.10 y unas primeras semanas de uso real, esa
columna deja de ser una suposición y se puede fijar una duración concreta del
experimento.

## Qué falta para activar esto

1. H.10: cohorte beta real (≥ 30 usuarios no basta por sí solo — el análisis
   de arriba sugiere que el experimento necesita cientos de usuarios con
   varias semanas de uso para el margen de AUC realista, muchos más que el
   mínimo de 30 que H.10 pide para otras afirmaciones del motor).
2. Una vez haya unas primeras semanas de datos reales: fijar la cifra de
   "respuestas por usuario en la ventana del experimento" y recalcular la
   duración concreta con este mismo script.
3. Decisión del dueño: lanzar el experimento (crear la fila `Experiment` con
   `status="active"`) — no es una decisión reversible desde código, va a
   «Solo el dueño».
