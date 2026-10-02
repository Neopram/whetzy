# Sesiones en paralelo — mapa de terrenos

> Nace el 2026-10-02 en la **fase 0** (sesión 1, plataforma). Mientras este fichero no esté en
> `master`, ninguna de las sesiones 2-6 arranca. Cuando una regla de aquí choque con `CLAUDE.md`,
> manda `CLAUDE.md`; sobre *quién escribe qué fichero*, manda este.

## 0. Por qué existe

Lo que rompió GitHub hasta el 2026-10-02: fusionar en rojo, Dependabot subiendo majors sin
puerta (bcrypt 5, typescript 7, redis 8) y sesiones paralelas editando los mismos ficheros
(ledger, i18n, migraciones). Un fichero = un dueño; lo compartido lo integra una sola sesión.

## 1. Estado de este mapa — léelo antes de fiarte de §3

- **Sesión 1 (§3.1): exacto**, copiado del prompt de la sesión 1.
- **Sesiones 2-6 (§3.2-§3.6): PROPUESTA de la sesión 1, sin contrastar.** La sesión 1 no tiene
  los prompts de las otras cinco; los globs salen de la estructura del repo y del nombre de cada
  fichero de idioma creado en la fase 0. **El dueño los sustituye por los de cada prompt** antes
  de lanzar las sesiones 2-6 (o confirma que coinciden). Hasta entonces, si el prompt de una
  sesión y esta tabla dicen cosas distintas, manda su prompt y la sesión lo anota en su PR.

## 2. Ficheros compartidos — solo los edita la sesión 1

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
en **«Fuera de alcance»** con el fichero exacto y el cambio. La sesión 1 re-ejecuta cada comando
citado antes de aplicarlo y, tras tocar filas, corre `python scripts/ledger.py fases --write`
(la tabla de `## 1` se genera; `ledger.py check` y `check_docs.py` [14] fallan si no cuadra).

## 3. Terrenos

### 3.1 Sesión 1 — fundador técnico, plataforma e integración (exacto)

Todos los ficheros compartidos de §2, más:

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

### 3.2 Sesión 2 — producto (PROPUESTA)

```
frontend/src/i18n/{es,en}/common.json      (la ÚNICA sesión que lo edita)
frontend/src/i18n/{es,en}/producto.json
frontend/src/pages/*.tsx, frontend/src/pages/*.css   (salvo LegalScreen*, DeleteAccountScreen*)
frontend/src/components/**, frontend/src/hooks/**, frontend/src/stores/**, frontend/src/styles/**
docs/MAPA_PRODUCTO.md, docs/PLAN_EXPERIENCIA.md, docs/design/**
```

### 3.3 Sesión 3 — contenido (PROPUESTA)

```
content/**                                 (salvo content/economy/**)
scripts/content_qa/**, scripts/check_question_bank.py, scripts/catalog_coverage.py,
scripts/metas_catalogo.json, scripts/check_content_sources.py, scripts/check_source_licenses.py
backend/tests/content/**
frontend/src/i18n/{es,en}/contenido.json
docs/CATALOGO_MAESTRO.md
```

### 3.4 Sesión 4 — motor (PROPUESTA)

```
backend/app/services/engine/**, backend/app/services/{quiz,placement,progress,mock_exam,track_exam,lesson_gate,mastery_report,dkt}.py
backend/app/ml/**
frontend/src/i18n/{es,en}/motor.json
docs/ml/**
```

### 3.5 Sesión 5 — legal (PROPUESTA)

```
docs/legal/**
frontend/src/pages/LegalScreen*, frontend/src/pages/DeleteAccountScreen*
frontend/src/i18n/{es,en}/legal.json       (las claves `legal.*` de common.json siguen en common
                                            hasta que la sesión 2 las mueva: ADR-55)
scripts/check_legal_facts.py
```

### 3.6 Sesión 6 — marketing (PROPUESTA)

```
frontend/src/pages/marketing/**            (rutas reservadas: /es/carrera, /en/career,
                                            /es/empresas, /en/enterprise, /blog)
frontend/src/i18n/{es,en}/marketing.json
docs/DISTRIBUCION.md, docs/distribucion-assets/**, docs/COMPETENCIA.md, docs/competitive-teardown.md
```

**Sin dueño en esta propuesta** (la sesión que los necesite lo pide en «Fuera de alcance»):
`backend/app/api/**`, `backend/app/models/**`, `backend/app/schemas/**`, el resto de
`backend/app/services/**`, `backend/tests/**` fuera de contenido, `frontend/src/services/api.ts`,
`docs/API.md`, `docs/ARCHITECTURE.md`, `docs/ECONOMIA.md`, `content/economy/**`.

## 4. Migraciones de Alembic

1. Antes de crear una, lista los PRs abiertos y sus ficheros
   (`gh api repos/Neopram/whetzy/pulls?state=open`, o el conector de GitHub). Si **alguno** toca
   `backend/alembic/versions/`, no crees la tuya: para ese punto y repórtalo.
2. Como máximo **una** migración por PR, siempre con `alembic revision`; nunca `create_all`.
3. `alembic heads` muestra **una** cabeza antes del push.
4. El título del PR lleva **«[MIGRACIÓN]»**. En la cola de fusión van primero los PRs con
   migración y después los que dependen de ellos, uno cada vez (Railway despliega cada fusión).

## 5. Textos de interfaz

- Cada sesión escribe solo `frontend/src/i18n/{es,en}/<su-rol>.json`, en ES y EN nativos.
- Cada fichero es un **namespace propio** de i18next, no se mezcla en `common`: dos sesiones con
  la misma clave se pisarían en silencio. Uso: `useTranslation('marketing')` o
  `t('marketing:hero.title')`.
- `frontend/src/test/i18n.parity.test.ts` exige, fichero a fichero, las mismas claves en los dos
  idiomas y ningún valor vacío, y que cada fichero de rol esté registrado en `src/i18n.ts`.

## 6. Antes de cada push (todas las sesiones)

1. `git fetch origin && git merge origin/master` (nunca rebase de una rama ya empujada).
2. Por cada PR abierto de otra sesión: `git merge-tree --write-tree HEAD origin/<su-rama>`.
   Código distinto de 0 o `CONFLICT` en la salida ⇒ no empujes; lista los ficheros y para.
3. Nivel 1: `git config core.hooksPath .githooks` (config local: repítelo en cada clon).
4. Nivel 2: en la nube, `WHETZY_NIVEL2=gestionado git push …` y después
   `bash scripts/ci_local.sh --sha <sha>` como tarea en segundo plano gestionada (límite ≥ 60
   min). Sale 0 si VERDE y 1 si ROJO; `bash scripts/ci_local.sh --estado` da el último veredicto
   y distingue un nivel 2 que murió sin terminar. Un `nohup` desde un shell que se cierra muere
   con él y deja «CORRIENDO».

## 7. PRs

Uno por tema y pequeño. Secciones: Qué · Por qué (filas del ledger) · Evidencia (comandos y salida
real) · Riesgos al desplegar · Delta del ledger · Fuera de alcance · Solo el dueño. El único check
que cuenta es **«Cloudflare Pages»**; los jobs de Actions mueren sin runner (H.13) y no son ni
fallo ni aprobado. Solo el dueño fusiona (ADR-45).
