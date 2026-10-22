# Capturas — 46.4, un solo sistema de tokens

Evidencia del PR de la fila 46.4 (`docs/PLAN_UI_AVANZADA.md` §7.5). Se migraron a `--le-*` los 10 ficheros
CSS que seguían con el sistema viejo (`theme/tokens.css`) y se borró ese fichero y su `@import`.

**Cómo se hicieron**
- **Fecha y entorno:** 2026-10-21, Playwright (Chromium) contra el servidor de desarrollo, ES, 390 px, tema oscuro y claro.
- **Sin backend:** la API se simula con `page.route`; el reloj no importa (no hay cifras vivas en estas pantallas).
- **«Antes»:** el commit base `4389cde` (con `theme/tokens.css`). **«Después»:** esta rama.
- **Pantallas:** las que pintan los ficheros migrados y se pueden abrir sin cuenta de pago:
  - `landing` (`LandingScreen.module.css`);
  - `onboarding` (`styles/onboarding.css`);
  - `playground` (`PlaygroundScreen.module.css` y `MonacoCodeEditor.module.css`);
  - `perfil-publico`, `/u/ana` (`PublicProfileScreen.module.css`);
  - `ui-kit`, la sección TabsNav de `/_ui` (`TabsNav.module.css`).
- **Sin captura:** `AdminScreen` (necesita 2FA del dueño), `DistributionBanner` y `ResponsiveTable` (ninguna pantalla los monta hoy) y `PlacementScreen` (dos variables, sin cambio de valor).

**Qué cambió a la vista y por qué (comparación por píxeles de cada pareja)**
- **`landing`:** 32 y 36 píxeles distintos (diferencia máxima de 4 y 15 sobre 255), en un punto animado del distintivo. Es movimiento, no color.
- **`playground`:** idéntico en oscuro. En claro solo cambia el botón principal, que dice «Cargando runtime…» o «Ejecutar» según si el runtime de Python llegó a cargar durante la captura (en esta máquina, sin red, depende del momento). No es CSS.
- **`onboarding`:** solo las esquinas de la tarjeta (el radio pasa de 18 a 16 px, que es el `--le-radius-lg`). Ningún color cambia.
- **`perfil-publico`:** las tres tarjetas ganan el borde que el CSS siempre pidió. Usaban `--color-border`, una variable que **nunca existió**, y con una variable sin definir la declaración `border` entera se descartaba: hasta hoy no había borde. Ahora es `--le-border`. Es el único cambio visible a propósito.
- **`ui-kit` (TabsNav):** idéntico píxel a píxel en los dos temas.

**Tabla de equivalencias (el detalle completo está en la descripción del PR)**
- **Idénticas en los dos temas:** `--color-primary` → `--le-brand`, `--color-accent` → `--le-blue`, `--color-error` → `--le-red`, `--bg-dark` → `--le-bg`, `--bg-dark-secondary` → `--le-surface`, `--text-primary/secondary/tertiary/inverse` → `--le-text`/`-secondary`/`-muted`/`-inverse`, `--border-color` → `--le-border`, y las escalas `--space-*` y `--radius-md/xl/full`.
- **Token nuevo:** `--bg-dark-tertiary` → `--le-surface-2` (oscuro #172038, claro #E9EDF5; `--le-bg-elevated` en claro es blanco y habría cambiado la cabecera de tabla, la pestaña y la tarjeta de perfil).
- **Aproximadas:** `--radius-lg` 18 px → `--le-radius-lg` 16 px; `--transition-fast` y `-normal` (curva `cubic-bezier`, 150 y 250 ms) → `--le-transition-fast` (150 ms) y `--le-transition-base` (200 ms).
- **Variables que no existían:** `--color-border`, `--color-primary-dark`, `--transition-base`, `--transition-slow` y `--glow-cyan` (valor «sin halo»). Se resolvieron a `--le-border`, `--le-brand-deep` (el banner, con texto blanco a 5,3:1), `--le-transition-base` y `--le-transition-slow`; el halo vacío se quitó.

**Guardas**
- `src/test/tokens.contraste.test.ts` cubre los pares nuevos (texto sobre `--le-surface-2`, marca y rojo como glifo, blanco sobre `--le-brand-deep`, el placeholder de Monaco) en los dos temas.
- Mutada en rojo: con `--le-surface-2` claro en #6A7590 fallan 3 casos; restaurado, 79 verdes.
- `grep -rl "var(--color-" frontend/src` → nada.
