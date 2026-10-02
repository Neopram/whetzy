# PR a jwasham/coding-interview-university y donnemartin/system-design-primer — ledger 27.3

**Solo el texto. No abro ningún PR.**

## Hallazgo antes de redactar: los dos repos no encajan igual

Comprobé la estructura real de los dos repos (2026-10-02, lectura directa de sus
`README.md`), no asumí que ambos tuvieran una sección "añade tu plataforma aquí":

- **`jwasham/coding-interview-university`** sí tiene un sitio razonable: la
  sección "Coding Problems" ya lista plataformas de práctica con freemium/pago
  (LeetCode, HackerRank, TopCoder) una debajo de otra, con nombre + link + una
  frase. Whetzy encaja ahí en formato, aunque su contenido (Python general,
  certificaciones cloud, IA) no es específicamente "preparación de entrevistas
  de algoritmos" — es un ajuste parcial, no perfecto.
- **`donnemartin/system-design-primer`** NO tiene una sección de "recursos
  generales" ni "plataformas de aprendizaje". Su única sección de enlaces
  externos es "Additional system design interview questions": una tabla de
  preguntas concretas («Design a file sync service like Dropbox») cada una con
  enlaces a artículos sobre ESE diseño específico. No hay sitio natural para
  "Whetzy" ahí sin forzarlo.

**Recomendación: no abrir el PR a `system-design-primer`.** Forzar un enlace
genérico en una lista de preguntas específicas es justo el patrón que los
mantenedores de listas curadas cierran como fuera de tema, y gastaría la
atención del maintainer sin necesidad. Si el dueño quiere intentarlo igual, el
texto de abajo (versión "genérica") sirve, pero el riesgo de cierre es alto.

## PR a `coding-interview-university` — texto propuesto

**Dónde:** sección "Coding Problems" del `README.md`, siguiendo el mismo formato
que las entradas existentes.

**Línea propuesta** (mismo estilo que `- [LeetCode](https://leetcode.com/)` +
una frase):

```
- [Whetzy](https://whetzy.com)
    - Adaptive Python + cloud/AI certification prep (BKT + FSRS engine); not interview-specific, but useful for the Python fundamentals this list assumes going in.
```

**Título del PR:** `Add Whetzy to Coding Problems (Python fundamentals + cert prep)`

**Cuerpo del PR:**
> This isn't an interview-algorithm site specifically — it's adaptive Python
> fundamentals + cloud/AI certification practice (AWS, Microsoft, ISC2). Adding
> it here because a chunk of this repo's audience is shoring up Python basics
> before the algorithm grind, and the adaptive engine (BKT+FSRS) means it
> doesn't re-quiz what you already know. Totally fine if this isn't the right
> fit for this list — happy to close if so.

> La última frase es a propósito: es honesto decir que puede no encajar, en vez
> de vender el ajuste como perfecto cuando no lo es.

## Texto genérico para `system-design-primer` (solo si el dueño decide intentarlo
igual, con el riesgo ya dicho arriba)

No hay una sección donde insertarlo sin crear una nueva. Si se insiste, la única
opción no forzada sería proponer una nueva entrada en una sección de "recursos
generales" que el repo no tiene hoy — eso ya es un cambio estructural al README
de otro proyecto, no una línea añadida, y los mantenedores de listas curadas con
miles de estrellas casi nunca aceptan reestructurar su propio documento a
petición de un tercero. No he escrito un texto de PR para esto porque no hay un
lugar honesto donde ponerlo.
