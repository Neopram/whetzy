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
   por cohorte, no la misma gente medida dos veces).
2. **No empeora D7**: comparación de dos proporciones (retención a 7 días).
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

- **D7 (dos proporciones)**: calcula el tamaño de muestra por la fórmula
  cerrada estándar (Fleiss) **y** lo cruza con una simulación Monte Carlo
  (2000 repeticiones por celda) de un test z de dos proporciones real. Las
  dos caen en el mismo orden de magnitud siempre (p. ej. drop del 12pp:
  fórmula cerrada n=131, simulación confirma 81% de potencia empírica justo
  en n=131) — la fórmula cerrada queda verificada contra una simulación
  independiente, no solo citada de un libro.
- **AUC (dos AUCs independientes, no pareadas)**: no hay una fórmula cerrada
  tan simple y fiable como la de proporciones para este caso, así que es
  simulación de principio a fin: genera puntuaciones de un modelo binormal
  calibrado para que el AUC resultante sea el objetivo exacto (Hanley &
  McNeil 1982), calcula el AUC de cada cohorte con `sklearn.roc_auc_score`
  (la misma función que ya usa `docs/ml/kt-benchmark.json`, 11.3) y decide
  significación con un test de permutación sobre la diferencia observada —
  no con un supuesto de normalidad adicional.

## Resultados (semilla `20261002`, α=0,05, potencia objetivo 80%)

### D7: usuarios por brazo para detectar una caída desde el 20% base (criterio 11.8)

| Caída absoluta | n/brazo (fórmula cerrada) | n/brazo (Monte Carlo, confirma) |
|---|---|---|
| 20% → 15% (-5 pp) | 906 | 1132 (79% en 906, 88% en 1132 — el umbral real cae entre los dos) |
| 20% → 12% (-8 pp) | 329 | 411 (80% redondeado en 329, confirmado por encima del 80% en 411) |
| 20% → 8% (-12 pp) | 131 | 131 (81%) |

(Las dos columnas no tienen por qué coincidir dígito a dígito — son dos
métodos independientes sobre el mismo problema, no el mismo cálculo repetido;
que caigan en el mismo orden de magnitud es la confirmación que importa.)

### AUC: respuestas por brazo para detectar el margen BKT→DKT (criterio 11.3)

Base real medida: BKT AUC = 0,7983, DKT AUC = 0,8294 (margen 0,0311) —
`docs/ml/kt-benchmark.json`, no un número inventado para este documento.

| Margen de AUC | Respuestas/brazo para 80% de potencia |
|---|---|
| 0,0311 (el margen medido) | entre 3000 (76%) y 6000 (100%) — el umbral real cae en algún punto intermedio |
| 0,08 (margen mayor, hipotético) | ≤ 1000 (98% ya en 1000) |

**Esto es en respuestas, no en usuarios** — el experimento vive el tiempo que
tarde en acumularse ese volumen, no un número fijo de personas. Traducción a
usuarios, según cuántas respuestas registre cada uno durante la ventana del
experimento:

| Respuestas por usuario durante el experimento | Usuarios/brazo para 4000 respuestas (margen medido) |
|---|---|
| 10 | 400 |
| 30 | 134 |
| 50 | 80 |
| 100 | 40 |

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
