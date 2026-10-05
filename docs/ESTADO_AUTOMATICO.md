# Estado automático de Whetzy

> Creado el 2026-10-05. Script: `scripts/estado.py` (con `scripts/estado.ps1` para Windows) y
> sus tests en `backend/tests/unit/test_estado.py`. **Solo lee**: no escribe en GitHub, Railway,
> Cloudflare ni en el repo.

Etiquetas: **[V]** comprobado con una herramienta el 2026-10-05 · **[P]** estimación o dato sin
volver a comprobar.

## 1. Para qué sirve

Sustituye el «trae todo actualizado» que hasta ahora se le pedía a una sesión. Cada uno de esos
informes costaba unos 15 minutos y 3-4 $ de modelo [P: diferencia del coste registrado de la sesión
que los hizo]. Además, las sesiones gastan turnos solo en confirmar estado. Ejemplos medidos con la
diferencia de `total_cost_usd` entre turnos consecutivos [V]:

| Sesión | Turno | Coste del turno |
|---|---|---|
| S1 | «Still early. Waiting for the background task notification» | 0,55 $ |
| S1 | «Just the Cloudflare deploy notice, no action needed» | 0,27 $ |
| S5 | «Nothing new to do: this is the merge notice for #134» | 0,25 $ |
| S3 | «PR #128 (C.1) merged. Four of six PRs merged now» | 0,15 $ |

El script hace la misma comprobación en unos **10 segundos y sin coste de modelo** [V: ejecución
del 2026-10-05], y siempre lee producción de la misma forma. Así evita el error que corrigió la
enmienda del `PLAN_MAESTRO.md`: presentar un valor por defecto del código como si fuera el estado de
producción.

## 2. Cómo se usa

**En Windows (PC del dueño):**

```powershell
pwsh scripts/estado.ps1 -Abrir                 # informe y lo abre
pwsh scripts/estado.ps1 -Registrar -CadaHoras 3 # tarea programada de Windows
pwsh scripts/estado.ps1 -Quitar                 # borra esa tarea
```

- El informe, el JSON y el historial (últimos 60) van a `%LOCALAPPDATA%\whetzy-cache\estado`, fuera
  del proyecto: OneDrive con Controlled Folder Access bloquea escribir dentro (CLAUDE.md).
- Cada ejecución se compara con la anterior: «master: x → y», PR nuevos o cerrados, checks que cambian
  de nivel o desaparecen, y cifras que se mueven.
- **Sale con 1 si hay alguna alerta**, para que una tarea programada o un CI la vean.

**En cualquier sistema:** `python scripts/estado.py [--out f.md] [--json f.json] [--state previo.json] [--sin-repo]`.

**Requisitos:**
- Python 3.11 o posterior.
- `git` y una copia del repo para la parte «Repo»: se lee el contenido de `origin/master` con
  `git archive`, no la rama en la que estés.
- Opcional, `gh`, para obtener el token de GitHub.

**Credenciales.** Las dos son opcionales; sin ellas, esa parte sale como «sin leer»:

| Variable | Para qué | Permiso mínimo |
|---|---|---|
| `GITHUB_TOKEN` (o `gh auth token`) | El repo es privado | Lectura de contenido, PR y checks |
| `RAILWAY_PROJECT_TOKEN` | Último despliegue del servicio `api` | Token de proyecto del entorno `production` (Railway → proyecto → Settings → Tokens) |

## 3. Qué comprueba

| Área | Comprobación | Alerta cuando | Fuente |
|---|---|---|---|
| GitHub | `master`: SHA, fecha y título | — | `GET /repos/…/commits/master` |
| GitHub | `master` protegido | No lo está (H.16) | `GET /branches/master` |
| GitHub | Cada PR abierto: borrador, **cuántos commits va detrás de `master`** y sus checks | Un check propio en rojo (aviso en el resumen) | `compare`, `check-runs` |
| Cloudflare | `whetzy.com` responde | No da 200 | HTTP |
| Cloudflare | El build servido es el de `master` | — (aviso si difiere: despliegue en curso o fallido) | `<meta name="whetzy-build">` del HTML, el mismo que usa `check-deployed.mjs` |
| Railway | `/health` | No da 200 `healthy` | HTTP |
| Railway | Paddle | — (aviso si está apagado; lista los precios sin definir) | `/api/v1/billing/paddle/config` |
| Railway | Último despliegue de `api` = `master` | `FAILED` o `CRASHED` | API pública de Railway: `deployments(input:{projectId, environmentId, serviceId}, first: 1)` con la cabecera `Project-Access-Token`; el commit sale de `meta.commitHash` [V: documentación de Railway y conector, 2026-10-05] |
| Repo | Cifras del ledger y preguntas pendientes | — | `ledger.py stats`, `catalog_coverage.py` |
| Repo | `VITE_FEEDBACK_EMAIL`, carpeta iOS | — (avisos) | Ficheros de `origin/master` |
| Repo | `sync.ps1` | Restaura con `pg_restore --clean` sobre una URL de Railway (§6) | Fichero |

En GitHub, los checks de **GitHub Actions se cuentan aparte**. Sin runner (H.13), fallan en todos
los PR y su rojo no dice nada del PR.

**Lo que no comprueba y por qué:**
- **El estado de las sesiones de Claude.** Solo se lee con las herramientas de una sesión, no hay API
  para un script [P]. Se documenta a mano en §5.
- **Los flags de cobro en Railway** (`CERTIFICATION_PAYWALL` y compañía). Leerlos exige leer variables
  de producción, que es nivel H en `CONECTORES.md`. Los confirma el dueño (PLAN_MAESTRO §5, n.º 3).
- **La prueba de login → respuesta → logout (CSRF, #131).** Necesita una cuenta. Se puede automatizar
  con Playwright y una cuenta de QA cuando el dueño la cree (`smoke_post_deploy.sh` ya acepta
  `QA_EMAIL`).

## 4. Ejecutarlo solo: dónde y qué hace falta

| Dónde | Estado | Qué falta | Coste |
|---|---|---|---|
| **Programador de tareas de Windows** | **Listo**: `estado.ps1 -Registrar` | Nada en la nube. Probado con PowerShell 7.4.6 en Linux; el registro de la tarea solo puede probarse en Windows [P] | 0 |
| **Railway (cron job)** | Propuesto | Crear un servicio nuevo es nivel H (`CONECTORES.md`): lo decide el dueño | Solo mientras corre [V: docs de Railway] |
| **GitHub Actions** | Propuesto | `.github/**` es de S5 (SESIONES §3), y H.13: ningún job recibe runner desde el 2026-10-01 | Minutos de Actions |
| **Cloudflare** | No recomendado | Pages no tiene cron. Un Worker con cron obligaría a reescribir el script en JS, y el script ya lee Cloudflare desde fuera | — |

**Railway cron.** Railway ejecuta el comando de arranque del servicio según un horario de crontab en
UTC (mínimo cada 5 minutos) y espera que termine. Si la ejecución anterior sigue activa, se salta la
siguiente [V: docs de Railway, «Cron Jobs»]. Pasos para el dueño:
1. En el proyecto `whetzy`, crear un servicio nuevo desde el mismo repo y la rama `master`.
2. Comando de arranque: `python scripts/estado.py --sin-repo`. En Railway no hay un clon con
   `origin`, así que la parte «Repo» se omite.
3. Horario: `0 */3 * * *`.
4. Variables del servicio:
   - `GITHUB_TOKEN`, un token de grano fino de solo lectura sobre `Neopram/whetzy`;
   - `RAILWAY_PROJECT_TOKEN`.
5. El informe sale en los logs del servicio. Para que llegue a algún sitio (un comentario en el #89,
   un correo) habría que escribir fuera de Railway, y eso es otra decisión del dueño.

**GitHub Actions.** Texto propuesto para que S5 lo aplique cuando haya runner (H.13). No se crea
aquí:

```yaml
# .github/workflows/estado.yml
name: estado
on:
  schedule: [{ cron: "17 */3 * * *" }]
  workflow_dispatch: {}
permissions: { contents: read, pull-requests: read, checks: read }
jobs:
  estado:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: python scripts/estado.py --out "$GITHUB_STEP_SUMMARY"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          RAILWAY_PROJECT_TOKEN: ${{ secrets.RAILWAY_PROJECT_TOKEN }}
```

## 5. Sesiones: foto del 2026-10-05, ~01:10 UTC

Leído con `list_sessions` y `list_events` de las herramientas de sesión, **sin enviar mensajes ni
interrumpir ninguna** [V]. Los costes son el `cost_usd` que registra cada sesión (precio de lista),
no necesariamente la factura.

| Sesión | Rol | Estado | Lo último | Espera del dueño | Coste |
|---|---|---|---|---|---|
| Reglas de hierro 1 | S1 full stack | Lista para revisión (00:56) | Arregló el bucle infinito de logout en su #153 que detectó el dueño; espera el nivel 2 | — | 240,10 $ |
| Reglas de hierro 2 | S2 contenido | Terminada (10-03) | #96, #99, #102 y #106 fusionados; parada por ADR-59 | — | 56,47 $ |
| Reglas de hierro 3 | S3 motor | Lista para revisión (10-04) | 5 de 6 PR fusionados; #133 abierto, 67 commits por detrás de `master` [V] | Fusionar o descartar #133 | 131,74 $ |
| Reglas de hierro 4 | S4 legal | Terminada (10-04) | #122 fusionado con 7 propuestas legales | **Decidir las 7 propuestas** (ADR-55) | 29,57 $ |
| Reglas de hierro 5 | S5 integrador | **Bloqueada en el dueño** (10-04 19:42) | 6 PR fusionados; CI completo en verde (1.852 backend, 71.729 contenido, 553 frontend) | **Prueba CSRF** (login → responder → logout) y **D1–D4** en el #89 | 143,02 $ |
| Reglas de hierro 6 | S6 marketing | Lista para revisión (10-04) | Disponible | — | 103,28 $ |
| Progreso del proyecto | COORD | Lista para revisión (01:01) | Nivel 2 de su rama de AI-901 (track45) en marcha; ha encontrado 3 fallos de docs | — | 450,91 $ |
| Conexión a Lovable | Auditoría | **Bloqueada en el dueño desde el 10-04 19:19** | Auditoría de 7 dimensiones terminada | **Aprobar o rechazar su plan** (ExitPlanMode) | 314,89 $ |
| Prompt avanzado… | Esta sesión | Trabajando | Este documento y el script | — | 20,26 $ |

**Total registrado: unos 1.490 $** [V: suma de `cost_usd`]. Fuera de Whetzy hay 5 sesiones antiguas
de otro repo (PSM) y personales, que no cuentan aquí.

## 6. Riesgo encontrado: `sync.ps1`

`sync.ps1`, en la raíz del repo, hace dos cosas:
1. una copia de la base local de Docker (`learning-engine-db-1`);
2. **`pg_restore --clean --if-exists` sobre la `DATABASE_URL` de Railway que se le pegue** [V: leído
   entero].

Con la URL de producción, **sustituye los datos reales por los de desarrollo**. Siempre termina con
«PROCESO COMPLETADO AL 100% CON ÉXITO», aunque falle. Entró el 2026-09-24 dentro del commit
`36a5532`, que era de la racha.

**No ejecutarlo.** El script de estado lo marca como alerta mientras exista. Borrarlo o protegerlo es
decisión del dueño, porque puede ser una herramienta suya.

## 7. Mantenimiento

- Los tests (`backend/tests/unit/test_estado.py`) no usan la red. Cada regla que decide una alerta tiene
  su test, y se comprobó mutándola: 7 mutaciones, las 7 en rojo, el 2026-10-05 [V].
- Si cambia la salida de `ledger.py stats` o de `catalog_coverage.py`, falla el test que lee el ledger
  real, antes de que el informe se quede sin cifras sin avisar.
- Si cambia el `<meta name="whetzy-build">` o la API de Railway, el informe lo marca como «aviso»; no
  inventa un estado.
