# Capturas — 46.7b, resumen de sesión con recuento

Evidencia del PR de la fila 46.7b (`docs/PLAN_UI_AVANZADA.md` §6.0, nivel 3, y
§6.2, «Resumen»). Capturas del 2026-10-19 con Playwright (Chromium) contra el
stack local (Postgres 16 + Redis, backend en `:8000`, Vite en `:5199`). Cada
juego es una cuenta registrada de cero que contesta desde la interfaz una
sesión de 10 preguntas (la primera opción, o «No lo sé»), así que las notas son
bajas: es lo que pasó, no un decorado.

- `recuento-es-390.png`, `recuento-es-1280.png`, `recuento-en-390.png`: a los 0,35 s de abrir el resumen. Los
  aciertos, la precisión y los XP van contando; «Saltar recuento» está arriba
  y la nota todavía no se ha estampado.
- `final-es-390.png`, `final-es-1280.png`, `final-en-390.png`: el mismo resumen al terminar (≈ 1,4 s): la
  nota estampada, los números finales y sin botón de saltar.
- `final-es-390-reducido.png`: con `prefers-reduced-motion: reduce` no hay
  recuento ni botón; los números y la nota salen quietos desde el principio.

`e2e/resumen-recuento.spec.ts` comprueba que «Saltar recuento» aparece al abrir
el resumen, que al pulsarlo la nota queda puesta y que axe (WCAG 2.2 AA) da 0
violaciones en el resumen ya terminado. axe no se pasa con el recuento en
marcha: tarda más que los 1,4 s que dura.
