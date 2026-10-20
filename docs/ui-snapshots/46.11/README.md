# Capturas: 46.11, la llama de la racha en tres tamaños y el escudo del comodín

Evidencia del PR de la fila 46.11 (`docs/PLAN_UI_AVANZADA.md` §7.3).

**Cómo se hicieron**
- **Fecha y entorno:** 2026-10-20, Playwright (Chromium) contra el stack local: Postgres 16 + Redis, backend en `:8000` y Vite en `:5199`.
- **Datos:** cuenta nueva en cada caso; la racha y el escudo se fijan desde el store de desarrollo.
- **Spec:** `frontend/e2e/racha-llama.spec.ts`. Las capturas son solo de la barra superior.
- **Qué no prueba:** que el servidor gaste el comodín. Eso lo cubren los tests de `_update_streak` y `_fx_events`.

**Capturas**
- **`llama-{3,12,45}-{es,en}-{390,1280}.png`:** un tramo por captura. 1–6 días: 16 px, sin brillo. 7–29: 20 px, con brillo. ≥ 30: 24 px, con doble brillo. El número y su etiqueta no cambian.
- **`escudo-{es,en}-{390,1280}.png`:** el día que el servidor gasta un comodín, un escudo cubre la llama durante 600 ms. El lector de pantalla oye «Comodín usado: tu racha sigue».

**Accesibilidad:** axe (WCAG 2.2 AA) da 0 violaciones en las cuatro.
