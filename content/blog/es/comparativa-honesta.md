---
title: "Whetzy frente a las plataformas de catálogo — una comparativa honesta"
slug: "honest-comparison"
date: "2026-10-02"
lang: es
author: "Whetzy"
summary: "Comparamos contra lo que de verdad volvimos a comprobar en la página de precios de cada competidor, no contra lo que suponemos de ellos."
---

El ítem del ledger detrás de esta entrada pedía "una comparativa honesta frente
a Coursera y Udemy". No publicamos una — y el motivo es justo lo que hace que
esta comparativa merezca llamarse "honesta".

## Por qué Coursera y Udemy no están en esta tabla

Lo comprobamos. La página de precios de Udemy devuelve un 403 a cualquier
acceso automatizado cada vez que lo intentamos (la última, hoy, 2026-10-02) —
no tenemos una cifra verificada de forma independiente para ella. El precio de
Coursera Plus existe solo como una cifra que un rastreo anterior reportó pero
nunca volvió a descargar ni confirmar contra la página en vivo (registrado
internamente como "probable", no "comprobado" — ver `docs/COMPETENCIA.md`
§A.2). Publicar una cifra concreta para cualquiera de los dos aquí, en una
página cuya premisa entera es "solo mostramos lo que comprobamos", socavaría
esa premisa en la primera fila.

Así que, en su lugar, esta es la comparativa que sí podemos defender — la
misma que muestra la propia landing de `whetzy.com`, construida desde
`frontend/src/lib/comparison.ts` y comprobada el `2026-09-24` (esa fecha es
una constante en el código, no una afirmación que inventamos para esta
entrada — si cambia la tabla, cambia la fecha, y hay un test que lo exige).

## Qué comprobamos, y dónde

| | Whetzy | Codecademy | Platzi | EDteam |
|---|---|---|---|---|
| Web en español | Sí | No (`codecademy.com/es` redirige a la home en inglés) | Sí | Sí |
| Plan gratuito | Sí, sin límite de tiempo | Basic, limitado | Algunos cursos gratis | 9 cursos gratis |
| Mensual (USD) | 14,99 (Pro) | 29,99 | 49 | 30 |
| Anual, al mes (USD) | Sin anual aún | 14,99 | ≈21 (249/año) | 20 (240/año) |

Cada cifra de la competencia viene de volver a descargar la página de precios
el 2026-09-24 y leer el precio en la propia estructura de datos de la página
(JSON-LD o el objeto de precios embebido) — no una captura de pantalla, no un
resumen de un agente de investigación. `docs/COMPETENCIA.md` §A.1 tiene la
cita exacta y la URL de cada celda.

## La diferencia real, no solo el precio

El precio solo no dice mucho sin saber qué se obtiene por él. Lo que creemos
que vale la pena decir sin rodeos: la ruta `/es` de Codecademy es una
redirección, no un producto en español — si "nativo en español" te importa,
lee esa fila dos veces. Platzi y EDteam sí sirven contenido en español, y no
decimos lo contrario; la diferencia que señalamos es el motor adaptativo (BKT
decide qué estás listo para aprender, FSRS programa cuándo repasarlo) frente a
una secuencia de cursos fija, y la ejecución de código en el navegador
(WebAssembly/Pyodide, sin sandbox externo) frente a IDEs embebidos que llaman
a un servidor.

## Si querés las cifras de Coursera/Udemy

Nosotros también. Cuando alguien vuelva a descargar esas páginas de precios y
lea una cifra real en ellas — no una estimación, no algo que un rastreo
automatizado no pudo traer porque lo bloquearon — esta tabla crece dos filas y
la fecha se actualiza. Hasta entonces, una comparativa a la que le faltan dos
competidores a propósito es más honesta que una que los tiene a todos con una
cifra que no podemos defender.

---

*Whetzy (whetzy.com) — aprendizaje bilingüe y adaptativo de Python a IA.
Precios según `docs/DECISIONS.md` ADR-41/49; sujetos a cambio.*
