# Capturas — 46.7, ceremonia al cerrar la sesión

Evidencia del PR de la fila 46.7 (`docs/PLAN_UI_AVANZADA.md` §6.0 y §6.4).
Capturas del 2026-10-18 con Playwright (Chromium) contra el stack local
(Postgres 16 + Redis, backend en `:8000`, Vite en `:5199`), con insignias y
misiones sembradas por `python -m app.services.seed` y una cuenta registrada de
cero que contesta **desde la interfaz** una sesión de 10 preguntas acertando
todas (la clave sale del contenido, como en `e2e/gamification.spec.ts`).

Nada está inventado: el servidor concedió en esa sesión dos insignias
(«Primer Dominio» y «Perfeccionista») y las mandó en `events[]` (46.1b).

- `ceremonia-es-{390,1280}.png`: al cerrar la sesión sale UNA ceremonia
  («Nueva insignia: Primer Dominio») con «Saltar»; se cierra sola a los 3 s.
- `resumen-es-{390,1280}.png`: el resumen tras la ceremonia; la otra insignia
  sale como tarjeta quieta en «También en esta sesión».

axe (WCAG 2.2 AA) con la ceremonia abierta: 0 violaciones.
