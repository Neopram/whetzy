---
title: "Cómo construimos un motor adaptativo de Python: BKT, FSRS, Elo — y DKT en una celda de A/B"
slug: "adaptive-engine-bkt-fsrs-elo-dkt"
date: "2026-10-02"
lang: es
author: "Whetzy"
summary: "Cuatro modelos, tres de ellos activos para todos y uno que sigue siendo un experimento — y por qué contamos cuál es cuál."
---

"Aprendizaje adaptativo" se usa como palabra de marketing más veces de las que
se usa como palabra de ingeniería. Esto es lo que significa de verdad en el
backend de Whetzy, modelo por modelo, y — porque esto importa por honestidad,
no solo por gusto de ingeniero — cuáles de estos son la experiencia por
defecto de cada estudiante y cuál sigue siendo un experimento que todavía no
llega a todo el mundo.

## Los tres que corren para cada estudiante

- **BKT (Bayesian Knowledge Tracing)** — `app/services/engine/bkt.py`. Sigue
  la probabilidad de que de verdad domines una habilidad, actualizada después
  de cada respuesta (`bkt.update`). No es "la acertaste, seguí" — es una
  probabilidad que se revisa con evidencia, incluida la evidencia de que
  acertaste de casualidad.
- **FSRS (Free Spaced Repetition Scheduler)** — `app/services/engine/fsrs.py`.
  Decide cuándo volvés a ver una habilidad. `fsrs.review(card, grade, now)`
  toma tu desempeño en un repaso y programa el siguiente — la misma familia
  de algoritmo detrás de las herramientas modernas de repetición espaciada,
  aplicada a habilidades de programación en vez de tarjetas de memoria.
- **Elo** — `app/services/engine/elo.py`. Cada estudiante y cada pregunta
  tiene un rating; `elo.expected_score` predice qué tan probable es que
  acertés una pregunta dada antes de que respondas, y `elo.update` ajusta los
  dos ratings después según si esa predicción se cumplió. Esto es lo que
  permite que el selector de preguntas apunte a "lo bastante difícil para ser
  útil, no tanto como para ser una moneda al aire".

Juntos, estos tres deciden dos cosas cada vez que abrís una lección: qué
habilidad estás listo para practicar y qué pregunta concreta — de las que
existan para esa habilidad — es la dificultad correcta para vos en ese
momento.

## El que sigue siendo un experimento: DKT

**DKT (Deep Knowledge Tracing)** — `app/services/dkt.py` — está pensado como
un modelo LSTM que predice el dominio por habilidad a partir de tus últimas
100 respuestas. Es código real y está conectado al endpoint de quiz, detrás
de la cohorte de A/B `"dkt"` (`app/services/quiz.py`: `if get_cohort(user.id)
== "dkt": predictions = _dkt.predict(history)`). Pero el camino LSTM solo
corre cuando PyTorch se puede importar, y `backend/requirements.txt` excluye
torch a propósito — pesa demasiado para nuestro plan de Railway. Así que en
producción, cada quien caiga en la cohorte "dkt" recibe en realidad el
respaldo de `dkt.py`: una media móvil exponencial (`_ALPHA = 0,3`) sobre el
historial reciente de aciertos/errores de cada habilidad, no una red
neuronal entrenada. El reparto de A/B sigue siendo real y determinista por
usuario (`hash(user_id) % 1000 < ratio * 1000`), y el valor por defecto
(`DKT_AB_RATIO` en `app/core/config.py`) es 0,5 — pero lo que esa cohorte
está comparando contra la base, hoy, es el heurístico EWMA, no el LSTM que
sugiere su propio nombre. No decimos que DKT "mueve Whetzy" — mueve un brazo
del experimento, corriendo como un modelo más simple de lo que su docstring
sugiere, y si le gana a la base es justo lo que el A/B está ahí para
responder. (Un análisis de potencia correcto para esa comparación — cuántos
usuarios hacen falta antes de que el resultado signifique algo — está en
nuestro propio backlog como un trabajo aparte, todavía sin empezar.)

## Por qué esta separación importa más que los nombres de los modelos

La decisión de ingeniería interesante no es "usamos cuatro modelos" — es que
tres de ellos son lo bastante simples como para razonarlos y auditarlos (todo
el estado de BKT es una probabilidad por habilidad; lo podés imprimir y tiene
sentido), y el cuarto, el más difícil de auditar, es justo el que todavía no
confiamos para la experiencia de todo el mundo. Esa es la lección real, si
hay una: la sofisticación de un modelo y la confianza que deberías tener para
enviarlo al 100 % de los usuarios son ejes distintos, y confundirlos es cómo
los productos de aprendizaje adaptativo terminan enviando cosas que parecen
inteligentes y rinden peor que una regla simple.

## Código que corre, no solo código que se describe

Cada ejemplo de arriba corresponde a un fichero del backend en producción, no
a un diagrama. Los ejemplos de código que los estudiantes ejecutan de verdad
mientras estudian corren todos en el navegador, sin ida y vuelta a un
servidor — pero no todos de la misma manera: Python corre en Pyodide y SQL en
sql.js, los dos WebAssembly; JavaScript corre en un Web Worker aislado (un
worker por Blob URL, sin acceso al DOM), que no es WebAssembly.

---

*Whetzy (whetzy.com) — aprendizaje bilingüe y adaptativo de Python a IA.*
