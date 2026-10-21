# Capturas: landing, ola 2 (banderas, ancho y datos estructurados)

Evidencia del primer PR de landing de la ola 2 (2026-10-21).

**Cómo se capturaron.** Playwright (Chromium) contra `vite` en local, el 2026-10-21, en
`/landing?lang=es`. `antes-*` es `master` (`4389cde`) y `despues-*` es esta rama. La cabecera va
con el tema oscuro y el claro; el hero, solo con el oscuro. Todo a 1440 y a 390 px.

**Lo que cambia en `despues-*`:**
- **Banderas.** El selector de idioma dibuja las banderas en SVG; antes eran los emoji 🇪🇸 y 🇬🇧.
  - En este Chromium de Linux los emoji sí se ven, así que `antes-*` no muestra el fallo.
  - El fallo era en Windows, que no trae glifos de bandera y enseña las letras sueltas. Es
    comportamiento conocido de Windows, no reproducido aquí.
  - El selector dice además cuál está activo (`aria-pressed`).
- **Ancho.** Los contenedores pasan de 72rem (1152 px) a 80rem (1280 px). Medido a 1440 px: el
  bloque del hero mide 1152 px en `antes` y 1280 px en `despues`. A 390 px no cambia.
- **Datos estructurados.** schema.org en JSON-LD, en el HTML pre-renderizado: Organization, WebSite
  y SoftwareApplication, con las ofertas Gratis, Pro y Pro Max.
  - Los precios salen de `plans.ts`, que `backend/tests/test_constantes_planes.py` ata a
    `app/core/prices.py`.
  - Sin valoraciones ni recuentos: no hay datos reales con que darlos.
  - Creador no sale, porque su precio no se publica en la landing (D-7).
- **Tabla comparativa.** A 390 px se desplaza en horizontal. Ahora recibe el foco (`tabIndex=0`,
  `role="region"`) para que el teclado también llegue.

**axe (WCAG 2.2 AA):**

| | 1440 px | 390 px |
|---|---|---|
| `antes` | 0 | 1 (`scrollable-region-focusable`, la tabla) |
| `despues` | 0 | 0 |

Las dos columnas cubren los temas oscuro y claro. Sin scroll horizontal en ningún caso.
