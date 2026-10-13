# Whetzy — instrucciones del proyecto

**Pausa levantada el 2026-10-01 (dueño, ADR-56).** Las sesiones vuelven a trabajar en rama
+ PR (ADR-45); `master` lo sigue fusionando solo el dueño. Trampas del entorno medidas:
`docs/CIERRE_2026-09-30.md` §7.

- Fuente de verdad del progreso: `docs/AUTONOMOUS_STATE.md` — **no lo leas entero**
  (~29.500 tokens). `python scripts/ledger.py next` responde «qué toca ahora» en ~114;
  `show <ID>`, `series <N>`, `blocked`, `inv`, `stats`. Parsea el ledger, no lo duplica:
  la fuente de verdad sigue siendo el markdown (ADR-40)
- Alcance del producto (tracks, certificaciones, fuentes, volúmenes, puerta de calidad): `docs/CATALOGO_MAESTRO.md`.
  Plan del catálogo (ADR-54, 2026-10-01): forma única por track, 32 skills × 10 preguntas
  (≥ 3 ejecutables) con 1 lección y 1 término por skill; certificaciones con práctica
  ≥ máx(300, 3 × examen) y simulacro reservado de 2 × examen; tracks nuevos por demanda
  (niveles de ADR-53); el contenido corre en paralelo al piloto (ADR-59). Método y orden de
  producción: `docs/PLAN_CONTENIDO.md`. Cobertura:
  `python scripts/catalog_coverage.py` (metas en `scripts/metas_catalogo.json`)
- Estado narrativo e histórico: `docs/STATUS.md` (registro por sesión; no se reescribe hacia atrás)
- Prompt operativo: `docs/ORCHESTRATOR.md`
- Posición competitiva con pesos fijos: `docs/competitive-teardown.md` (última: §14 ADR-53; §12 captura en vivo, sin re-puntuar) y mercado verificado con URL y fecha en `docs/COMPETENCIA.md` §A
- Decisiones irreversibles: `docs/DECISIONS.md` (ADR-11 fuentes, ADR-12 herramientas, ADR-13 social login, ADR-40 memoria en el repo, ADR-41 precios del dueño, **ADR-45 rama + PR y `master` solo por el dueño, ADR-46 corpus abierto fuera del repo y guarda 37.0 (su meta de volumen, sustituida: hoy manda ADR-54), ADR-47 valores por defecto de la cola humana, ADR-48 un plan = una fila, ADR-49 Pro Max = tutor ilimitado y certificación 39,99 $ pago único, ADR-50 aprobación en bloque del 2026-09-26 (Free, analítica PostHog, Sentry, correo, staging), ADR-53 plan por cobertura (sustituido por ADR-54), ADR-54 catálogo uniforme 32 × 10 (la meta vigente), ADR-55 la fuente legal es lo publicado (claves i18n `legal.*`), ADR-56 fin de la pausa, ADR-58 los créditos no compran simulacros ni cursos (el plan decide) y privacidad con IP y navegador a 90 días, ADR-59 autoría de contenido: escribe Sonnet 5 desde la fuente, por `Workflow`, en paralelo al piloto**)
- Prompt de arranque con control total: `docs/PROMPT_CONTROL_TOTAL.md`
- Auditoría externa del 2026-09-19 (histórica, archivada el 2026-10-01: su «el CI no ha corrido nunca» dejó de ser cierto): `docs/archive/AUDITORIA_EXTERNA_2026-09-19.md`
- Guardia docs-vs-código: `python scripts/check_docs.py` (debe pasar antes de cada commit que toque contenido o docs)
- Protocolo de verificación (cada `DONE`, cada doc, modelos y tokens): `docs/PROTOCOLO_VERIFICACION.md`
- Sesiones en paralelo S1–S6 (qué ficheros escribe cada una, compartidos, migraciones, i18n por rol; bus: issue #89): `docs/SESIONES.md`
- Conectores (Railway, Sentry, PostHog, diseño, redes): cuenta, uso y qué se hace sin preguntar en `docs/CONECTORES.md`. Leer y escribir en privado, sí; producción, publicar, datos de personas, secretos o recursos nuevos, no (ADR-45)
- Documentos vivos: los del índice `docs/README.md`; `docs/archive/` no manda

## Invariantes

- **`master` lo fusiona el dueño a mano (ADR-45, 2026-09-24).** La sesión trabaja en su rama,
  abre un PR por oleada con evidencia y capturas, y **nunca** hace `git push origin master` ni
  fusiona. Cloudflare Pages publica un preview por rama (`<rama>.whetzy.pages.dev`).
- **Corpus abierto fuera del repo (ADR-46):** `corpus/` está en `.gitignore`; al repo solo entra
  `content/sources/index.json` y contenido original ES/EN con fuente. Ninguna pregunta nueva
  hasta que la guarda 37.0 esté en verde.
- **Puerta local antes de cada push** (2026-09-20). `git push origin master` despliega a
  producción y hasta esa fecha no había **nada** en medio: cero hooks de git, y el
  `.github/workflows/ci.yml` depende de la facturación de GitHub Actions: corrió en verde
  el 2026-10-01 (runs de los #60 y #61) y desde ese mismo día, ~12:52 UTC, ningún job
  recibe runner (`runner_id: 0`, sin pasos; H.13). La puerta local es la que vale. Dos niveles:
  `.githooks/pre-push` **bloquea** (~20-30 s: ruff, guardas de esquema y contrato, y
  banco de preguntas / `check_docs.py` solo si cambió contenido o docs);
  `scripts/ci_local.sh` corre **al fondo sin bloquear** (suite entera, `tests/content`,
  `mypy --strict`, frontend) y su veredicto lo imprime el push siguiente. Se activa con
  `git config core.hooksPath .githooks` — **es config local, no viaja con el repo**: en
  un clon nuevo hay que repetirlo. Nada de `--no-verify`; si molesta, el nivel 1 se ha
  vuelto lento y se recorta, no se salta
- **Las cachés de herramientas van FUERA del proyecto.** El repo vive bajo OneDrive con
  Controlled Folder Access, que bloquea en silencio `.mypy_cache` y `.pytest_cache`:
  mypy tardaba ~2 min *siempre* porque nunca llegaba a existir una caché caliente
  (1m58 dentro contra 1m09 fuera). `MYPY_CACHE_DIR` y `-o cache_dir=` apuntan a
  `%LOCALAPPDATA%/whetzy-cache`, que es lo que hacen el hook y `ci_local.sh`. Por lo
  mismo, **escribir ficheros del proyecto desde Python falla con «Bad file
  descriptor»**: escribe al scratchpad y luego `cp`
- Backend prod: `https://api-production-9751.up.railway.app` — **deploy AUTOMÁTICO desde `master`** (verificado 2026-09-16, ledger H.16): cada commit que llega a `master` (una fusión del dueño, ADR-45) despliega backend, migraciones y `content_loader`, con ~1 min de 502/503 durante el cambio (medido 2026-09-24, fila 35.8). Antes de cada push de rama: `pytest tests/content` y `check_question_bank.py` verdes
- Frontend prod: `https://whetzy.com` — **Cloudflare Pages está conectado a Git** y **`master` publica solo a producción** (verificado 2026-09-24: tras el push de `5be177f`, `whetzy.com/landing/` sirve el hero nuevo pre-renderizado; cada otra rama genera un preview y un check `Cloudflare Pages` en el PR). El panel corre `npx tsc -b && npx vite build`; el prerender va dentro de `vite build` y la API sale del fichero, no del panel. Deploy manual también posible con `npx wrangler pages deploy dist --project-name whetzy --branch main` desde `frontend/` (sin `--branch main` va a Preview). `whetzy.com/health` devuelve el SPA; el health real es el del backend. **Tras cada deploy, `node scripts/check-deployed.mjs` (desde `frontend/`; desde la raíz no existe) en PASS** o no está hecho (incidente de login 2026-09-24, serie 30). La API sale de `frontend/.env.production` (`https://api-production-9751.up.railway.app/api/v1`)
- Fuentes de contenido: **solo gratuitas y legales** (ADR-11) — reutilizar MIT/Apache/BSD/CC BY/CC0/PSF/dominio público; CC BY-SA **no** se reutiliza (ADR-47, valor por defecto de H.LIC); CC BY-NC y propietario se cita, nunca se copia. Biblioteca: `docs/CATALOGO_MAESTRO.md` §2.1
- Social login: si existe cualquier OAuth, **Sign in with Apple es obligatorio** antes de enviar a App Store (4.8, ADR-13)
- DB local: Docker `:5433`, `neurium` / `neurium_dev` / db `neurium`
- Alembic: nunca `create_all`. Toda migración por `alembic revision`. HEAD actual: `20261012_paddle_events` (58 migraciones)
- LLM: `qwen/qwen3.8-27b` en Groq
- OpenAPI en `/api/v1/openapi.json`; `POST /quiz/start` devuelve el id en `.question.id`

## Modelos

**Política del dueño del 2026-09-27 (ADR-52, sustituye la de ADR-50; fila de autoría enmendada por ADR-59 el 2026-10-03):**

| Papel | Modelo |
|---|---|
| Hilo principal de una sesión interactiva | **Sonnet 5** (lo fija el dueño al arrancar) |
| Autoría masiva de contenido (escritor en `Workflow`, desde un fragmento de fuente `reusar`) | **Sonnet 5** (ADR-59) |
| Revisor y corrector de calidad en `Workflow`; workers de la lista de riesgo de `docs/PROTOCOLO_VERIFICACION.md` §2 | **Sonnet 5** |
| Lecturas, inventarios, diffs | **Haiku 4.5** |
| Sesiones autónomas programadas | workers **Haiku 4.5** (ADR-14); hilo, el de `settings.json` |
| Fable (cualquier versión), Opus 4.x | **Nunca**, en ningún papel |

Todo lo que se escribe para el alumno pasa revisión adversaria **completa** de Sonnet 5 contra
su fragmento de fuente, la puerta de `CATALOGO_MAESTRO.md` §7 y `scripts/content_qa/`
(`docs/PLAN_CONTENIDO.md`). Primer bloque: piloto de 10 ítems (37.25); si más de 3 salen con
`blocker`/`major`, se para y lo decide el dueño (ADR-52/59; los pilotos de Haiku de track28 y
39.37 superaron ese umbral). Dieta de contexto: el ledger se lee por
secciones, nunca entero; `STATUS.md` y `archive/` no se leen. Bloques de contenido
grandes: `Workflow` paralelo, un bloque = un commit verde. Cada `DONE` pasa por el
verificador adversario (protocolo §7) antes de escribirse.

## Estilo

Tests con el código, no después. **Una guarda que no has roto a propósito no sabes si vigila algo**: mútala, compruébala en rojo, restaura. Y **un test que falla al azar no puede ser una puerta** — o lo arreglas o lo sacas de la puerta, porque un guardián intermitente se acaba ignorando y entonces no protege nada. **Correr subconjuntos de tests no es correr la suite**: la suite entera sacó 3 fallos que ningún subconjunto dirigido tocaba. Escribe como el código que te rodea. Evidencia
ejecutable o no pasó. Documentación en español; contenido y UI en ES y EN nativos.
El schema de `tracks.json` es `name_es/name_en/order/color/icon` (nunca `title_*`):
el loader hace `data["name_es"]` y revienta con otra forma.

