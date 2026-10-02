# Blog de Whetzy — convención de contenido (ledger 26.9)

Esta carpeta es el contenido del blog (`/blog` ES/EN, SEO orgánico —
`docs/AUTONOMOUS_STATE.md:256`). **Solo el contenido.** La ruta `/blog` en sí,
el prerender en `vite build` y el parser que lee estos ficheros van en
`frontend/src/pages/marketing/**`, que esta sesión no toca todavía: esas rutas
quedan reservadas hasta que el PR A de fase 0 (S5) fusione `App.tsx` — ver el
comentario `[COORD] ARRANQUE YA` del issue #89. Esto no es un bloqueo falso:
sin esas rutas registradas, cualquier componente de blog que yo escriba no
tendría dónde montarse.

## Estructura

```
content/blog/
  es/<slug>.md
  en/<slug>.md
```

Un slug, dos ficheros (uno por idioma) — igual que el resto del contenido del
repo (bilingüe nativo, nunca traducción automática, CLAUDE.md). El slug es el
mismo en los dos idiomas para que `/blog/<slug>` y `/en/blog/<slug>` apunten al
mismo artículo.

## Frontmatter (YAML) que cada fichero lleva al principio

```yaml
---
title: "Título del artículo"
slug: "mismo-slug-en-los-dos-idiomas"
date: "2026-10-02"
lang: es
author: "Whetzy"
summary: "Una o dos frases para la vista de lista y el meta-description."
---
```

- `date`: fecha de redacción, no de publicación — la publicación real (subir a
  Dev.to/Hashnode/freeCodeCamp, o que el prerender lo saque en `/blog`) es del
  dueño.
- Nada de frontmatter con cifras de engagement, vistas o comentarios: eso no
  existe todavía (línea roja — ninguna cifra inventada).

## Por qué markdown plano y no un CMS

`archive/SPEC_WEB.md:152` (histórico, no manda, pero el razonamiento sigue
siendo válido) ya apuntaba a Markdown en `content/blog/` con prerender en
`vite build` — mismo patrón que el resto del contenido del repo (lecciones,
preguntas), que vive en JSON/Markdown versionado, no en una base de datos
aparte. Un CMS externo sería una dependencia nueva (regla 4: prohibido añadir
dependencias sin que conste en «Fuera de alcance»).

## Quién escribe qué va aquí

Los 10 artículos de las filas 26.1 (ES) y 27.2 (EN) del ledger van en
`content/blog/es/` y `content/blog/en/` respectivamente. Cada título ya estaba
fijado en `docs/DISTRIBUCION.md` §8 (serie EN) antes de que yo escribiera nada
— no son títulos que haya inventado esta sesión, están citados en cada
fichero.
