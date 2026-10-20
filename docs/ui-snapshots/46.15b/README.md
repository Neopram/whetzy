# Capturas — 46.15 B, movimiento en las pantallas de aprender

Evidencia del PR de la fila 46.15, bloque B (`docs/PLAN_UI_AVANZADA.md` §7.5).

**Cómo se hicieron**
- **Fecha y entorno:** 2026-10-20, Playwright (Chromium) contra el backend local real.
- **Spec:** `frontend/e2e/aprender.spec.ts` (6 casos).
- **axe (WCAG 2.2 AA):** 0 violaciones, salvo lo que se dice abajo del editor.

**Capturas**
- **`copiado-es-390.png`, `copiado-en-1280.png`:** el ejemplo de la lección, tras pulsar «Copiar código».
  - El e2e lee el portapapeles y comprueba que contiene el código mostrado.
  - «Copiado» es texto con `role="status"`. Si el navegador no deja copiar, dice «No se pudo copiar».
- **`rutas-sube-es-{390,1280}.png`:** Rutas tras una subida de banda.
  - El módulo lo avisa aunque esté cerrado.
  - Abierto, la banda de la skill que subió («En desarrollo») late una vez.
  - **Excepción al backend real:** subir de banda pide 7 respuestas. Para no contestarlas, se suben los intentos de una skill en la respuesta de `/progress/curriculum`. El resto de la respuesta es la del servidor.
- **`proyecto-pasa-es-390.png`:** proyecto SQL sembrado, con el paso 1 bien.
  - El servidor ejecuta los tests y lo acepta; el aviso entra con efecto y se emite el acierto (nivel 1).
  - Si el servidor lo rechaza, no hay ni efecto ni aviso (vitest).

**Decisiones**
- **Una foto de bandas por pantalla.** Con una sola, la de Hoy, la pantalla que se abriese primero se comería la subida y la otra no la vería nunca. Rutas guarda la suya; Hoy conserva su clave de siempre.
- **«Desde la última visita» es entre sesiones.** Volver a Rutas desde Hoy no la remonta (la pantalla sigue viva), así que el e2e lo prueba recargando.
- **Lección:**
  - El plan pedía secciones que aparecen al hacer scroll (IntersectionObserver). La lección real va por pasos, sin scroll, y cada paso ya entra con movimiento: no hay secciones que observar.
  - Se hace la otra mitad: copiar el ejemplo.
- **Playground no tiene tests:** solo ejecuta. «Ejecutar» lleva `aria-busy` mientras corre, igual que en Proyecto.
- **Proyecto no tiene una lista de tests que escalonar.** El servidor da un sí o un no por paso. Lo que se anima es ese veredicto, y solo cuando es sí.

**Encontrado al hacerlo**
- **Mi regresión, corregida antes del PR:** la primera captura de Rutas a 390 px mostraba la banda caída de su sitio. La regla `.skill > [data-band]` ya no alcanzaba la banda envuelta; el envoltorio tiene ahora su propia alineación.
- **Del editor, no de este bloque:** el tema `vs-dark` de Monaco pinta las cadenas en `#ff0000` sobre `#1e1e1e` (4,16:1, por debajo de AA). El caso de Proyecto excluye `.monaco-editor` de axe por eso. Queda para arreglar aparte, con un tema propio del editor.
