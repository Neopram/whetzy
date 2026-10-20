# Capturas — 46.13, Liga y Preparación entran escalonadas

Evidencia del PR de la fila 46.13 (`docs/PLAN_UI_AVANZADA.md` §7.3 y §6.2).

**Cómo se hicieron**
- **Fecha y entorno:** 2026-10-20, Playwright (Chromium) contra el stack local, con Vite en `:5199`.
- **Datos simulados:** la clasificación de liga (siete alumnos) y la preparación (tres dominios). Una cuenta nueva no
  tiene ninguna de las dos.
- **Spec:** `frontend/e2e/liga-preparacion.spec.ts`.

**Capturas.** Se toman al terminar la entrada; las de movimiento reducido no están.
- **`liga-{es,en}-{390,1280}.png`:**
  - El podio y las filas entran escalonados.
  - La ▲ de la zona de ascenso late una vez (rangos 4 y 5; el podio no lleva flecha).
  - **No hay ceremonia de ascenso**: el servidor aún no aplica ascensos (§6.2), y el e2e comprueba que no se abre
    ningún diálogo.
- **`preparacion-{es,en}-{390,1280}.png`:** los dominios entran escalonados.

**Accesibilidad:** axe (WCAG 2.2 AA) da 0 violaciones en las dos pantallas y en los cuatro tamaños.

**Notas de captura**
- La barra de navegación aparece a media página porque es fija y la captura es de página completa.
- «Últimos 5 descienden» es el texto genérico de las reglas, aunque en los datos simulados descienda 1. Es
  anterior a este PR.
