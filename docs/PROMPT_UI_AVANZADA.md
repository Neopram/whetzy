# Prompt — Serie 46 «Experiencia avanzada» para la sesión «Progreso del proyecto y oportunidades de mercado»

> Texto que el dueño pega en esa sesión. Spec: `docs/PLAN_UI_AVANZADA.md`. Se guarda aquí para que
> quede trazable qué se pidió y cuándo (2026-10-17), como `docs/archive/PROMPT_SINCRONIZACION_DOCS.md`.
> Cuando la serie 46 esté cerrada, este fichero pasa a `docs/archive/`.

---

Orden del dueño, 2026-10-17. Lee `docs/PLAN_UI_AVANZADA.md` entero (es corto) y después
`docs/PLAN_EXPERIENCIA.md` §1–§2 y `docs/SESIONES.md` §3–§4.1. Vas a ejecutar la serie 46 y las filas
40.1–40.6 de la serie 40 con esas reglas. Si este prompt y `CLAUDE.md` o `SESIONES.md` dicen cosas
distintas, mandan ellos y lo anotas en el PR.

## Orden de trabajo

1. Termina **45.4** y abre su PR como tenías previsto. La serie 46 empieza después, con una sola
   excepción: **46.0** (dieta del ledger y alta de las filas 46.x) puede ir ya en un worktree aparte.
2. Después, ola por ola, en el orden del plan: 46.2 (+ 46.2b) → 46.1b → 46.1 → 46.3 → 46.7 → **pregunta D1–D4** →
   40.1 → 40.2 → 40.3/40.4 → 40.5 → 40.6 → 46.4 → 46.5 → 46.6. Dentro de una ola puedes paralelizar
   filas que no compartan ficheros; entre olas, no.
   La ceremonia de ascenso de liga queda bloqueada hasta que el servidor aplique ascensos;
   anótalo como fila H.<n> si no existe (`PLAN_UI_AVANZADA.md` §6.2).
3. La serie 44 (`PLAN_BACKOFFICE.md`) no la mezcles con la 46 en el mismo worktree ni en la misma
   rama; si el dueño te la pide, va en su propio worktree y en PRs separados.

## Aislamiento (para no chocar contigo mismo ni con otras sesiones)

- Un worktree por fila en tu scratchpad: `wt-46N` o `wt-40N`. Rama `claude/serie-46-N-<slug>` o
  `claude/serie-40-N-<slug>`, creada desde `origin/master` recién traído. Nunca dos filas en el mismo
  worktree.
- `git fetch origin master && git merge origin/master` antes de cada push. Un PR por fila, ≤ ~400
  líneas; si una fila no cabe, se parte en `N-a`, `N-b` con sus propios PRs.
- **Ficheros vedados hasta que 45.1–45.4 estén en `master`** (la 45 los toca):
  `frontend/src/pages/AuthScreen.tsx`, `pages/LandingScreen.tsx`, `App.tsx`, `i18n.ts`,
  `i18n/{es,en}/common.json`, `services/api.ts`, `stores/useAppStore.ts`, `pages/DuelScreen.tsx`,
  `e2e/duel.spec.ts`, `e2e/correoAlta.spec.ts`, `backend/app/api/v1/endpoints/auth.py`,
  `endpoints/oauth.py`, `services/email.py`, `core/cookies.py`, `docs/API.md`,
  `docs/MAPA_PRODUCTO.md`, `docs/RUNBOOK.md`. Si una fila los necesita (40.1 necesita `api.ts`),
  espera a la fusión y entonces `git merge origin/master` primero.
- **i18n:** las cadenas nuevas van a `frontend/src/i18n/{es,en}/producto.json` (tu namespace), nunca
  a `common.json` mientras tengas un PR de la 45 abierto. `legal.json`, `motor.json`, `contenido.json`
  y `marketing.json` no se tocan: si una fila necesita un cambio ahí, va en «Fuera de alcance».
- **Compartidos** (`SESIONES.md` §3): `frontend/package.json` + lockfile, `scripts/ci_local.sh`,
  `.githooks/**` solo en PRs propios y mínimos (46.2b, 46.5b), listados en «Fuera de alcance».
- **Ledger:** lo editas tú, como con la 45, pero en commits `ledger: …` separados y siempre tras
  `git merge origin/master`. Antes del push: `python scripts/ledger.py fases --write`,
  `python scripts/ledger.py check`, `python scripts/check_docs.py`. Hoy quedan 475 B de margen
  (60.965 de 61.440): por eso 46.0 va primero y sin ella no se añade ninguna fila.
- **Contenido:** `content/**` no se toca (ADR-62) hasta D1. `frontend/src/widgets/**` es tuyo
  (`SESIONES.md` §4.1).

## Puertas (ninguna se salta; `--no-verify` no existe)

- Hook de nivel 1 en cada push; nivel 2 en tu cola (`l2seq.sh`), y su veredicto antes de dar una fila
  por `DONE`.
- Por fila, lo que dice su criterio en el plan, más: `node scripts/check-bundle.mjs`,
  `check-prerender.mjs`, `check-no-third-party.mjs` (desde `frontend/`), e2e a 390 y 1280 px, axe 0
  en las pantallas tocadas, y capturas ES/EN en `docs/ui-snapshots/<fila>/` con un README como el de
  `docs/ui-snapshots/design-v2/README.md` (qué muestra cada captura, con datos reales).
- Una guarda nueva se muta en rojo antes de aceptarla y se restaura (regla de estilo de `CLAUDE.md`).
- Evidencia pegada en el PR: salida real de los comandos, no un resumen.

## Decisiones del dueño (D1–D4 del plan §4)

Al cerrar 46.3 y antes de tocar 40.1, pregúntalas **en un solo mensaje**, con la consecuencia de
cada opción en una línea. No asumas ninguna. Hasta la respuesta, puedes adelantar en 40.1 solo lo que
no depende de ellas (esquema, checkers en servidor, tests).

## Informe

- Al cerrar cada fila, cinco líneas: fila, PR, evidencia (comando y resultado), lo que no se hizo y por
  qué, siguiente paso.
- Ninguna frase «mejor que Brilliant / Duolingo / Kodree» en landing, listing, docs públicas ni en el
  PR hasta que 46.6 cierre 40.13 con su tabla.
- Si algo del plan resulta falso contra el código (una ruta, una línea, un supuesto), lo corriges en
  `docs/PLAN_UI_AVANZADA.md` en el mismo PR y lo dices en «Fuera de alcance»; no lo ejecutas tal cual.
