# PR a EbookFoundation/free-programming-books — ledger 26.2

**Solo el texto. No abro el PR** (`docs/CONECTORES.md` §1, clase H: publicar es pregunta al dueño).

## Aviso antes de usar esto: riesgo real de rechazo

Comprobé el `CONTRIBUTING.md` de ese repo
(`raw.githubusercontent.com/EbookFoundation/free-programming-books/main/docs/CONTRIBUTING.md`,
2026-10-02): su regla es explícita — **"Please only contribute free content. Make
sure it's free"** y rechazan recursos "free for a limited period" (freemium).
Whetzy tiene plan gratuito sin límite de tiempo (bueno) **pero también** planes
de pago (Pro $14,99/mes, Pro Max $19,99/mes — ADR-41/49): es un producto
freemium, no "enteramente gratis". Los mantenedores de ese repo revisan a mano
y cierran PRs que no cumplen la letra de esa regla.

**Recomendación:** antes de abrir el PR, decidir si se presenta solo el acceso
gratuito (sin mencionar los planes de pago) — lo que algunos mantenedores
aceptan igual si el recurso principal es gratis — o si se asume el riesgo de
cierre. Esa decisión es del dueño; aquí dejo el texto listo para cualquiera de
las dos variantes.

## Dónde iría (confirmado en el repo, 2026-10-02)

`books/free-programming-books-es.md`, sección `### Python` (entre Perl 6/Raku y
Ruby en el índice alfabético del fichero). Formato exacto de cada línea en esa
sección, copiado del propio fichero:

```
* [Aprende Python](https://aprendepython.es) - Sergio Delgado Quintero (HTML, PDF) (CC BY)
```

## Línea propuesta (variante sin mencionar precio — la que más se ajusta a su regla)

```
* [Whetzy](https://whetzy.com) - academia de Python a IA con motor adaptativo (BKT+FSRS); plan gratuito sin límite de tiempo (HTML)
```

## Línea alternativa (si se decide ser transparente sobre el freemium, asumiendo el riesgo)

```
* [Whetzy](https://whetzy.com) - academia de Python a IA con motor adaptativo; plan gratuito y planes de pago opcionales (HTML)
```

## Mensaje del PR (para cualquiera de las dos variantes)

**Título:** `Add Whetzy (adaptive Python learning platform) to Python section, Spanish list`

**Cuerpo:**
> Adding Whetzy (whetzy.com), a Spanish/English adaptive learning platform for
> Python (and related tracks). It has a free tier with no time limit; code
> examples run in-browser via WebAssembly (Pyodide), no external sandbox
> required. Happy to adjust format/placement per maintainer feedback.
