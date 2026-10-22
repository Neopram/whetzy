# 14.8 — Predictor beta-binomial de aprobado: validación con datos simulados

**Estado: validado por simulación, no calibrado con datos reales (bloqueado
por H.10 — depende de la cohorte beta de 30+ usuarios).** El código está listo
para usarse con datos reales en cuanto H.10 se libere; nada aquí llama a la
base de datos ni se activa contra usuarios.

Reproducible: `cd backend && python scripts/beta_binomial_calibration.py`
(semilla fija `20261002`, `n_users=5000`).

## El modelo

`backend/app/ml/exam_pass_predictor.py`. La precisión real de un
alumno en preguntas de examen se modela como una probabilidad desconocida
θ con prior Beta(0.5, 0.5) (Jeffreys — mínimamente informativo, simétrico:
no sesga la primera predicción hacia "va a aprobar" ni hacia "va a
suspender" antes de ver ninguna evidencia). Cada respuesta de práctica
(acierto/fallo) es una observación Bernoulli que actualiza la posterior por
conjugación estándar: `Beta(0.5 + aciertos, 0.5 + fallos)`.

La puntuación en un examen real de `n_exam` preguntas no se predice con un
punto (`Binomial(n_exam, θ̂)`): se predice con la distribución
**Beta-Binomial(n_exam, α, β)**, que integra la incertidumbre que aún queda
sobre θ. Esto es lo que hace que dos alumnos con la misma θ̂ = 0.85 pero uno
con 10 respuestas de práctica y otro con 500 reciban `p_pass` distintos: el
primero tiene una posterior ancha, así que la Beta-Binomial reparte
probabilidad sobre un rango más amplio de posibles resultados del examen,
algunos por debajo del corte.

`n_exam_questions` y `pass_pct` salen de `Track.exam_question_count` /
`Track.passing_score_pct` (o `DEFAULT_PASS_PCT = 70.0`), nunca de un valor
inventado — la predicción siempre corresponde al examen que el alumno va a
hacer de verdad.

## Qué supuesto hace esta simulación (revisión adversaria del `[COORD]`, 17:21 UTC)

`simulate_one()` (`backend/scripts/beta_binomial_calibration.py`) genera
tanto las respuestas de práctica como el examen a partir del **mismo**
`theta_true` para un usuario simulado. Eso es correcto para lo que las dos
comprobaciones de abajo validan — que la matemática beta-binomial (cobertura
del intervalo, calibración de `p_pass`) es internamente consistente —, pero
significa que esta simulación **no puede medir, ni mide, ninguna diferencia
sistemática entre el rendimiento en práctica y el rendimiento en un examen
real** (nervios, formato distinto, preguntas de práctica más fáciles que las
de examen, fatiga, etc.): si existiera un sesgo así en la realidad, el
modelo seguiría viéndose perfectamente calibrado aquí porque la simulación
asume por construcción que practicar y examinarse miden exactamente la
misma θ. Ese es precisamente el punto 1 de «Qué falta para activar esto con
datos reales» más abajo: con datos reales hay que comprobar esta igualdad,
no asumirla.

## Por qué dos validaciones, no una

Un único número de precisión agregada puede ocultar un modelo mal calibrado.
Hacen falta dos comprobaciones separadas, y los datos simulados (con θ
verdadera conocida) son los únicos que permiten hacer la primera:

### 1. Recuperación de parámetros (cobertura del intervalo creíble)

Para cada alumno simulado con una θ verdadera conocida, ¿el intervalo creíble
del 90 % contiene de verdad a esa θ, aproximadamente el 90 % de las veces?
Un modelo puede tener una `theta_mean` con buena pinta y aun así reportar
intervalos demasiado estrechos (sobreconfiado) o demasiado anchos
(infraconfiado).

| n práctica | cobertura (nominal 90 %) | ancho medio del IC |
|---|---|---|
| 10 | 89.3 % | 0.394 |
| 30 | 90.1 % | 0.246 |
| 100 | 90.4 % | 0.139 |
| 300 | 89.5 % | 0.081 |
| 1000 | 89.1 % | 0.044 |

Las cinco dentro de ±3 errores estándar binomiales del 90 % nominal
(n=5000 alumnos simulados por fila, semilla `20261002 * 1000 + n_práctica`).
El ancho del intervalo se reduce monótonamente de 0.39 a 0.04 según crece la
práctica — la incertidumbre se recupera correctamente, no es un número
decorativo.

### 2. Curva de calibración + Brier score (sobre el resultado del examen)

Sobre una mezcla realista de θ verdaderas (uniforme en [0.3, 0.98]) y
cantidades de práctica (10 a 1000 respuestas), se agrupan las predicciones de
`p_pass` en 10 cubos y se compara la media predicha contra la tasa de
aprobado observada en la simulación — el chequeo literal del ticket, «de
aquellos a quienes dijimos 90 %, aprobó ~90 %», contra un examen simulado en
vez de uno real:

| cubo (rango de p_pass) | n | predicho | observado | \|error\| |
|---|---|---|---|---|
| 0.00–0.00 | 500 | 0.000 | 0.000 | 0.000 |
| 0.00–0.00 | 500 | 0.001 | 0.000 | 0.001 |
| 0.00–0.03 | 500 | 0.012 | 0.010 | 0.002 |
| 0.03–0.12 | 500 | 0.064 | 0.068 | 0.004 |
| 0.12–0.28 | 500 | 0.200 | 0.204 | 0.004 |
| 0.28–0.57 | 500 | 0.450 | 0.430 | 0.020 |
| 0.57–0.84 | 500 | 0.730 | 0.730 | 0.000 |
| 0.85–0.97 | 500 | 0.914 | 0.906 | 0.008 |
| 0.97–1.00 | 500 | 0.991 | 0.984 | 0.007 |
| 1.00–1.00 | 500 | 1.000 | 0.998 | 0.002 |

Las 10 filas por debajo del umbral de 0.10 de error (el mismo listón que usa
32.1/`calibration_curve.py` para BKT); el peor error real es 0.020.

**Brier score:** modelo = 0.0768, base-rate-only (predecir la tasa media de
aprobado del 43.3 % para todo el mundo) = 0.2455. Brier skill score = 0.687
(> 0 significa que el modelo mejora sobre adivinar la tasa base; 1.0 sería
predicción perfecta).

## Validación de la fórmula en sí (no solo del comportamiento)

`backend/tests/unit/test_exam_pass_predictor.py::test_p_pass_matches_monte_carlo_simulation`
cruza la función de supervivencia Beta-Binomial cerrada contra una simulación
Monte Carlo independiente (semilla `20261002`, 200 000 repeticiones:
muestrear θ de la posterior, luego una puntuación de examen de
`Binomial(n_exam, θ)`), con una tolerancia de 1,5 puntos porcentuales (muy
por encima del error estándar de Monte Carlo a ese tamaño de muestra). Esto
atraparía un error de uno-por-uno en el corte o un alfa/beta intercambiado
que un test de «¿es alto o bajo?» no detectaría.

**Regla 11 (romper la guarda a propósito):** mutar `cutoff - 1` a `cutoff` en
la función de supervivencia (el error de uno-por-uno clásico) → 2 de 12 tests
en rojo (`test_p_pass_matches_monte_carlo_simulation`,
`test_more_practice_at_the_same_ratio_narrows_the_interval`); restaurado →
12/12 en verde.

## Qué falta para activar esto con datos reales

1. **Datos reales de práctica → examen**: cuando exista la cohorte de H.10,
   sustituir las simulaciones por pares reales (aciertos/fallos de práctica
   antes del examen, resultado real del examen) y repetir exactamente las
   mismas dos comprobaciones (cobertura del intervalo, curva de calibración +
   Brier) contra la realidad en vez de contra el simulador. Esto es también
   la primera vez que se puede comprobar de verdad el supuesto que esta
   simulación se salta (sección de arriba): si la práctica predice el examen
   real igual de bien que predice, en la simulación, un examen generado con
   la misma θ.
2. **Elegir qué cuenta como "práctica relevante"**: ¿todas las respuestas del
   alumno en el track, o solo las de modo examen/repaso? Esto es una decisión
   de producto, no estadística — no la tomo aquí.
3. **Endpoint público** (14.9, URL verificable): este módulo da el número;
   publicarlo con una URL estable y sin necesidad de login es la fila
   siguiente.
