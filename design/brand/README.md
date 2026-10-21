# Marca de Whetzy — logo y colores

**Origen.** Lámina de logo que aportó el dueño el 2026-10-13 (un SVG de 1200 × 1200 con el
logo grande, el icono de app y las versiones a color y monocroma). El dueño decidió ese mismo
día que **la app adopta los colores del logo** (opción «B»): sustituyen a la «chispa» `#FF7A45`
de `design/v2/GUIA.md` §1. Lo demás de esa guía (tipografía, navegación, tono) sigue vigente.

## Colores

| Uso | Valor |
|---|---|
| Fondo de la app (oscuro) | `#0A0E1A` |
| Fondo del icono de app | `#0D1525` |
| Acento principal (CTA, foco, «zy» del logo) | `#00BFFF` · en claro `#0072B5` |
| Degradado del símbolo | `#00BFFF` → `#7B68EE` → `#C71585` → `#FF1493` |
| Punto | `#FF1493` |
| Texto del logo sobre blanco | `#1A1A2E` |

En la interfaz se usan por sus tokens (`frontend/src/styles/design-tokens.css`), nunca como literales. `test/tokens.contraste.test.ts` fija
el contraste AA de cada pareja en los dos temas. El blanco sobre el cian se queda en
2,12:1, así que el texto sobre un relleno de marca va en `--le-text-inverse` (oscuro).

## Ficheros

| Fichero | Para qué |
|---|---|
| `whetzy-mark.svg` | Símbolo a color, sin fondo (fondos oscuros) |
| `whetzy-mark-mono.svg` | Símbolo en una tinta (fondos claros, impresión) |
| `whetzy-app-icon.svg` | Icono de app: fondo a sangre, símbolo centrado en la zona segura del 80 % |
| `whetzy-adaptive-foreground.svg` | Primer plano del icono adaptativo de Android (círculo seguro del 61 %) |
| `whetzy-favicon.svg` | Favicon simplificado para 16-32 px (sin brillos ni líneas de velocidad) |
| `whetzy-logo-{dark,light,mono}.png` | Logo horizontal, 1200 × 300 |

Cambios frente a la lámina original: el símbolo del icono estaba descentrado (30 px a la
izquierda, 75 a la derecha en una caja de 220) y ahora queda centrado; el favicon es una
versión simplificada porque a 16 px el original era una mancha; y el nombre se dibuja con
Inter (la tipografía de la interfaz, autoalojada) en vez de con la Arial que tenga cada equipo.

## Regenerar los PNG

Desde `frontend/`: `node scripts/generate-icons.mjs`. Dibuja con Chromium, desde estos SVG,
el favicon, los iconos PWA, la imagen para compartir (`og-image.png`), los iconos y pantallas
de arranque de Android, los iconos de las tiendas y los logos horizontales. Si la versión de
Playwright no coincide con el Chromium instalado, `CHROME_PATH=<ruta> node scripts/generate-icons.mjs`.
