# Cuarentena de contenido

Lo que hay aquí **no** lo carga `content_loader` ni lo mide
`check_question_bank.py`: los dos escanean `content/questions/**` y esta
carpeta queda fuera a propósito. No se borra nada; simplemente no se publica.

## track24_pentest y track25_cloud_security (2026-09-19, sesión bj)

800 preguntas que no pasan la puerta de calidad de `CATALOGO_MAESTRO.md` §7.
Medido, no opinado:

| | track24 | track25 | tracks legítimos |
|---|---|---|---|
| enunciados distintos | 14/400 (4 %) | 14/400 (4 %) | 86-100 % |
| opciones de una sola palabra | 95 % | 95 % | 0-56 % |
| ejecutables sin código que ejecutar | 80/80 | 80/80 | — |

«¿Qué es HTTPS?» aparece 41 veces en track24; «¿Qué es SIEM?» 45 veces en
track25. Uno de los enunciados es literalmente `SELECT`. Los temas tampoco
corresponden: hay preguntas de criptografía básica dentro de un módulo de
reconocimiento de pentest.

El origen fue de coordinación, no de modelo: **tres agentes duplicados**
generaron los mismos ficheros y se pisaron entre ellos. El tercero rebalanceó
las posiciones de respuesta, con lo que `check_question_bank` llegó a dar
`PASS` — y ese PASS es justo lo que motivó ampliar el guardia, que ahora mira
también si la pregunta dice algo.

**Para recuperarlos hay que reescribirlos**, no moverlos de sitio: enunciados
propios por skill, distractores defendibles y código real en los ejecutables.
Las skills sk2401xx–sk2505xx y las entradas de `tracks.json` se quitaron con
ellos.
