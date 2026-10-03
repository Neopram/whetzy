---
title: "La matemática de FSRS: cómo Whetzy programa los repasos de programación"
slug: "math-behind-fsrs"
date: "2026-10-02"
lang: es
author: "Whetzy"
summary: "FSRS cambia 'repasa cada N días' por tres números por habilidad — estabilidad, dificultad, recuperabilidad — y actualiza los tres después de cada respuesta."
---

La mayoría de las herramientas de repetición espaciada todavía corren sobre
SM-2, el algoritmo que traía Anki en 2006: intervalos fijos, un solo "factor
de facilidad" por tarjeta, y poco más. Whetzy usa **FSRS-6** en su lugar — un
modelo de 21 parámetros que cambia el único número de SM-2 por tres,
actualizados con datos reales en vez de una curva ajustada a mano.

## Qué sigue FSRS de verdad, por habilidad

Nuestra implementación (`app/services/engine/fsrs.py`) guarda tres números por
`Card`:

- **Estabilidad** — a grandes rasgos, cuántos días tardaría tu probabilidad de
  recordar en caer al 90 %. Más estabilidad, más tiempo hasta que necesites
  otro repaso.
- **Dificultad** — qué tan difícil es esta habilidad concreta para vos en
  particular, no qué tan difícil es en abstracto.
- **Recuperabilidad** — la estimación actual del modelo de "si te preguntaran
  ahora mismo, qué probabilidad hay de que aciertes".

Cada repaso actualiza los tres, no solo "acerté o no". El flujo clásico de
FSRS pide que el alumno se autocalifique en una escala de 4 — Otra vez,
Difícil, Bien, Fácil. Nosotros no te lo pedimos: Whetzy calcula la nota por
vos, a partir de si acertaste y qué tan rápido respecto al tiempo esperado
(`_grade_from_response` en `app/services/quiz.py`) — "acerté pero tardé más
de lo esperado" y "acerté rápido" caen en notas distintas (Difícil vs. Fácil)
aunque las dos sean "correcto", igual que en la versión autocalificada, solo
que medido en vez de preguntado.

## De dónde vienen los 21 números

Los pesos de FSRS no son nuestros — vienen del proyecto open-spaced-repetition,
ajustados contra unos 700 millones de registros reales de repasos en Anki. Ese
es el punto real de usar FSRS en vez de un factor de facilidad de SM-2 elegido
a mano: la curva que describe cómo decae la memoria se ajustó a cómo decayó de
verdad la memoria en cientos de millones de repasos reales, no se adivinó por
quien diseñó un algoritmo en 2006. La cifra publicada detrás de FSRS (algo que
no medimos de forma independiente sobre los registros de repaso de Whetzy) es
20-30 % menos repasos que SM-2 para la misma retención — menos repeticiones
gastadas en cosas que ya tenías firmes, porque la estabilidad se sigue por
tarjeta en vez de inferirse de una sola curva de facilidad compartida.

## Por qué esto importa para programar, no solo para tarjetas de memoria

FSRS se construyó para tarjetas de memoria — vocabulario, trivia, cualquier
cosa con una señal limpia de "me acordé o no". Las habilidades de programación
son más desordenadas: "te acordás de las comprensiones de listas" no es un solo
hecho, es un grupo de juicios relacionados. Lo que seguimos por habilidad (no
por pregunta individual) es si retuviste la *habilidad*, con las preguntas
concretas elegidas por dificultad vía Elo dentro de esa habilidad (ver nuestra
entrada sobre la arquitectura del motor) en vez de que FSRS intente modelar
cada pregunta como su propia memoria independiente.

## La salvedad honesta

No hemos publicado cifras de retención específicas de Whetzy que comparen
nuestra programación con FSRS frente a una base de intervalo fijo sin
adaptación — eso necesitaría un A/B test en forma, con usuarios suficientes
para decir algo real, el mismo estándar que le exigimos al experimento de DKT.
La cifra de 20-30 % de arriba es el resultado publicado del propio FSRS sobre
datos de Anki, no un resultado de Whetzy, y lo decimos así en vez de dejar que
la cita se confunda con una afirmación sobre nosotros.

---

*Whetzy (whetzy.com) — aprendizaje bilingüe y adaptativo de Python a IA.*
