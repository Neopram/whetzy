# Capturas — 46.15 A, movimiento en las pantallas de entrada

Evidencia del PR de la fila 46.15, bloque A (`docs/PLAN_UI_AVANZADA.md` §7.5).

**Cómo se hicieron**
- **Fecha y entorno:** 2026-10-20, Playwright (Chromium) contra el backend local real.
- **Excepción:** verificar el correo necesita un token del buzón, así que se intercepta la respuesta de `/auth/verify-email`. La pantalla es la real.
- **Spec:** `frontend/e2e/entrada.spec.ts`.
- **axe (WCAG 2.2 AA):** 0 violaciones en todas las capturas.

**Capturas**
- **`error-{es,en}-{390,1280}.png`:** el error de entrar con una contraseña mala, tras el temblor.
  - El temblor es de nivel 0 (sin sonido), ~0,3 s.
  - Vuelve a temblar si cambia el mensaje.
  - Se anuncia con `role="alert"`.
- **`enlace-{es,en}-390.png`:** «Revisa tu correo», con el check ya dibujado.
- **`verificado-{es,en}-1280.png`:** «Correo verificado», con el check ya dibujado.
- **`alta-paso2-es-390.png`:** el paso 2 del alta.
  - Cada paso entra desplazándose (~0,2 s).
  - Solo hay entrada, sin salida: con salida, el paso nuevo esperaba a que el viejo se fuera y el toque parecía no responder. Dos tests del alta lo cazaron.

- **`prueba-puntos-es-390.png`:** la prueba de nivel tras la primera respuesta.
  - Hay un punto por pregunta respondida. El último se llena con un pulso.
  - Los puntos son decorativos (`aria-hidden`), porque «Pregunta n de 20» ya lo dice en texto.
  - El e2e exige que el punto lleno tenga color: el primer intento usaba un token que no existe (`--le-primary`) y ningún test lo veía.
  - Al terminar, el nivel en palabras (ADR-60) aparece con un desplazamiento corto. Está cubierto en vitest; no hay captura porque exige contestar las 20.

**Lo que del bloque A no se hace, y por qué**
- **Check dibujado en la tarjeta elegida del alta:** el paso avanza al tocar. Para ver el check habría que añadir una pausa a cada paso, y el alta es el camino a la primera pregunta (TTFQ). El cambio de paso ya confirma el toque.
- **Botón «enviando» sin cambiar de tamaño:** el botón ya es de ancho completo (`full`), así que el ancho no cambia. El alto no lo he medido.

**Arreglo de contraste encontrado aquí (no lo introdujo este PR)**

| Tema | `.error` en `master` (`--le-red-dark`) | Con `--le-danger-text` |
|---|---|---|
| Oscuro | 3,73:1 (falla AA) | 6,88:1 |
| Claro | 6,84:1 | 5,34:1 |

El error de Auth no llegaba a AA en oscuro; axe lo detectó al capturar.

**Movimiento reducido:** no tiembla, el check sale ya dibujado y el paso no se desplaza (último caso del spec).
