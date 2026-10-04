---
title: "De 0 a ~11.000 preguntas: cómo construimos el banco de contenido de Whetzy"
slug: "from-0-to-10000-questions"
date: "2026-10-02"
lang: es
author: "Whetzy"
summary: "Un banco de 35 tracks y 727 habilidades no se construye con una regla de tres — y menos sin medir qué tan bueno es, no solo qué tan grande."
---

El título dice "~11.000", no "más de 10.000" como decíamos antes. Esto es por
qué cambió la cifra, y por qué contamos cómo la medimos en vez de simplemente
afirmarla.

## El recuento real, ahora mismo

```
find content/questions -name "*.json" | wc -l   # 271 ficheros
```

Sumando cada array de preguntas en esos 271 ficheros salen **10.984** preguntas,
repartidas en **35 tracks** y **727 habilidades** — y a día de hoy, **727 de
727 habilidades (100 %) tienen al menos una lección** escrita (lo imprime
nuestra propia suite de tests en cada corrida: `[lessons] 727/727 skills have
a lesson`).

Llamamos a la cifra "~11.000" y no "10.984" a propósito: es una foto de un solo
paso de `find` + `json.load` sobre el árbol de contenido, no un número que
sirva nuestro backend por API. Va a ser otro número para cuando lo leas:
se añaden tracks, se reclasifica contenido, se retiran preguntas por calidad.
Preferimos redondear hacia abajo y tener razón que redondear hacia arriba y
no tenerla.

## Por qué "cómo se contó" importa más que el número

Un banco de 10.000 preguntas con un 90 % de relleno de baja calidad es peor que
uno de 1.000 donde cada ítem de verdad distingue entre "lo sabe" y "no lo
sabe". La cantidad es la parte fácil — cualquiera genera preguntas de examen
con apariencia plausible con un LLM. El trabajo de ingeniería real fue
construir una puerta que atrape el relleno antes de que llegue a producción:

- **Un pipeline de QA de contenido** (`scripts/content_qa/`) que revisa cada
  bloque antes de darlo por terminado — no es un corrector ortográfico, es una
  revisión adversaria que busca exactamente los fallos típicos de preguntas
  escritas por un LLM (redacción ambigua, más de una respuesta correcta
  defendible, una explicación que no explica nada).
- **Piloto antes de escalar cualquier escritor.** La regla del propio
  proyecto: antes de confiar en un modelo de autoría para un bloque completo,
  corre un piloto de 10 ítems. Si más de 3 de 10 salen marcados `blocker` o
  `major`, el bloque se para y lo decide el dueño — no es hipotético, un
  piloto real falló ese umbral (7 de 10 marcadas) y se paró antes de tocar el
  banco en producción.
- **Las preguntas ejecutables se ejecutan de verdad.** Donde una pregunta
  afirma que un código se comporta de cierta manera, hay un test que ejecuta
  ese código y comprueba la afirmación — no una persona mirando el fragmento
  por encima. Las de Python corren en un subproceso de CPython, las de SQL
  contra el propio módulo `sqlite3` de CPython — los dos imitando lo que hace
  el navegador, no corriendo literalmente dentro de él. Un conjunto pequeño de
  tests de Playwright confirma, aparte, que los sandboxes reales del navegador
  (Pyodide, sql.js) de verdad inicializan y ejecutan bien.

## Qué significa esto si estás construyendo algo parecido

Si la única señal de calidad de tu pipeline de contenido es "un LLM lo escribió
y se veía bien", no tenés una señal de calidad — tenés una sensación. La
puerta tiene que ser algo que puedas señalar y decir "esta comprobación
concreta atrapó esta clase concreta de error", y tiene que ser algo que
puedas *romper a propósito* para confirmar que de verdad atrapa algo. Una
comprobación que nadie ha visto fallar nunca es una comprobación que nadie ha
verificado que funcione.

---

*Whetzy (whetzy.com) es una plataforma bilingüe y adaptativa para aprender
Python e IA. Los ejemplos de código corren en el navegador vía WebAssembly —
sin sandbox externo.*
