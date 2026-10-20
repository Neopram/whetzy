# Capturas — 46.15 C, movimiento en las pantallas de competir

Evidencia del PR de la fila 46.15, bloque C (`docs/PLAN_UI_AVANZADA.md` §7.5).

**Cómo se hicieron**
- **Fecha y entorno:** 2026-10-20, Playwright (Chromium) contra el backend local real.
- **Spec:** `frontend/e2e/competir.spec.ts` (4 casos).
- **axe (WCAG 2.2 AA):** 0 violaciones en todas las capturas.

**Capturas**
- **`reloj-urgente-es-{390,1280}.png`:** examen final de ruta con el reloj ya en los 5 últimos minutos.
  - Al cruzar esa raya el reloj late una vez. No suena: avisa, no asusta.
  - El color y el texto ya avisaban antes, y con movimiento reducido siguen avisando.
  - Para no esperar 70 minutos, el e2e adelanta solo `expires_at` en la respuesta de empezar.
- **`veredicto-es-{390,1280}.png`:** entregado en blanco, el servidor dice «No aprobado».
  - El veredicto entra con efecto y la sesión se cierra con un efecto de nivel 3 (`session_end`), una sola vez.
  - El simulacro hace lo mismo (cubierto en vitest).
- **`duelo-desenlace-es-390.png`:** duelo real de dos jugadores, desde quien termina segundo.
  - El servidor ya tiene el resultado y el desenlace entra con efecto.
  - Quien termina primero ve «Cuando tu oponente termine…», sin efecto: aún no hay nada que celebrar.

**Lo que el plan pedía y no se hace, y por qué**
- **Duelo, «barra del rival en vivo» y «anillo de cuenta atrás»:** los duelos son asíncronos (cada uno juega cuando puede) y no tienen reloj. Ninguna respuesta del servidor da el progreso del rival en vivo, así que pintarlo sería inventarlo.
- **Navegador de preguntas con puntos:** ya existe (cuadrícula de respondidas, marcadas y pendientes en `ExamSitting`).
- **Contar la nota como en el resumen:** `CountUp` vive en #273 (46.7b), aún sin fusionar. Contarla aquí exige ese componente; queda para cuando se fusione, con su test.

**Encontrado al hacerlo (del e2e, no de la app)**
- El primer intento adelantaba el reloj con `page.clock`.
- Ese reloj falso también lleva `requestAnimationFrame`, y las entradas de framer se quedaban a medias: las capturas salían vacías.
- axe midió colores mezclados con la opacidad (3,0–3,6:1) que no existen en la app: los tokens dan 9,16:1 y 7,24:1.
