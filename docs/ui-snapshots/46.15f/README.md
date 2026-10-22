# Capturas — 46.15 F, cierre del movimiento (rehacer la tabla de §7.5)

Evidencia del cierre de la fila 46.15 (`docs/PLAN_UI_AVANZADA.md` §7.7: «la serie se cierra al rehacer la tabla
de §7.5 contra el código, con capturas»).

**Cómo se hicieron**
- **Fecha y entorno:** 2026-10-21, Playwright (Chromium) a 390 px, en español, contra el backend local real
  (base de datos nueva, migrada y con el contenido cargado) y el servidor de desarrollo de Vite.
- **Spec:** `frontend/e2e/capturas-46-15f.spec.ts` (3 casos). Solo comprueba que cada pantalla carga y deja
  la imagen; el comportamiento de cada bloque lo afirman sus propios specs (`aprender`, `competir`, `comprar`…).
- **Simulado con `page.route`:** la verificación del correo, el cambio de contraseña y el certificado público,
  porque en local no hay un correo verificado ni un examen aprobado con código válido.

**Capturas (`<pantalla>-es-390.png`)**
- **A. Entrada:** `auth`, `onboarding`, `verificar` (check dibujado), `restablecer-formulario` y
  `restablecer-exito` (check dibujado nuevo en esta serie).
- **Páginas sueltas de §7.4:** `landing` y `estado`, ya con la transición de eje.
- **Con sesión:** `hoy`, `rutas`, `perfil`, `stats`, `cartera`, `liga`, `duelo`, `playground`, `marketplace`.
- **E. Comprar:** `checkout` (sin Paddle configurado, la página dice que el pago no está disponible) y
  `certificado-publico`.

**Lo que no está y por qué**
- **Prueba de nivel, Lección, Proyecto, Simulacro, Examen de ruta, Preparación:** hacen falta una ruta o un
  examen elegidos en el estado de la app. Con `setScreen` desde fuera salían en blanco o en la pantalla de
  carga, así que se quitaron en vez de dejar una captura engañosa. Los cubren los specs de sus bloques.
- **Olvidé mi contraseña, Informe de dominio, Perfil público:** sin captura aquí; los dos últimos necesitan un
  código público válido.
- **Estados que el servidor tiene que dar:** insignia nueva, sello del certificado, check del checkout; salen
  en las capturas de 46.15 D y E.
- **Tipografías:** el servidor de desarrollo de este entorno no servía las fuentes de `node_modules`
  (enlazado fuera del proyecto), así que las capturas llevan la tipografía de respaldo.

**Encontrado al hacerlo**
- **Restablecer no tenía confirmación visible:** tras el cambio esperaba un segundo y redirigía sin decir nada.
  Ahora muestra el check dibujado y «Contraseña cambiada.» (`resetPassword.success`) hasta el redirect.
- **La ceremonia contaba doble en desarrollo:** `StrictMode` montaba el efecto dos veces y `fx_emitted` salía
  duplicado. Con una guarda y su test, sale una vez.
- **«Saltar recuento» del resumen no se medía:** no llamaba a `trackFxSkipped`; ahora emite `fx_skipped`
  del nivel 3 (`session_end`).
