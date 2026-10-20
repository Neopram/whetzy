# Capturas — 46.14, esqueletos de carga en vez de «Cargando…»

Evidencia del PR de la fila 46.14 (`docs/PLAN_UI_AVANZADA.md` §7.4).

**Cómo se hicieron**
- **Fecha y entorno:** 2026-10-20, Playwright (Chromium) contra el backend local real.
- **Caso:** se frena `/progress/dashboard` 1,5 s y se abre Estadísticas.
- **Spec:** `frontend/e2e/esqueletos.spec.ts`.

**Capturas**
- **`esqueleto-{es,en}-{390,1280}.png`:** el esqueleto mientras llega el dato.
  - Es una línea, de la altura del texto al que sustituye.
  - Para el lector de pantalla es `role="status"` con `aria-busy` y «Cargando».
  - axe (WCAG 2.2 AA): 0 violaciones.
- **`contenido-{es,en}-{390,1280}.png`:** el contenido ya cargado.

**Lo que se midió (CLS de ese tramo)**

| Variante | CLS |
|---|---|
| `master`, con el «Cargando…» de texto | 0,003 |
| Esqueleto de tarjeta dentro de la sección | 0,072, peor que el original |
| Esqueleto de una línea (este PR) | 0,003 |

El e2e exige CLS < 0,01. Con la tarjeta restaurada como mutación falla (0,036).

**Regla que queda:**
- Dentro de una sección, donde no se sabe cuánto medirá lo que llega, el esqueleto es de una línea.
- Las formas grandes (`list`, `card`) se usan solo cuando el esqueleto ocupa la pantalla entera: ahí nada de alrededor
  se mueve.
