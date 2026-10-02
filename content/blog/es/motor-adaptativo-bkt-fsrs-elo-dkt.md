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

Juntos, estos tres decimen dos cosas cada vez que abrís una lección: qué
habilidad estás listo para practicar y qué pregunta concreta — de las que
existan para esa habilidad — es la dificultad correcta para vos en ese
momento.

## El que sigue siendo un experimento: DKT

**DKT (Deep Knowledge Tracing)** — `app/services/dkt.py` — es un modelo
neuronal que predice el dominio a partir de todo tu historial de respuestas,
no solo una probabilidad por habilidad. Es código real, corre, y está
conectado al endpoint de quiz — pero solo para quienes caen en la cohorte de
A/B `"dkt"` (`app/services/quiz.py`: `if get_cohort(user.id) == "dkt":
predictions = _dkt.predict(history)`). La mayoría de los estudiantes sigue en
el camino BKT+FSRS+Elo de arriba. No decimos que DKT "mueve Whetzy" — mueve
un brazo del experimento, y si le gana a la base es justo lo que el A/B está
ahí para responder. (Un análisis de potencia correcto para esa comparación
— cuántos usuarios hacen falta antes de que el resultado signifique algo —
está en nuestro propio backlog como un trabajo aparte, todavía sin empezar.)

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
mientras estudian — Python, SQL, JavaScript — corren de la misma manera: en el
navegador, vía WebAssembly (Pyodide para Python, sql.js para SQL), sin ida y
vuelta a un servidor.

---

*Whetzy (whetzy.com) — aprendizaje bilingüe y adaptativo de Python a IA.*
