# Whetzy — instrucciones del proyecto

Este proyecto se opera de forma autónoma. **Si arrancas sin instrucciones
específicas del usuario, lee `docs/ORCHESTRATOR.md` y ejecútalo.** No preguntes
qué hacer; el ledger lo sabe.

- Fuente de verdad del progreso: `docs/AUTONOMOUS_STATE.md` — **no lo leas entero**
  (~29.500 tokens). `python scripts/ledger.py next` responde «qué toca ahora» en ~114;
  `show <ID>`, `series <N>`, `blocked`, `inv`, `stats`. Parsea el ledger, no lo duplica:
  la fuente de verdad sigue siendo el markdown (ADR-40)
- Alcance del producto (tracks, certificaciones, fuentes, volúmenes, puerta de calidad): `docs/CATALOGO_MAESTRO.md`
- Estado narrativo e histórico: `docs/STATUS.md` (registro por sesión; no se reescribe hacia atrás)
- Prompt operativo: `docs/ORCHESTRATOR.md`
- Posición competitiva con pesos fijos: `docs/competitive-teardown.md` (última: §11)
- Decisiones irreversibles: `docs/DECISIONS.md` (ADR-11 fuentes, ADR-12 herramientas, ADR-13 social login, ADR-40 memoria en el repo)
- Auditoría externa más reciente (producción medida en vivo, CI, coste de contexto): `docs/AUDITORIA_EXTERNA_2026-09-19.md`
- Guardia docs-vs-código: `python scripts/check_docs.py` (debe pasar antes de cada commit que toque contenido o docs)
- Protocolo de verificación (cada `DONE`, cada doc, modelos y tokens): `docs/PROTOCOLO_VERIFICACION.md`
- Documentos vivos: los del índice `docs/README.md`; `docs/archive/` no manda

## Invariantes

- **Puerta local antes de cada push** (2026-09-20). `git push origin master` despliega a
  producción y hasta esa fecha no había **nada** en medio: cero hooks de git, y el
  `.github/workflows/ci.yml` —que está bien escrito— **no se ha ejecutado nunca** por
  facturación de GitHub. Dos niveles:
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
- Backend prod: `https://api-production-9751.up.railway.app` — **deploy AUTOMÁTICO desde `master`** (verificado 2026-09-16, ledger H.16): `git push origin master` despliega backend, migraciones y `content_loader`. Antes de cada push: `pytest tests/content` y `check_question_bank.py` verdes
- Frontend prod: `https://whetzy.com` — **deploy MANUAL** con `npx wrangler pages deploy dist --project-name whetzy --branch main` desde `frontend/` (sin `--branch main` va a Preview). `whetzy.com/health` devuelve el SPA; el health real es el del backend
- Fuentes de contenido: **solo gratuitas y legales** (ADR-11) — reutilizar MIT/Apache/BSD/CC BY/CC0/PSF/dominio público; CC BY-SA espera H.LIC; CC BY-NC y propietario se cita, nunca se copia. Biblioteca: `docs/CATALOGO_MAESTRO.md` §2.1
- Social login: si existe cualquier OAuth, **Sign in with Apple es obligatorio** antes de enviar a App Store (4.8, ADR-13)
- DB local: Docker `:5433`, `neurium` / `neurium_dev` / db `neurium`
- Alembic: nunca `create_all`. Toda migración por `alembic revision`. HEAD actual: `b1c2d3e4f5a6` (28 migraciones)
- LLM: `qwen/qwen3.8-27b` en Groq
- OpenAPI en `/api/v1/openapi.json`; `POST /quiz/start` devuelve el id en `.question.id`

## Modelos

Hilo principal: el que fije `settings.json` (Sonnet 4.6). **Sesiones autónomas: sin
Opus ni Fable** (ADR-14, propuesta del dueño 2026-09-18). Subagentes: **Haiku por
defecto** — inventarios, lecturas masivas, diffs doc↔código, verificación adversaria y
**autoría de contenido por fichero** (siempre con la puerta de calidad de
`CATALOGO_MAESTRO.md` §7); Sonnet solo cuando la tarea escribe en la lista de ficheros de
riesgo de `docs/PROTOCOLO_VERIFICACION.md` §2. Dieta de contexto: el ledger se lee por
secciones, nunca entero; `STATUS.md` y `archive/` no se leen. Bloques de contenido
grandes: `Workflow` paralelo, un bloque = un commit verde. Cada `DONE` pasa por el
verificador adversario (protocolo §7) antes de escribirse.

## Estilo

Tests con el código, no después. **Una guarda que no has roto a propósito no sabes si vigila algo**: mútala, compruébala en rojo, restaura. Y **un test que falla al azar no puede ser una puerta** — o lo arreglas o lo sacas de la puerta, porque un guardián intermitente se acaba ignorando y entonces no protege nada. **Correr subconjuntos de tests no es correr la suite**: la suite entera sacó 3 fallos que ningún subconjunto dirigido tocaba. Escribe como el código que te rodea. Evidencia
ejecutable o no pasó. Documentación en español; contenido y UI en ES y EN nativos.
El schema de `tracks.json` es `name_es/name_en/order/color/icon` (nunca `title_*`):
el loader hace `data["name_es"]` y revienta con otra forma.

