# Capturas — 46.3c, primer minuto: prueba de nivel y «Tu mayor palanca»

Evidencia del PR de la fila 46.3c (`docs/PLAN_UI_AVANZADA.md` §2, ola 1, y §6.2).
Capturas del 2026-10-19 con Playwright (Chromium) contra el stack local
(Postgres 16 + Redis, backend en `:8000`, Vite en `:5199`). Cada juego es una
cuenta registrada de cero que en el onboarding elige «Certificarme», Seguridad y
redes (track13) e ISC2 CC (track40), en ES y en EN, a 390 y 1280 px.

- `onboarding-prueba-{es,en}-{390,1280}.png`: el último paso del onboarding
  presenta la prueba de nivel con lo que mide y cuánto dura («20 preguntas de
  Ciberseguridad, unos 10 minutos…»). Ese texto ya existía desde 43.3; aquí
  solo se comprueba que se ve sin scroll.
- `hoy-nuevo-{es,en}-{390,1280}.png`: Hoy recién llegado, sin ninguna respuesta
  en la certificación. No hay palanca: lo primero sigue siendo «Siguiente paso»
  (la lección). Practicar en ese momento devolvía `needs_lesson` y llevaba a
  «Empieza por la lección» (medido en local).
- `hoy-palanca-{es,en}-{390,1280}.png`: la misma cuenta tras ver una lección y
  contestar una pregunta de ISC2 CC. «Tu mayor palanca · ISC2 CC» es la primera
  tarjeta de Hoy, con el mismo cálculo que Preparación.

`e2e/primer-minuto.spec.ts` recorre lo mismo a 390 px: prueba de nivel a la
vista, Hoy sin palanca y con ella, y axe (WCAG 2.2 AA) en Onboarding y en Hoy:
0 violaciones.
