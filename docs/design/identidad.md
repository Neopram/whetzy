# Identidad visual — guía de tokens (24.1)

Documenta lo que el código tiene HOY, no un rediseño nuevo. Fuente de verdad:
`frontend/src/styles/design-tokens.css` (namespace `--le-*`, canónico desde la
serie 34 — paleta "Obsidian", ADR-47). No narrativa RPG, no plantilla genérica.

## Dos ficheros de tokens, uno canónico

`frontend/src/theme/tokens.css` (namespace `--color-*`, `--bg-dark-*`,
`--text-*`, `--border-color`) es anterior a `design-tokens.css` y sigue en uso
en algunos ficheros (`LandingScreen.module.css`, `PlaygroundScreen.module.css`
y 8 más — `grep -rl "var(--color-" frontend/src --include="*.module.css" | wc -l`
da 10; `--le-*` da 67). Ambos se cargan siempre (los dos entran por
`src/styles/global.css`), así que no hay bug de runtime, pero es deuda de identidad:
un componente nuevo debe usar `--le-*`; no se ha migrado el resto por ser un
cambio grande fuera del alcance mecánico de 24.1 (quitar colores hex
literales), que sí está cerrado.

## Color

Tema por defecto: **oscuro** (`:root` en `design-tokens.css`, sin
`[data-theme]`). El claro vive en `:root[data-theme="light"]`, solo si el
usuario lo pide — antes era al revés y la landing (oscura, cian) y la app
(clara, azul cielo) parecían dos productos distintos.

- **Marca:** `--le-brand` (cian `#00BFFF`) para CTAs, hero, logo, acentos.
  `--le-brand-text` para texto/glifos (el fill no pasa AA como texto).
- **Éxito:** `--le-green`/`--le-success-text` — significa solo acierto,
  nunca otra cosa (línea roja).
- **Superficies:** `--le-bg`, `--le-bg-elevated`, `--le-surface`,
  `--le-border`/`--le-border-light` — todas cambian con el tema.
- **Texto:** `--le-text`, `--le-text-secondary`, `--le-text-muted`,
  `--le-text-inverse` (esta última se INVIERTE con el tema — casi negro en
  oscuro, blanco en claro; no vale para un fondo que no sigue el tema, ver
  «Colores fijos» abajo).
- **Semántico:** `--le-danger`/`--le-danger-text`, `--le-warning-text`,
  `--le-orange`, `--le-gold`, `--le-purple`, cada uno con variante `-dark`/
  `-light`/`-on-tint` cuando hace falta un par con contraste AA verificado
  (`src/test/tokens.contraste.test.ts`, mutado en rojo antes de
  aceptarlo — vigila la regresión real de 2026-09-20: cuatro combinaciones a
  1.08–2.75:1 de contraste en producción).

### Colores fijos (no siguen el tema, a propósito)

Un puñado de superficies deben verse igual en claro y oscuro: el logo de un
lenguaje de programación no cambia de azul porque el usuario cambie de tema.
Viven en el bloque `:root` de `design-tokens.css` sin redefinirse en
`[data-theme="light"]` (o en `theme/tokens.css` si el componente ya usaba ese
namespace):

- `--brand-python`, `--brand-sql`, `--brand-js`/`--brand-js-bg` — identidad
  de marca de terceros (`ProjectScreen.module.css`).
- `--le-code-bg`/`--le-code-text` — editor de código, siempre oscuro como
  Monaco/VS Code (`LessonScreen.module.css`).
- `--editor-loading-bg`/`--editor-loading-text` (namespace `theme/tokens.css`)
  — placeholder de Monaco mientras carga (`PlaygroundScreen.module.css`).
- `--le-pro-card-from`/`--le-pro-card-to` — tarjeta "Pro" con `!important`
  (`ProfileScreen.module.css`).
- La palabra clave CSS `white`/`black` (no un token) cuando el texto va
  siempre sobre un relleno de color fijo — mismo caso, sin necesidad de un
  token nuevo (p. ej. `WhyButton.module.css`, `EvidenceScreen.module.css`).

## Tipografía

Inter para la interfaz (`--le-font`), Bricolage Grotesque para títulos
(`--le-font-display`) y JetBrains Mono para cifras y código (`--le-font-mono`),
autoalojadas en `global.css`. Escala en `--le-fs-*`
(`xs`→`xl`), peso en `--le-fw-*` (`bold`, `black`).

## Espaciado y radios

`--le-space-*` (`xs` a `xl`, base 8px) y `--le-radius-*` (`sm`/`md`/`lg`/
`full`). `--le-nav-height`, `--le-topbar-height`, `--le-max-width` fijan el
layout de la app (no de la landing, que tiene su propio `landing.css`).

## Modo oscuro

Por defecto (ver «Color»). `prefers-reduced-motion` se respeta en las
transiciones (`--le-transition-*`) donde el componente lo comprueba — no es
un token, es una media query por componente.

## Guarda anti-regresión

`src/test/tokens.noLiterals.test.ts` (24.1, 2026-09-28): recorre todos los
`.module.css` y falla si aparece un color hex fuera de un comentario.
Mutado en rojo (color de prueba reinyectado) antes de aceptarlo. Antes de
esta fila: 6 de 51 ficheros con hex literal (88,2 %, bajo el 90 % del
criterio); ahora 0 de 51 (100 %).

## Pendiente (no lo cubre esta fila)

- Consolidar `theme/tokens.css` en `design-tokens.css` (deuda documentada
  arriba, cambio grande, no mecánico).
- Aprobación del dueño registrada — este documento describe el sistema
  actual; no sustituye esa firma.
