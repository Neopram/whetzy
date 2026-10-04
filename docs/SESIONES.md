# Sesiones en paralelo — mapa de terrenos (S1–S6)

> Nace el 2026-10-02 en la **fase 0** (S5). Numeración y ramas: las del dueño en el
> [issue #89](https://github.com/Neopram/whetzy/issues/89), que es además el **bus de
> coordinación** (las sesiones en la nube no pueden escribirse entre sí). Si este fichero y el
> #89 dicen cosas distintas, manda el #89; sobre *quién escribe qué fichero*, manda este.
> `CLAUDE.md` manda sobre los dos.

## 0. Por qué existe

Lo que rompió GitHub hasta el 2026-10-02: fusionar en rojo, Dependabot subiendo majors sin
puerta (bcrypt 5, typescript 7, redis 8) y sesiones paralelas editando los mismos ficheros
(ledger, i18n, migraciones). Un fichero = un dueño; lo compartido lo integra una sola sesión (S5).

## 1. Quién es quién y cuándo arranca

| Sesión | Rol | Rama asignada | Fichero de textos |
|---|---|---|---|
| S1 | Full stack | `claude/loving-galileo-60vp6g` | `producto.json` (y la única que edita `common.json`) |
| S2 | Contenido y certificaciones | `claude/pensive-ride-ddce6s` | `contenido.json` |
| S3 | Matemático del motor | `claude/loving-fermi-oow6if` | `motor.json` |
| S4 | Abogado y cumplimiento | `claude/vibrant-carson-iult4i` | `legal.json` |
| S5 | Fundador-ingeniero (fase 0) e integrador (fase 2) | `claude/sleepy-faraday-fhfmd3` | — |
| S6 | Marketing y crecimiento | `claude/ecstatic-meitner-2x08pf` | `marketing.json` |
| COORD | Coordinación y autoría masiva de contenido (ADR-59) | `claude/youthful-allen-i8k7zb` y `-<trackNN>` | — (terreno en §4.2) |

**Arranque:** por decisión del dueño (comentario `[COORD] ARRANQUE YA` del #89, 2026-10-02
21:45 UTC) S1–S4 y S6 trabajan ya sobre `origin/master`. Lo único que esperan al PR A de la
fase 0 son sus ficheros: S1, `frontend/src/App.tsx`, `frontend/src/i18n.ts`,
`frontend/src/test/i18n.parity.test.ts` y `producto.json`; S4, `legal.json`; S6,
`frontend/src/pages/marketing/**` y `marketing.json`. Cada sesión trabaja en su rama de la
tabla, puesta al día con `git merge origin/master`, con un PR por tema.

## 2. De dónde sale este mapa

Los terrenos de §4 son los de cada prompt, copiados del comentario `[COORD] → S5` del #89
(2026-10-02). Si el prompt de una sesión y este fichero dicen cosas distintas, manda su prompt:
lo anota en su PR y S5 corrige este fichero.

## 3. Ficheros compartidos — solo los edita S5

```
docs/AUTONOMOUS_STATE.md   docs/STATUS.md        docs/CHANGELOG.md     docs/DECISIONS.md
docs/archive/**            CLAUDE.md             docs/README.md
frontend/package.json      frontend/package-lock.json
backend/requirements*.txt  Dockerfile
.github/**                 .githooks/**
scripts/ci_local.sh        scripts/ledger.py     scripts/check_docs.py
```

**Compartido de solo-añadir:** `docs/INVENTARIO_DOCS.md`. Quien cree un `.md` nuevo bajo `docs/`
(fuera de `archive/`) añade **una línea** con su clase, porque `check_docs.py` [12] exige que cada
doc esté en `docs/README.md` o aquí; no edita ni borra líneas ajenas. Dos PRs que añaden líneas
distintas se fusionan sin conflicto o con uno trivial que resuelve S5.

**Excepción: las líneas de cifras del banco** (`[COORD] DESBLOQUEO` del #89). `check_docs.py`
exige que las cifras del banco cuadren en ficheros compartidos: la fila `Contenido` de
`docs/AUTONOMOUS_STATE.md` ([2]) y las cifras de `frontend/src/lib/catalog.ts` ([4]) y de
`docs/ARCHITECTURE.md` ([5a]). **El PR de contenido que cambia el banco (S2, o la sesión coordinadora desde ADR-59) regenera esas líneas**,
y solo esas, a partir del banco real, y las lista en «Fuera de alcance». Si dos PRs de contenido
las tocan, el segundo hace `git merge origin/master` tras fusionarse el primero, las regenera y
repite el nivel 2; nunca se edita a mano la cifra de otro PR.

**Excepción: las líneas del HEAD de Alembic** (`[COORD]` del #89, 2026-10-03 00:04). `check_docs.py`
[1] exige que el HEAD y el número de migraciones cuadren con `backend/alembic/versions/` en tres
líneas: «HEAD actual» de `CLAUDE.md`, la fila «Alembic HEAD» de `docs/AUTONOMOUS_STATE.md` y
«Current Alembic HEAD» de `docs/RUNBOOK.md`. **El PR que trae una migración actualiza esas tres
líneas**, y solo esas, y las lista en «Fuera de alcance»; sin ellas su `check_docs.py` sale con
5 ✗ y el nivel 1 lo para. Como las migraciones se fusionan de una en una (§5), el siguiente PR con
migración, tras `git merge origin/master`, apunta su `down_revision` a la cabeza nueva, sube el
número en uno y repite el nivel 2.

Las demás sesiones proponen sus cambios a estos ficheros en su PR: el ledger, en la sección
**«Delta del ledger»** (`ID | estado nuevo | commit | comando ejecutado | salida real`); el resto,
en **«Fuera de alcance»** con el fichero exacto y el cambio. S5 re-ejecuta cada comando citado
antes de aplicarlo; si no se reproduce, no lo aplica. Tras tocar filas corre
`python scripts/ledger.py fases --write`: la tabla de `## 1` se genera desde las filas, y
`ledger.py check` y `check_docs.py` [14] fallan si no cuadra.

## 4. Terrenos

### 4.1 S1 — full stack

```
frontend/src/**  salvo: frontend/src/i18n/{es,en}/{contenido,motor,legal,marketing}.json,
                        frontend/src/pages/marketing/**
frontend/src/i18n/{es,en}/common.json      (la ÚNICA sesión que lo edita) y producto.json
frontend/src/App.tsx                       (tras la fase 0)
frontend/src/widgets/**                    (ampliado por [COORD] en el #89: 40.1/40.2)
frontend/.env.production                   (paso 2 del dominio propio de la API, #101)
backend/app/api/v1/endpoints/**  salvo los del motor, la newsletter y lo legal; sus tests
backend/app/core/cookies.py                (excepción aceptada por [COORD] para el #101;
                                            el resto de backend/app/core/** sigue siendo de S5)
migraciones: con la regla de §5 (19.11, moderación, lleva una)
```

### 4.2 S2 — contenido y certificaciones

```
content/**  salvo content/blog/** y content/legal/**
backend/tests/content/**   scripts/content_qa/**   scripts/metas_catalogo.json
docs/CATALOGO_MAESTRO.md   frontend/src/i18n/{es,en}/contenido.json
scripts/question_diversity_baseline.json   (la línea base de la guarda de contenido)
docs/ARCHITECTURE.md                       (solo sus cifras del banco: excepción de §3)
```

**Desde el 2026-10-03 (ADR-59):** la autoría nueva en masa (serie 37, 39.8) la lleva la
sesión coordinadora con `Workflow`, según `docs/PLAN_CONTENIDO.md`, en ramas
`claude/youthful-allen-i8k7zb-<trackNN>`. S2 cierra sus PRs en curso y las correcciones
puntuales del banco, y no abre autoría masiva. Un track tiene un solo dueño a la vez: el que
tenga PR abierto sobre él.

### 4.3 S3 — matemático del motor

```
los módulos del motor (BKT, FSRS, DKT, placement): S3 declara la lista exacta con grep en su
primer commit; incluye backend/app/services/ai/rag.py y
backend/tests/integration/test_rag_self_retrieval.py (39.32)
docs/ml/**   sus tests   frontend/src/i18n/{es,en}/motor.json
```

### 4.4 S4 — abogado y cumplimiento

```
docs/legal/**   content/legal/**   frontend/src/i18n/{es,en}/legal.json
```

### 4.5 S5 — fundador-ingeniero e integrador

Todos los ficheros compartidos de §3, más:

```
backend/app/core/**
backend/scripts/start.sh
frontend/scripts/check-deployed.mjs
frontend/src/i18n.ts                       (el cargador)
frontend/src/i18n/{es,en}/{producto,contenido,motor,legal,marketing}.json   (solo crearlos vacíos)
frontend/src/App.tsx                       (solo en la fase 0, para las rutas reservadas; después es de S1)
docs/RUNBOOK.md
docs/SESIONES.md
```

### 4.6 S6 — marketing y crecimiento

```
content/blog/**   docs/distribucion-assets/**   store/**   frontend/src/pages/marketing/**
frontend/src/i18n/{es,en}/marketing.json
un endpoint NUEVO de newsletter con su test (si lleva migración, regla de §5)
```

Lo que no aparece en ninguna lista no tiene dueño: quien lo necesite lo pide con
`[S<n>] NECESITO` en el #89.

## 5. Migraciones de Alembic

1. Antes de crear una, lista los PRs abiertos y sus ficheros
   (`gh api repos/Neopram/whetzy/pulls?state=open`, o el conector de GitHub) y los `MIGRACIÓN`
   del #89. Si **alguno** toca `backend/alembic/versions/`, no crees la tuya: comenta `BLOQUEO`
   y sigue con otra cosa.
2. Al abrirla, comenta en el #89 `[S<n>] MIGRACIÓN: abro una en #<PR>`.
3. Como máximo **una** migración por PR, siempre con `alembic revision`; nunca `create_all`.
4. `alembic heads` muestra **una** cabeza antes del push.
5. El título del PR lleva **«[MIGRACIÓN]»**. En la cola de fusión (la mantiene S5 en el #89) van
   primero los PRs con migración y después los que dependen de ellos, uno cada vez: Railway
   despliega cada fusión.

## 6. Textos de interfaz

- Cada sesión escribe solo `frontend/src/i18n/{es,en}/<su fichero>.json` (§1), en ES y EN nativos.
- Cada fichero es un **namespace propio** de i18next, no se mezcla en `common`: dos sesiones con
  la misma clave se pisarían en silencio. Uso: `useTranslation('marketing')` o
  `t('marketing:hero.title')`.
- `frontend/src/test/i18n.parity.test.ts` exige, fichero a fichero, las mismas claves en los dos
  idiomas y ningún valor vacío, y que cada fichero de rol esté registrado en `src/i18n.ts`.

## 7. Antes de cada push (todas las sesiones)

1. Lee los `MIGRACIÓN` y `AVISO` abiertos del #89.
2. `git fetch origin && git merge origin/master` (nunca rebase de una rama ya empujada).
3. Por cada PR abierto de otra sesión: `git merge-tree --write-tree HEAD origin/<su-rama>`.
   Código distinto de 0 o `CONFLICT` en la salida ⇒ no empujes; lista los ficheros y para.
4. Nivel 1: `git config core.hooksPath .githooks` (config local: repítelo en cada clon).
5. Nivel 2 (regla 7d enmendada en el #89): se puede empujar tras el nivel 1 **solo con el PR en
   borrador**. En la nube, el hook con `WHETZY_NIVEL2=gestionado` no lo lanza al fondo; córrelo tú
   como tarea en segundo plano **gestionada** (límite ≥ 60 min):
   `bash scripts/ci_local.sh --sha <sha>` sale 0 si VERDE y 1 si ROJO (`WHETZY_PYTHON` elige el
   intérprete). Solo con VERDE: «Listo para revisión» y `[S<n>] LISTO: #<PR> — nivel 2 VERDE (<sha>)`
   en el #89. `--estado` da el último veredicto y distingue uno que murió sin terminar. Un `nohup`
   desde un shell que se cierra muere con él y deja «CORRIENDO».
   **Varios PRs a la vez:** un carril por PR, `bash scripts/ci_local.sh --carril pr96 --sha <sha>`
   (y `--carril pr96 --estado`). Sin carril, el cerrojo del checkout mata al nivel 2 anterior: eso
   fue el `exit 137` del #96. Con carriles distintos no se tocan (cerrojo, bitácora y worktree
   propios). `XDG_CACHE_HOME` distinto solo separa el worktree, no el cerrojo.
6. **Ruta nueva o con otra protección** (I.6/J.13): `cd backend && python -m app.core.authz --write`
   y el diff de `backend/tests/authz_matrix.json` va en el PR. Sin eso, el nivel 1 para el push
   (`tests/test_authz_matrix.py`). Una ruta `admin` nueva la prueba sola el test: un alumno con
   sesión tiene que recibir 401 o 403.

## 8. PRs

Uno por tema y pequeño. Secciones: Qué · Por qué (filas del ledger) · Evidencia (comandos y salida
real) · Riesgos al desplegar · Delta del ledger · Fuera de alcance · Solo el dueño. El único check
que cuenta es **«Cloudflare Pages»**; los jobs de Actions mueren sin runner (H.13) y no son ni
fallo ni aprobado. Al abrirlo: `[S<n>] ENTREGADO: <qué> — #<PR>` en el #89. Solo el dueño
fusiona (ADR-45).
