# Capturas: rediseño de /checkout

Evidencia del PR del rediseño del checkout (plan de Paddle, tarea 3, 2026-10-21). Antes, la página
solo mostraba un título, el aviso de renovación, la casilla legal y «Ir al pago». No decía qué se
compraba ni cuánto costaba, y un fallo de Paddle salía con su código crudo.

**Cómo se capturaron.** Playwright (Chromium) contra `vite` en local, el 2026-10-21. `antes-*` es
`master` (`4de1ca9`) y `despues-*` es esta rama. La API (`/auth/me`, `/billing/paddle/config`) y
Paddle.js están simulados en la propia captura, porque la cuenta de Paddle aún no cobra (dominio en
revisión). Cada página se capturó en ES y EN, con el tema oscuro y el claro, a 390 y a 1280 px.

**Lo que cambia en `despues-*`:**
- Resumen del plan: nombre, precio, periodicidad, frase y ventajas. Salen de `landing.planPro` y
  `landing.planProMax`, los mismos textos que la landing. Sus precios los vigila
  `backend/tests/test_constantes_planes.py`, que ahora también lee el formato español «14,99 $».
- Selector Pro / Pro Max: cambia `?plan=` y el precio que se abre en Paddle.
- Botón con el importe: «Pagar 14,99 $ al mes».
- Debajo del botón: cancelar desde Perfil, enlace a la política de reembolsos y quién cobra (Paddle).
- Si el error es `transaction_checkout_not_enabled`, el aviso sale en palabras y el código queda
  plegado. Esto lo cubre `src/test/checkout.rediseno.test.tsx`; no tiene captura.

axe (WCAG 2.2 AA) a 390 px: 0 violaciones en las ocho combinaciones de `antes` y `despues`.
