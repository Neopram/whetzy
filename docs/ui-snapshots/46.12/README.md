# Capturas — 46.12, Hoy cuenta desde la última visita

Evidencia del PR de la fila 46.12 (`docs/PLAN_UI_AVANZADA.md` §7.3).

**Cómo se hicieron**
- **Fecha y entorno:** 2026-10-20, Playwright (Chromium) contra el stack local (Vite en `:5199`).
- **Datos:** las respuestas de progreso y de misiones se simulan, porque una cuenta nueva no tiene skills dominadas.
  La foto de la visita anterior se escribe en `localStorage`, tal como la dejaría Hoy.
- **Spec:** `frontend/e2e/hoy-contadores.spec.ts`. La lógica de la foto tiene sus tests de componente.

**Qué se comprueba (e2e)**
- Las misiones cuentan desde 0 (`data-from="0"`) hasta «1/2».
- Python cuenta sus skills dominadas desde 3 hasta 6/32, y su icono hace un toque (`data-fx="tap"`).
- JavaScript no cambió, así que ni cuenta ni late.
- La banda de «Variables» subió de «En desarrollo» a «Fuerte», y la etiqueta nueva entra animada.

**Capturas:** `final-{es,en}-{390,1280}.png`, el estado al terminar el recuento (dura 600 ms). No hay capturas a
mitad del recuento: una foto a 250 ms ya salía terminada y no se presenta como lo que no es. axe (WCAG 2.2 AA): 0
violaciones en las cuatro.

**Notas de captura**
- El «Elo: 1500» de «Tu territorio» solo existe en desarrollo (ADR-60, `import.meta.env.DEV`). La captura viene del
  servidor de desarrollo; en producción no sale.
- La barra de navegación aparece a media página porque es fija y la captura es de página completa.
