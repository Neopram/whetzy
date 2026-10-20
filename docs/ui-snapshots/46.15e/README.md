# Capturas — 46.15 E, movimiento en las pantallas de comprar

Evidencia del PR de la fila 46.15, bloque E (`docs/PLAN_UI_AVANZADA.md` §7.5).

**Cómo se hicieron**
- **Fecha y entorno:** 2026-10-20, Playwright (Chromium) contra el backend local real.
- **Spec:** `frontend/e2e/comprar.spec.ts` (3 casos).
- **axe (WCAG 2.2 AA):** 0 violaciones.

**Capturas**
- **`catalogo-es-{390,1280}.png`:** el catálogo (35 rutas) con las tarjetas ya dentro.
  - Entran escalonadas, con el retraso total recortado a `DUR.response`.
  - Con movimiento reducido no hay escalonado (tercer caso del spec).

**Checkout: el éxito solo con el servidor (sin captura)**
- El check se dibuja cuando el servidor confirma el plan: fase `active`, tras sondear `/auth/me` o el acceso a la certificación.
- Que Paddle diga `checkout.completed` no basta: «Activando…» no lleva check.
- En local no se puede recorrer, porque hace falta Paddle y aquí no está configurado (la página dice que el pago no está disponible). Lo cubre `comprar46.test.tsx` con el evento de Paddle simulado y el sondeo real del componente:
  - sin confirmación, no hay check;
  - con confirmación, sí;
  - la mutación «check también en activando» sale en rojo.

**Lo que el plan pedía y no se hace**
- **«La tarjeta del plan elegida se eleva»:** el checkout no ofrece tarjetas que elegir (el plan llega en la URL) y el catálogo no elige una tarjeta, abre una ruta. Las tarjetas de planes están en la landing y en Perfil, fuera de este bloque.

**Encontrado al hacerlo**
- **El escalonado de `Stagger` (#298) no tenía tope.** Con 35 tarjetas y 0,04 s entre cada una, la última tardaba 1,4 s en empezar a entrar. axe medía tarjetas a medio aparecer: colores mezclados de 1,27 a 4,16:1, cuando el token da 7,24:1.
- Se arregló en #298: `staggerFor(count)` recorta el total a `DUR.response`, con su test, y las capturas de 46.15 D se rehicieron.
