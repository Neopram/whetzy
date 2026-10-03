# 14.10 — Calibración de ítems IRT: validación con datos simulados

**Estado: validado por simulación, no calibrado con datos reales.** El ledger
bloquea esto explícitamente («No antes de tener miles de respuestas»): JMLE
(la técnica usada aquí) es conocida por sesgarse con pocos ítems o
respondientes, y sin datos reales aún no hay nada contra lo que calibrar.
Nada en este módulo toca la base de datos.

Reproducible: `cd backend && python scripts/irt_parameter_recovery.py`
(semilla fija `20261002`, 1500 personas simuladas × 40 ítems = 60 000
respuestas — la cifra que pide el propio criterio del ledger, «miles de
respuestas»).

## Qué existía ya y qué falta

`app/services/engine/placement.py` (`PlacementEngine`) ya hace la mitad de
IRT en producción: dados los parámetros de un ítem (dificultad,
discriminación, adivinación) **fijos**, estima la habilidad θ del alumno por
máxima verosimilitud (Newton-Raphson, `update_ability`) — eso es lo que
necesita la prueba de nivelación adaptativa mientras corre.

Lo que falta, y lo que pide 14.10, es la otra mitad: estimar los parámetros
del ítem **a partir de** respuestas reales. `backend/app/ml/irt_calibration.py`
implementa esto con **Estimación Conjunta de Máxima Verosimilitud** (JMLE,
Birnbaum 1968 / Lord 1980): alternar entre (a) reestimar la habilidad de cada
persona con los parámetros de ítem actuales fijos, y (b) reestimar
discriminación/dificultad de cada ítem con las habilidades actuales fijas,
hasta que las estimaciones se asientan.

## Un bug real de producción, encontrado calibrando con datos simulados

`PlacementEngine.fisher_information()` (usado por `select_next_item` al
elegir la siguiente pregunta de la prueba, y por `update_ability` al calcular
el error estándar) calculaba `math.exp(-discriminación * (θ - dificultad))`
**sin** el mismo recorte de exponente que `probability_correct()`, dos líneas
más arriba en el mismo fichero, ya tenía. Con una discriminación alta y un
ítem lejos de θ, el exponente supera ~700 y `math.exp` lanza `OverflowError`.

Esto no es solo un problema de mi script: `select_next_item` muestrea la
discriminación de una gamma **sin tope** (Thompson sampling) al elegir el
siguiente ítem — el mismo patrón que hizo saltar el error calibrando con
datos simulados puede darse en producción. Arreglado con el mismo recorte que
ya usa `probability_correct` (`backend/app/services/engine/placement.py`,
`fisher_information`); test de regresión
`tests/unit/test_placement_params.py::test_fisher_information_no_revienta_con_discriminacion_extrema`,
confirmado rojo sin el recorte (`OverflowError: math range error`) y verde
con él.

## Dos decisiones de diseño, encontradas por error, no supuestas

### 1. `update_ability` no sirve para recalcular una historia completa de una vez

El plan inicial era reusar `PlacementEngine.update_ability` sin cambios para
el paso de habilidad de JMLE (llamarlo una vez por respuesta, en orden,
acumulando el historial). Medido contra datos simulados con el diseño **más
fácil posible** (cada persona responde los 40 ítems, parámetros de ítem
**verdaderos**, no estimados): recuperación de θ con **r = 0,344**,
RMSE = 3,48 — inservible. `update_ability` hace 10 pasos de Newton-Raphson
**por llamada**, pensado para extender una estimación existente con una
respuesta más durante una prueba adaptativa en vivo, no para resolver de una
vez el ajuste de máxima verosimilitud sobre un vector de respuestas completo.

Sustituido, solo dentro de `irt_calibration.py`, por un ajuste MLE directo
vía `scipy.optimize.minimize` (acotado a [-4, 4], el mismo rango al que
`update_ability` ya recorta θ) sobre el vector de respuestas completo de cada
persona. Mismo caso: **r = 0,86-0,98** según el tamaño de la muestra. Esto
**no** cambia nada de cómo sirve la prueba de nivelación en producción —
`update_ability` sigue siendo la función correcta para su trabajo real,
extender una estimación respuesta a respuesta mientras la prueba corre; es
solo la herramienta equivocada resuelta de una vez sobre un lote completo,
fuera de línea.

### 2. El JMLE sin anclar deriva de escala

IRT solo fija habilidad y dificultad salvo un origen y una escala
compartidos: desplazar cada θ y cada dificultad por la misma constante, o
escalar `(θ - dificultad)` por un factor mientras se escala la discriminación
por su inverso, deja cada probabilidad del modelo exactamente igual. Nada
impide que las actualizaciones alternadas de JMLE deriven por esa
indeterminación. Confirmado empíricamente: sin reescalar, la dificultad
recuperada tenía un sesgo sistemático (una dificultad verdadera de -0,19 se
recuperaba como +1,32) y RMSE > 1,7.

Arreglo: al terminar el bucle (no en cada iteración — probado primero y
empeoraba: r de recuperación de habilidad cayó de 0,86 a 0,16, reescalar la
escala por debajo de ítems que aún no se habían adaptado desestabilizaba el
ajuste), `_rescale_to_standard_metric` lleva la distribución de habilidades a
media 0 / DE 1 y aplica la transformación inversa correspondiente a los
parámetros de ítem (`a' = a·σ`, `b' = (b-μ)/σ`), de forma que
`a·(θ-b)` — y por tanto cada probabilidad — queda exactamente igual.
Verificado con un test dedicado
(`test_rescale_preserves_every_response_probability`), no solo con la mejora
de las cifras.

## Resultado final (1500 personas × 40 ítems, semilla `20261002`, 5 iteraciones JMLE)

| Parámetro | r | RMSE |
|---|---|---|
| Dificultad (b) | 0,990 | 0,167 |
| Discriminación (a), todos los ítems | 0,939 | 0,370 |
| Discriminación (a), ítems con \|dificultad\| ≤ 1,5 (35/40) | 0,949 | 0,328 |
| Habilidad (θ), subproducto de la misma corrida | 0,895 | 0,463 |

## Límite real, no oculto: ítems en la cola de la distribución de habilidad

De los 40 ítems simulados, 5 caen fuera de ±1,5 DE de la media de habilidad
de la población (dificultad verdadera entre -3,03 y 2,20). Tres de esos
cinco se recuperan razonablemente; dos (dificultad 1,63 y 2,20, ambos con
discriminación verdadera alta, ~1,5) **no**: su discriminación estimada
choca con el tope superior de optimización (`DISCRIMINATION_BOUNDS = (0.1,
4.0)`, ver el módulo). Esto no es un fallo del código: un ítem difícil y muy
discriminante, con pocos respondientes cerca de su umbral, produce una
verosimilitud casi-degenerada (separación casi completa) con muy pocos datos
— el mismo problema de identificación que documenta la literatura de IRT
(Baker & Kim, cap. 2), no algo que más iteraciones o más personas totales
arreglen por sí solas (comprobado: subir de 300 a 1500 personas no movió la
discriminación de estos dos ítems). La lección operativa para cuando haya
datos reales: antes de confiar en la discriminación calibrada de un ítem,
comprobar cuántas respuestas reales cayeron cerca de su dificultad, no solo
cuántas respuestas tiene en total.

## Qué falta para activar esto con datos reales

1. Sustituir las respuestas simuladas por respuestas reales de examen/práctica
   (`UserSkillState`/`StudySession`, igual que hace 14.8) y repetir
   exactamente las mismas comprobaciones de recuperación — aunque sin
   parámetros verdaderos que comparar, la validación real pasa a ser
   estabilidad entre repeticiones (¿el mismo ítem calibra parecido con dos
   mitades distintas del mismo banco de respuestas?), no recuperación.
2. Decidir el umbral mínimo de respuestas por ítem antes de confiar en su
   discriminación calibrada (el límite de la sección anterior sugiere que
   «cerca de su propia dificultad», no solo «total», es la métrica que
   importa).
3. Decidir si los parámetros calibrados sustituyen a los que hoy tiene cada
   `IRTItem` a mano, o se usan solo para detectar ítems mal calibrados a
   mano — decisión de producto, no estadística; no la tomo aquí.
