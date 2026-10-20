# Whetzy v2 — sistema de diseño y guía de port

**Origen.** Prototipo generado en Lovable el 2026-10-01 (proyecto «Whetzy Prep»,
`4a18b84e-39fb-4fa9-a10e-4bac3c4c9c9c`) con un único mensaje, que consumió los 10 créditos
del plan gratuito. Lo que hay en `export/` es copia literal de ese proyecto, leída por MCP
(`read_file`), sin tocar. **No se compila ni se importa**: vive fuera de `frontend/` a
propósito y es la referencia para portar, no código de producción.

**Estado.** Lovable construyó: variables (oscuro y claro), componentes base, la estructura con 5
pestañas y la pantalla **Hoy**. **No** construyó Lección, Quiz, Rutas en detalle, Preparación
ni Examen (eran el mensaje 2, que no se pudo enviar por falta de créditos). Su especificación
completa está en `brief-msg2.md`: es el contrato de diseño para hacerlas a mano con este
mismo sistema.

## 1. Decisiones de marca

- **Posicionamiento:** el panel de instrumentos de tu certificación. Dominio por habilidad
  (BKT), repaso espaciado (FSRS) y preparación por dominio oficial del examen. En español
  primero. Sale de `docs/COMPETENCIA.md` §A.3.
- **Promesa:** «Afila lo que sabes. Llega listo al examen.»
- **Personalidad:** precisa, tranquila, honesta, técnica. Sin confeti y sin
  urgencias falsas (§A.4).
- **Mascota (enmienda del 2026-10-19, ADR-67 D2):** el dueño decide que sí la haya, en SVG + Lottie. Sustituye el
  «sin mascota» de esta guía. Tiene que casar con la personalidad de arriba: tranquila y técnica, no una caricatura
  ruidosa; la dibuja un ilustrador a partir de `design/mascota/BRIEF.md` y entra en la app solo con las capturas aprobadas por el dueño.
- **Color (sustituido el 2026-10-13):** la app adopta los colores del logo nuevo, decisión
  del dueño: azul noche `#0A0E1A` con el cian `#00BFFF` de acento (`design/brand/README.md`).
  Lo que sigue es el registro de la decisión anterior.
- **Color:** grafito con un único acento «chispa» `#FF7A45`, usado con moderación.
  **Prohibidos** `#58CC02`, `#1CB0F6`, `#1899D6` y `#CE82FF`, que hoy se usan como colores
  de track y como `theme-color`. Coinciden con la paleta de Duolingo; esto viene de memoria,
  no de una fuente consultada.
- **Tipografía:** Bricolage Grotesque (títulos), Inter (interfaz) y JetBrains Mono (toda
  cifra, porcentaje, temporizador y código). Las tres se autoalojan con
  `@fontsource-variable/*`, versión 5.3.0 comprobada en npm. Ninguna CDN, así que
  `check-no-third-party.mjs` sigue en verde.
- **Navegación:** 5 pestañas en vez de 7: Hoy · Rutas · Practicar · Ranking (liga y duelos)
  · Yo (perfil, estadísticas, cartera y ajustes).

## 2. Estrategia de port: primero reteñir, luego sustituir

La app actual usa `--le-*` en todo su CSS (`--le-text` 141 usos, `--le-border` 122,
`--le-brand` 98, `--le-text-muted` 94, `--le-surface` 64; contados el 2026-10-01). Por eso:

**PR 1 (≈100 líneas, sin tocar componentes):** reasignar los valores de `--le-*` en
`frontend/src/styles/design-tokens.css` a los de `export/src/styles/tokens.css`, en los dos
temas, y cambiar las fuentes. Las 28 pantallas cambian de piel de golpe. Tabla:

| Variable actual | Nuevo valor |
|---|---|
| `--le-bg` | `--bg` |
| `--le-bg-elevated` | `--surface-2` |
| `--le-surface` | `--surface` |
| `--le-border`, `--le-border-light` | `--border` |
| `--le-text` | `--text` |
| `--le-text-muted`, `--le-text-secondary` | `--text-muted` |
| `--le-brand`, `--le-brand-2`, `--le-brand-text` | `--ember` |
| `--le-brand-dark`, `--le-brand-deep` | `--button-hover` (oscuro) |
| `--le-brand-light`, `--le-brand-on-tint` | `--ember` con transparencia |
| `--le-green*`, `--le-success-*` | `--success` |
| `--le-red*`, `--le-danger*` | `--error` |
| `--le-orange*`, `--le-gold*`, `--le-warning-text` | `--attention` |
| `--le-blue*` | `--ice` / `--steel` |
| `--le-purple*`, `--le-pink`, `--le-teal` | `--steel` / `--ice` (fuera la paleta tipo Duolingo) |
| `--le-pro-card-from/to` | `--surface-2` (sin grandes manchas de acento) |
| `--le-shadow-btn*` | `none` (el botón 3D estilo Duolingo desaparece) |
| `--le-font` | `--font-body`; añadir `--font-display` |
| `--le-font-mono` | `--font-mono` |

Además: `theme.ts:20` pinta `#1CB0F6` en `meta[theme-color]`, que hay que cambiar a `--bg`
(hecho: `frontend/src/theme.ts:21` pinta `#0A0E1A`/`#F5F7FB`),
y `@fontsource-variable/nunito` sale de `package.json` en ese mismo PR (hecho).

**PR 2 en adelante:** una pantalla o flujo por PR (≤ ~500 líneas netas, regla de
`docs/CIERRE_2026-09-30.md` §2). En cada uno:
1. Se porta el componente o la pantalla desde `export/` o desde `brief-msg2.md`.
2. **En el mismo PR** se borran el `.module.css` y los componentes viejos que sustituye.
3. Pasan: `npx tsc -b`, `oxlint`, `check-bundle.mjs`, `check-no-third-party.mjs`,
   `check-prerender.mjs`, una búsqueda de `.module.css` que nadie importa, y las e2e del
   flujo tocado (`touchTargets`, `mobileNoScroll`, `accessibility`, `perf-budget`, más la
   del flujo: `quiz`, `onboarding`, `mock-exam`…).
4. Otra sesión lo verifica antes de que el dueño lo fusione (§2.5).

**Último PR:** renombrar `--le-*` a los nombres nuevos y borrar los alias.

Orden propuesto:
1. Variables.
2. Estructura: 5 pestañas, `TopBar` con racha etiquetada, y **rutas reales con
   `react-router-dom`**, que ya está en `package.json` pero se usa en 0 ficheros.
3. Hoy.
4. Rutas y detalle de ruta.
5. Lección.
6. Quiz.
7. Preparación.
8. Exámenes.
9. Yo, Cartera y Ranking.
10. Landing.

## 3. Qué hay en `export/` y cómo traducirlo

| Fichero | Uso |
|---|---|
| `src/styles/tokens.css` | Valores de los dos temas, escalas de tipo, espacio, radios y movimiento |
| `src/styles/global.css` | Base, foco visible y `prefers-reduced-motion` |
| `src/components/ui/whetzy.module.css` | Estilos de todos los componentes (ya en CSS Modules) |
| `src/components/ui/*.tsx` | `WButton`, `WCard`, `Chip`, `ProgressBar`, `ReadinessGauge`, `DomainBar`, `BottomNav`, `SideNav`, `TopBar`, `Brand`, `nav.ts` |
| `src/pages/Home.tsx` y `pages.module.css` | Pantalla Hoy, estructura y retícula de páginas |
| `src/i18n/index.tsx` | Contexto con `t()` y `pick()`. **No se porta**: la app ya usa i18next; solo se copian los textos |
| `src/fixtures/readiness.ts` | Tipo `Domain` y `readinessScore`, la fórmula de la preparación ponderada |

Traducciones:
- **Router:** el export usa `@tanstack/react-router` (lo que trae Lovable por defecto).
  En la app: `react-router-dom` (`Link`/`NavLink` con `className` activo en vez de
  `activeProps`).
- **Datos:** los fixtures llevan los nombres de campo reales de la API (comprobados el
  2026-10-01 contra `/progress/dashboard`, `/progress/curriculum`, `/content/tracks` y
  `/exams/certification/{id}/readiness`). En la app se sustituyen por los hooks de React
  Query que ya existen.
- **`readinessScore`:** Σ(weight_pct × p_known_mean) / Σ(weight_pct). Con los fixtures da 57,
  comprobado a mano (12,78 + 23,78 + 12 + 8,4 = 56,96).
- **Gauge:** arco de radio 82 con centro (100,100). El marcador del umbral del 75 % está en
  (158, 42), a 45°; comprobado.

## 4. Defectos conocidos del export, que **no** se portan tal cual

1. **Desalineado en escritorio:** `pages.module.css`, `@media (min-width:1024px)
   .nextPanel { align-self:end; }` descuadra «Siguiente paso». Usar `stretch`.
2. **La tarjeta de racha** tiene un hueco arriba. Quitar `margin-top:auto` de `.streakStats`.
3. **`TrackDetail.tsx`** (no exportado) llama a un hook dentro de `.map()`. No copiar ese
   patrón.
4. **Restos de plantilla:** en el proyecto de Lovable siguen 46 componentes shadcn (contados con `list_files`) sin
   uso y sus dependencias Radix. No se portan.
5. **404 y error del root** usan clases Tailwind de la plantilla. Rehacerlos con el sistema.
6. **`<html lang="en">`** está fijo en el shell de Lovable. En la app lo pone i18next.
7. **Placeholders:** Quiz, Lección y Preparación son vacíos (empty states). Se hacen desde
   `brief-msg2.md`.

## 5. Bugs de la auditoría que este rediseño cierra (por PR)

| Bug (auditoría 2026-10-01) | Dónde se cierra |
|---|---|
| El atrás del navegador o de Android saca de la app | PR de estructura: rutas reales con `react-router-dom`, más `@capacitor/app` para el botón atrás (el historial de pantallas ya está: #218, `frontend/src/lib/screenHistory.ts`) |
| Perfil público `/u/<handle>` 100 % inventado | PR de Yo/Ranking. El endpoint ya existe (`backend/app/api/v1/endpoints/profiles.py:35`, tras `PUBLIC_PROFILES_ENABLED`, hoy `False`) |
| Cartera muestra identificadores crudos («onboarding done», `wallet.10/month`) | PR de Yo/Cartera |
| Admin «Contenido»: paridad ES/EN, mal conectado y además stub | Fuera del rediseño (backend `admin.py:300-317` y frontend `AdminScreen.tsx:80`) |
| `/login` abre en registro, 422 sin detalle, onboarding repetido | Fuera del rediseño: PR pequeño propio |

## 6. Ficheros de esta carpeta

- `GUIA.md`: este documento.
- `brief-msg1.md`: el mensaje que se envió a Lovable, con decisiones de marca, restricciones
  y contratos de datos sintéticos.
- `brief-msg2.md`: especificación de Rutas, detalle de ruta, Lección, Quiz, Preparación y
  Examen. No se envió (sin créditos).
- `export/`: copia literal de los ficheros de Lovable descritos en §3.
