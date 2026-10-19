# Capturas — 46.1, la respuesta del quiz sin tapar el código

Evidencia del PR de la fila 46.1 (`docs/PLAN_UI_AVANZADA.md` §2 y §6.2). Capturas
del 2026-10-18 con Playwright (Chromium) contra el stack local (Postgres 16 +
Redis, backend en `:8000`, Vite en `:5199`), con una cuenta registrada de cero
en cada una y la pregunta `q010101001` («¿Cuál es un nombre de variable válido
en Python?») forzada como en `e2e/accessibility.spec.ts`. Se responde bien
(«_my_var») y se captura a 400 ms, con la animación en marcha.

- `feedback-{es,en}-{390,1280}.png`: la tarjeta de respuesta. La animación de
  Lottie (36 px) va en la esquina superior derecha de la tarjeta, fuera del
  flujo: antes era un overlay fijo de 160 px en el centro de la pantalla que
  tapaba la pregunta y el código 1,4 s. Medido en las cuatro: la animación cae
  dentro de la tarjeta y se solapa 0 px con el texto de la explicación.

axe (WCAG 2.2 AA) sobre la respuesta del quiz: 0 violaciones
(`e2e/accessibility.spec.ts`, «quiz answer feedback has zero violations»).
