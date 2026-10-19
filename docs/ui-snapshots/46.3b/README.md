# Capturas — 46.3b, momentos de Hoy

Evidencia del PR de la fila 46.3b (`docs/PLAN_UI_AVANZADA.md` §6.2). Capturas del
2026-10-18 con Playwright (Chromium) contra el stack local (Postgres 16 + Redis,
backend en `:8000`, Vite en `:5199`), con las misiones sembradas por
`python -m app.services.seed` (las mismas plantillas que producción) y una cuenta
registrada de cero que contesta una sesión de 10 preguntas
(`registerAndCompleteAQuiz` de `e2e/helpers.ts`) y vuelve a Hoy.

- `hoy-mision-es-{390,1280}.png`: «Misiones del día». «Responde 10 preguntas»
  pasó de pendiente (foto tomada al entrar en Hoy recién registrada) a completa:
  lleva el check que se dibuja (300 ms) y sonó una vez por `lib/feedbackFx`.
  Medido en el mismo recorrido: 1 check al volver del quiz y 0 tras recargar.

axe (WCAG 2.2 AA) sobre Hoy: 0 violaciones (`e2e/accessibility.spec.ts`,
«home screen has zero violations after login»).
