# "Show HN" en español — ledger 26.6

**Nota antes de usar esto:** Hacker News no tiene una sección en español ni acepta
posts en español en "Show HN" — es una comunidad en inglés (lo confirma su propio
FAQ: https://news.ycombinator.com/newsfaq.html, "the site is in English"). Por eso
26.6 no es "publica esto en HN en español": es la misma historia (por qué existe
Whetzy, por qué en español) adaptada para las comunidades donde SÍ tiene sentido
publicarla en español — Reddit hispano (r/devsarg, r/MexicoDev, r/spain cuando
proceda), foros de Dev.to en español, Discord/Telegram de programación LATAM
(`docs/DISTRIBUCION.md` §5.1). Publicar bajo cualquier cuenta es "Solo el dueño"
(H.45); esto es el kit, no un envío.

## Título corto (para Reddit / foros con límite de título)

```
Construí un motor de aprendizaje adaptativo de Python→IA en español porque nadie más lo hizo
```

## Post completo

> Hola. Soy el único desarrollador detrás de **Whetzy** (whetzy.com), una plataforma
> de aprendizaje adaptativo de Python a IA. La parte del "por qué en español": la
> educación tech adaptativa de verdad (no solo cursos en video — motor que decide
> qué repasas y cuándo, como Duolingo pero para programación) casi siempre nace en
> inglés y trata el español como una traducción después, cuando llega a existir.
> Hispanohablantes somos ~500 millones y no encontré nada construido nativo en
> español (no traducido con IA) con un motor adaptativo real debajo.
>
> Por dentro: BKT (Bayesian Knowledge Tracing) decide qué estás listo para
> aprender, FSRS programa los repasos para que no se te olvide, y los ejemplos de
> código (Python, SQL, JS) corren en el navegador vía WebAssembly (Pyodide/sql.js)
> — sin ida y vuelta a un servidor para ejecutar un fragmento.
>
> Es gratis (el plan free tiene un cupo diario de preguntas). Me interesa de
> verdad qué piensa la comunidad: dónde está flojo el espacio de aprendizaje
> adaptativo en español, qué le pedirías a una plataforma "en serio" que un
> bootcamp o una serie de YouTube no te da, y dónde se rompe si la probás.
> Respondo lo que sea sobre el motor, el contenido bilingüe o la economía de
> construir esto solo.

## Cuándo

Mismo criterio que la versión EN (`show-hn/en.md`): martes o miércoles, evitando
fin de semana (tráfico bajo en foros técnicos en general). Para Reddit hispano
específicamente, horario tarde CET / mañana en LATAM suele solapar mejor con
ambas franjas horarias — supuesto de planificación, no medido.

## Qué no hacer

Igual que la versión EN: nada de pedir upvotes/karma coordinado (viola las reglas
de Reddit y de la mayoría de foros, y se detecta), nada de cifras inventadas en
el post ni en las respuestas — si un número no está en este repo con su cita, no
se dice.

## Checklist antes de publicar

- [ ] Confirmar en qué subreddit/foro concreto se publica (cada uno tiene sus
      propias reglas de autopromoción — revisar antes, no asumir)
- [ ] whetzy.com/es carga limpio, alta y onboarding sin errores
- [ ] El dueño disponible para responder comentarios las primeras horas
