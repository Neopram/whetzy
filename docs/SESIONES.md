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

**Arranque de S1–S4 y S6:** este fichero está en `origin/master` **y** S5 ha comentado en el #89
`[S5] FASE 0 FUSIONADA`. Cada sesión trabaja en su rama de la tabla, puesta al día con
`git merge origin/master`, con un PR por tema.

## 2. Estado de este mapa — léelo antes de fiarte de §4

- **S5 (§4.5): exacto**, copiado de su prompt.
- **S1–S4 y S6: PROPUESTA de S5, sin contrastar.** S5 no tiene los prompts de las otras cinco;
  los globs salen de la estructura del repo y del rol de cada una en el #89. Que `common.json`
  sea de S1 es una inferencia: las Reglas de hierro dicen «la sesión 2» con la numeración vieja,
  en la que la sesión 1 era la de fase 0 (hoy S5) y los ficheros de rol venían en el orden
  producto, contenido, motor, legal, marketing. **Si el prompt de una sesión dice otra cosa,
  manda su prompt**: lo anota en su PR y S5 corrige este fichero.

## 3. Ficheros compartidos — solo los edita S5

```
docs/AUTONOMOUS_STATE.md   docs/STATUS.md        docs/CHANGELOG.md     docs/DECISIONS.md
docs/archive/**            CLAUDE.md             docs/README.md
frontend/package.json      frontend/package-lock.json
backend/requirements*.txt  Dockerfile
.github/**                 .githooks/**
scripts/ci_local.sh        scripts/ledger.py     scripts/check_docs.py
```

Las demás sesiones proponen sus cambios a estos ficheros en su PR: el ledger, en la sección
**«Delta del ledger»** (`ID | estado nuevo | commit | comando ejecutado | salida real`); el resto,
en **«Fuera de alcance»** con el fichero exacto y el cambio. S5 re-ejecuta cada comando citado
antes de aplicarlo; si no se reproduce, no lo aplica.

## 4. Terrenos

### 4.1 S1 — full stack (PROPUESTA)

```
frontend/src/i18n/{es,en}/common.json      (la ÚNICA sesión que lo edita)
frontend/src/i18n/{es,en}/producto.json
frontend/src/pages/*.tsx, frontend/src/pages/*.css   (salvo LegalScreen*, DeleteAccountScreen*)
frontend/src/components/**, frontend/src/hooks/**, frontend/src/stores/**, frontend/src/styles/**
frontend/src/services/api.ts, backend/app/api/**, backend/app/schemas/**, backend/app/models/**
backend/alembic/versions/**                (con la regla de §5)
docs/MAPA_PRODUCTO.md, docs/PLAN_EXPERIENCIA.md, docs/design/**, docs/API.md
```

### 4.2 S2 — contenido y certificaciones (PROPUESTA)

```
content/**                                 (salvo content/economy/**)
scripts/content_qa/**, scripts/check_question_bank.py, scripts/catalog_coverage.py,
scripts/metas_catalogo.json, scripts/check_content_sources.py, scripts/check_source_licenses.py
backend/tests/content/**
frontend/src/i18n/{es,en}/contenido.json
docs/CATALOGO_MAESTRO.md
```

### 4.3 S3 — matemático del motor (PROPUESTA)

```
backend/app/services/engine/**, backend/app/services/{quiz,placement,progress,mock_exam,track_exam,lesson_gate,mastery_report,dkt}.py
backend/app/ml/**
frontend/src/i18n/{es,en}/motor.json
docs/ml/**
```

### 4.4 S4 — abogado y cumplimiento (PROPUESTA)

```
docs/legal/**
frontend/src/pages/LegalScreen*, frontend/src/pages/DeleteAccountScreen*
frontend/src/i18n/{es,en}/legal.json       (las claves `legal.*` de common.json siguen en common:
                                            moverlas es cosa de S1, ADR-55)
scripts/check_legal_facts.py
```

### 4.5 S5 — fundador-ingeniero e integrador (exacto)

Todos los ficheros compartidos de §3, más:

```
backend/app/core/**
backend/scripts/start.sh
frontend/scripts/check-deployed.mjs
frontend/src/i18n.ts                       (el cargador)
frontend/src/i18n/{es,en}/{producto,contenido,motor,legal,marketing}.json   (solo crearlos vacíos)
frontend/src/App.tsx                       (solo para dejar las rutas reservadas)
docs/RUNBOOK.md
docs/SESIONES.md
```

### 4.6 S6 — marketing y crecimiento (PROPUESTA)

```
frontend/src/pages/marketing/**            (rutas reservadas: /es/carrera, /en/career,
                                            /es/empresas, /en/enterprise, /blog)
frontend/src/i18n/{es,en}/marketing.json
docs/DISTRIBUCION.md, docs/distribucion-assets/**, docs/COMPETENCIA.md, docs/competitive-teardown.md
```

**Sin dueño en esta propuesta** (quien lo necesite lo pide con `[S<n>] NECESITO` en el #89):
el resto de `backend/app/services/**`, `backend/tests/**` fuera de contenido,
`docs/ARCHITECTURE.md`, `docs/ECONOMIA.md`, `content/economy/**`.

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
5. Nivel 2: `bash scripts/ci_local.sh` como tarea en segundo plano **gestionada** (límite ≥ 60
   min) y espera su veredicto. Un `nohup` desde un shell que se cierra muere con él y deja
   «CORRIENDO» sin veredicto.

## 8. PRs

Uno por tema y pequeño. Secciones: Qué · Por qué (filas del ledger) · Evidencia (comandos y salida
real) · Riesgos al desplegar · Delta del ledger · Fuera de alcance · Solo el dueño. El único check
que cuenta es **«Cloudflare Pages»**; los jobs de Actions mueren sin runner (H.13) y no son ni
fallo ni aprobado. Al abrirlo: `[S<n>] ENTREGADO: <qué> — #<PR>` en el #89. Solo el dueño
fusiona (ADR-45).
