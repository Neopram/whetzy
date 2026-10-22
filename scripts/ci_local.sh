#!/usr/bin/env bash
# Nivel 2 de la puerta local: lo mismo que hace .github/workflows/ci.yml, pero
# en este PC y sin bloquear el push. Lo arranca .githooks/pre-push al fondo.
#
# Existe por dos motivos medidos el 2026-09-20:
#   - Correr subconjuntos de tests NO es correr la suite: la suite entera saco 3
#     fallos que ningun subconjunto dirigido tocaba.
#   - Un fallo de `tests/content` aparecio una vez y su mensaje SE PERDIO, asi
#     que no hubo forma de saber que pregunta fallo. Aqui todo queda en
#     .ci-local/, con su fecha, para poder mirarlo despues.
#
# Uso: bash scripts/ci_local.sh            (corre todo, sobre un worktree de HEAD)
#      bash scripts/ci_local.sh --sha X    (sobre un worktree del commit X; el hook)
#      bash scripts/ci_local.sh --estado   (que paso la ultima vez)
#      bash scripts/ci_local.sh --carril pr96 --sha X   (carril propio, ver abajo)
#      bash scripts/ci_local.sh --carril pr96 --estado
#
# Carriles. Por defecto hay UN nivel 2 por checkout: el cerrojo
# (.ci-local/corriendo.pid) mata al anterior, porque el nuevo lleva el commit
# mas reciente y varias suites a la vez dejaron la maquina sin CPU (2026-09-27).
# Eso es lo que quiere el hook (pushes seguidos de la misma rama), pero no dos
# PRs distintos de la misma sesion: el 2026-10-02 el nivel 2 del #96 murio con
# `exit 137` al lanzar el del #99 desde el mismo checkout. `--carril <nombre>`
# separa cerrojo, bitacora (.ci-local/carril-<nombre>/) y worktree
# ($CACHE/wt-nivel2-<nombre>): dos carriles corren a la vez; dentro de un carril
# el nuevo sigue matando al viejo. Sin `--carril`, todo queda como antes.
#
# Sesiones en la nube (o cualquier shell que se cierre al acabar el comando):
# un `nohup ... &` lanzado desde ahi muere con el shell y deja «CORRIENDO» sin
# veredicto. Alli se empuja con WHETZY_NIVEL2=gestionado (el hook no lo lanza
# al fondo) y se corre el nivel 2 como tarea gestionada en primer plano:
#      bash scripts/ci_local.sh --sha <sha>   # sale 0 si VERDE, 1 si ROJO
# El log va a la salida estandar Y a .ci-local/ultima.log. El interprete es
# el `python` del PATH; WHETZY_PYTHON lo cambia (p. ej. el de un venv limpio).
set -uo pipefail

# Todo el cuerpo va dentro de una funcion A PROPOSITO. bash lee un script a
# trozos mientras lo ejecuta: si alguien sobrescribe este fichero con un run
# en marcha (un `git pull`, un parche a mano), el bash vivo sigue leyendo por
# el offset viejo en un fichero nuevo y ejecuta fragmentos al azar. Paso el
# 2026-09-21: «ignorando.: command not found» y la suite entera otra vez desde
# cero. Una funcion se parsea COMPLETA antes de ejecutar su primera linea.
main() {

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ" || exit 1

MODO="correr"
CARRIL=""
_sha_pedido="HEAD"
while [ $# -gt 0 ]; do
  case "$1" in
    --estado) MODO="estado"; shift ;;
    --sha) [ -n "${2:-}" ] && _sha_pedido="$2"; shift 2 || shift ;;
    --carril)
      CARRIL="${2:-}"; shift 2 || shift
      if ! printf '%s' "$CARRIL" | grep -Eq '^[a-z0-9][a-z0-9-]{0,39}$'; then
        echo "--carril necesita un nombre en [a-z0-9-] (p. ej. pr96), y es '$CARRIL'" >&2; exit 2
      fi ;;
    *) echo "argumento desconocido: $1" >&2; exit 2 ;;
  esac
done

BITACORA="$RAIZ/.ci-local${CARRIL:+/carril-$CARRIL}"
mkdir -p "$BITACORA"

# ¿Sigue vivo el nivel 2 del cerrojo? `kill -0` solo no basta: tras un
# reinicio del contenedor el PID lo puede tener otro proceso y «CORRIENDO»
# seguiria mintiendo. Donde hay /proc se exige ademas que sea este script.
nivel2_vivo() {
  local pid
  pid="$(cat "$BITACORA/corriendo.pid" 2>/dev/null)"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null || return 1
  if [ -r "/proc/$pid/cmdline" ]; then
    tr '\0' ' ' < "/proc/$pid/cmdline" | grep -q "ci_local.sh" || return 1
  fi
  return 0
}

if [ "$MODO" = "estado" ]; then
  if [ ! -f "$BITACORA/estado" ]; then
    echo "todavia no ha corrido nunca"
    exit 0
  fi
  # `estado` se escribe "CORRIENDO" al empezar y solo se sobrescribe con el
  # veredicto real al terminar normal. Un contenedor pausado/matado a medias
  # (visto el 2026-09-30: mas de una hora idle entre turnos de la sesion) deja
  # el cerrojo con un PID muerto y "CORRIENDO" mintiendo para siempre hasta la
  # proxima corrida que sí termine. `--estado` comprueba el PID antes de fiarse.
  if grep -q "^CORRIENDO" "$BITACORA/estado" 2>/dev/null && ! nivel2_vivo; then
    echo "SE INTERRUMPIO SIN TERMINAR (el proceso ya no existe; el cerrojo quedo huerfano)"
    cat "$BITACORA/estado"
    exit 0
  fi
  cat "$BITACORA/estado"
  exit 0
fi

if [ -n "${LOCALAPPDATA:-}" ] && command -v cygpath >/dev/null 2>&1; then
  CACHE="$(cygpath -u "$LOCALAPPDATA")/whetzy-cache"
else
  CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/whetzy"
fi
mkdir -p "$CACHE/mypy" "$CACHE/pytest"
export MYPY_CACHE_DIR="$CACHE/mypy"
CACHE_PYTEST="-o cache_dir=$CACHE/pytest"
PY="${WHETZY_PYTHON:-python}"

# El log lo escribe el propio script. Antes lo escribia la redireccion del
# hook, y una corrida a mano archivaba como suyo el ultima.log de la corrida
# anterior (otro SHA). WHETZY_CI_LOG_HECHO evita el doble tee si alguien ya
# redirige aqui.
if [ -z "${WHETZY_CI_LOG_HECHO:-}" ]; then
  export WHETZY_CI_LOG_HECHO=1
  exec > >(tee "$BITACORA/ultima.log") 2>&1
  TEE_PID=$!
fi

# Un solo nivel 2 a la vez. El hook decia «se reemplaza» cuando el anterior
# seguia corriendo y NO lo mataba: el 2026-09-21 hubo tres pytest a la vez y
# 1,8 GB libres de 14. Dos suites de 25 min compitiendo en esta maquina es
# exactamente lo que ya mato un run sin dejar traza (ver los gotchas de
# memoria). El nuevo manda: lleva el commit mas reciente.
# Mata un PID y todos sus descendientes (recursivo). Hace falta en Linux/Mac:
# ahi no hay `taskkill /T`, y un `kill -9` suelto sobre el bash del cerrojo
# deja a `timeout`/`pytest` huerfanos (reparentados a init) corriendo igual,
# quemando un nucleo cada uno. Medido el 2026-09-27 en un contenedor Linux:
# 5 pushes seguidos dejaron 5 `pytest tests/` a la vez, y ESE fue el motivo de
# que el push siguiente diera "backend: suite entera (cuelgue)" — no un fallo
# real, sino la maquina sin CPU libre para terminar en el limite de 2700 s.
_matar_arbol() {
  local pid="$1" hijo
  for hijo in $(pgrep -P "$pid" 2>/dev/null); do
    _matar_arbol "$hijo"
  done
  kill -9 "$pid" 2>/dev/null
}

CERROJO="$BITACORA/corriendo.pid"
if [ -f "$CERROJO" ]; then
  _viejo="$(cat "$CERROJO" 2>/dev/null)"
  if [ -n "$_viejo" ] && kill -0 "$_viejo" 2>/dev/null; then
    echo "[cerrojo] ya corria el nivel 2 (pid $_viejo); lo paro, este es mas nuevo"
    # `kill` solo alcanza al bash: `pkill` ni existe en Git Bash, y python.exe
    # es un nieto nativo que sobrevive huerfano quemando un nucleo entero (el
    # 2026-09-21 paso dos veces, con el cerrojo puesto). Y `taskkill /T` desde
    # el bash TAMPOCO llega: el subshell de `correr` hace exec en `timeout`, en
    # msys eso mata el proceso Windows original y el arbol queda roto justo
    # debajo del bash (python <- timeout <- timeout <- MUERTO). Por eso cada
    # paso apunta el WINPID de su `timeout` en paso.winpid: desde ahi el arbol
    # si esta entero. Primero el bash, para que no lance el paso siguiente.
    if command -v taskkill >/dev/null 2>&1; then
      _win="$(ps -p "$_viejo" 2>/dev/null | awk 'NR>1 {print $4}')"
      [ -n "$_win" ] && taskkill //PID "$_win" //T //F >/dev/null 2>&1
      _win_paso="$(cat "$BITACORA/paso.winpid" 2>/dev/null)"
      [ -n "$_win_paso" ] && taskkill //PID "$_win_paso" //T //F >/dev/null 2>&1
    else
      _matar_arbol "$_viejo"
    fi
    sleep 2
  fi
fi
echo $$ > "$CERROJO"
trap 'rm -f "$CERROJO" "$BITACORA/paso.winpid"' EXIT

# --- Se prueba un commit, no el disco (35.9) ---------------------------------
# El 2026-09-24 el contrato frontend↔backend dio rojo porque `api.ts` ganó una
# ruta a mitad de la suite: el nivel 2 leía el árbol de trabajo mientras se
# editaba. Ahora corre sobre un worktree del SHA (el empujado, que le pasa el
# hook con --sha; HEAD si se lanza a mano), fuera del proyecto. node_modules se
# enlaza desde el árbol principal: reinstalarlo costaría minutos por push.
SHA_COMPLETO="$(git rev-parse --verify "$_sha_pedido^{commit}" 2>/dev/null)" || {
  echo "ROJO"$'\n'"$(date '+%Y-%m-%d %H:%M') · no existe el commit $_sha_pedido" > "$BITACORA/estado"; exit 1; }
ARBOL="$CACHE/wt-nivel2${CARRIL:+-$CARRIL}"
NM="$ARBOL/frontend/node_modules"
# El enlace se quita ANTES de borrar el worktree: un borrado recursivo que lo
# siguiera vaciaría el node_modules del árbol principal. En Windows es una
# junction (el `ln -s` de Git Bash copia), y `rmdir` la quita sin tocar el destino.
soltar_arbol() {
  if [ -L "$NM" ]; then rm -f "$NM"
  elif [ -e "$NM" ] && command -v cygpath >/dev/null 2>&1; then cmd //c rmdir "$(cygpath -w "$NM")" >/dev/null 2>&1
  fi
  git -C "$RAIZ" worktree remove --force "$ARBOL" >/dev/null 2>&1
  git -C "$RAIZ" worktree prune >/dev/null 2>&1
}
soltar_arbol; rm -rf "$ARBOL"
git worktree add --detach "$ARBOL" "$SHA_COMPLETO" >/dev/null 2>&1 || {
  echo "ROJO"$'\n'"$(date '+%Y-%m-%d %H:%M') · no pude crear el worktree" > "$BITACORA/estado"; exit 1; }
if [ -d "$RAIZ/frontend/node_modules" ]; then
  if command -v cygpath >/dev/null 2>&1; then
    cmd //c mklink /J "$(cygpath -w "$NM")" "$(cygpath -w "$RAIZ/frontend/node_modules")" >/dev/null
  else
    ln -s "$RAIZ/frontend/node_modules" "$NM"
  fi
fi
trap 'rm -f "$CERROJO" "$BITACORA/paso.winpid"; soltar_arbol' EXIT

SHA="$(git rev-parse --short "$SHA_COMPLETO")"
INICIO="$(date '+%Y-%m-%d %H:%M')"
printf 'CORRIENDO desde %s (%s)\n' "$INICIO" "$SHA" > "$BITACORA/estado"
# Una señal que se puede atrapar (el shell que se cierra manda HUP; Ctrl-C,
# INT; un `kill`, TERM) deja el veredicto escrito en vez de «CORRIENDO» para
# siempre (35.9). Un SIGKILL no se atrapa: ese lo detecta `nivel2_vivo`.
interrumpido() {
  printf 'ROJO\n%s · %s · INTERRUMPIDO por %s antes de terminar (sin veredicto)\n' \
    "$(date '+%Y-%m-%d %H:%M')" "$SHA" "$1" > "$BITACORA/estado"
  _matar_arbol_hijos
  exit 1
}
_matar_arbol_hijos() {
  local hijo
  # El `tee` del log no: matarlo deja a este bash escribiendo en una tuberia
  # rota, muere por SIGPIPE y no llega a soltar el worktree.
  for hijo in $(pgrep -P $$ 2>/dev/null); do
    [ "$hijo" = "${TEE_PID:-}" ] || _matar_arbol "$hijo"
  done
}
trap 'interrumpido HUP' HUP
trap 'interrumpido INT' INT
trap 'interrumpido TERM' TERM

FALLOS=()
# Pasos que no corrieron por falta de algo (hoy, el e2e sin BD). No son rojo,
# pero tampoco verde: el veredicto los nombra para que no pasen por corridos.
SALTADOS=()
# Todo paso que se ANUNCIA tiene que dar un VEREDICTO. El 2026-09-20 el paso
# «backend: contenido» se anuncio, reviento (el script estaba en CRLF y la
# continuacion de linea se rompio), no imprimio ni [ok] ni [FALLA]... y el run
# salio VERDE. Una puerta que puede saltarse un paso en silencio es peor que no
# tenerla, porque ademas da confianza. Se comparan las dos listas al final.
ANUNCIADOS=()
RESUELTOS=()
titulo() {
  ANUNCIADOS+=("$1")
  printf '
========== %s ==========
' "$1"
}

# LIMITE_S por paso. No es paranoia: el 2026-09-20 la suite imprimio
# «1021 passed» y el proceso NO SALIO — CPU congelada, 30 hilos vivos, 2,8 GB,
# indefinidamente. Sin limite, el nivel 2 se queda «CORRIENDO» para siempre y
# deja de avisar de nada. Con limite, un cuelgue se reporta como cuelgue.
LIMITE_S="${WHETZY_CI_LIMITE_S:-2700}"

correr() {  # correr <nombre> <dir> <comando...>
  local nombre="$1" dir="$2"; shift 2
  titulo "$nombre"
  ( cd "$dir" && timeout --kill-after=60 "$LIMITE_S" "$@" ) &
  local hijo=$!
  # Un segundo despues del fork el subshell ya ha hecho exec y `ps` da el
  # WINPID de `timeout`, que es el que el cerrojo necesita (ver arriba).
  sleep 1
  ps -p "$hijo" 2>/dev/null | awk 'NR>1 {print $4}' > "$BITACORA/paso.winpid"
  wait "$hijo"
  local rc=$?
  if [ "$rc" = "0" ]; then
    echo "[ok] $nombre"
    RESUELTOS+=("$nombre")
  else
    if [ "$rc" = "124" ] || [ "$rc" = "137" ]; then
      echo "[CUELGUE] $nombre no termino en ${LIMITE_S}s"
      FALLOS+=("$nombre (cuelgue)")
      RESUELTOS+=("$nombre")
    else
      echo "[FALLA] $nombre (codigo $rc)"
      FALLOS+=("$nombre")
      RESUELTOS+=("$nombre")
    fi
  fi
}

# `-p no:randomly` a proposito: el orden aleatorio ya provoco un fallo
# irreproducible. Un guardian que falla al azar se acaba ignorando. El orden
# aleatorio es util, pero como ejercicio aparte y no como puerta.
# `--ignore=tests/content`: `tests/` son 20.518 tests y 19.481 son de contenido, que
# ya tienen su propio paso; sin esto corrian dos veces. Y ojo al leer el porcentaje de
# pytest con el contenido dentro: es el 95% de la CUENTA y una fraccion del TIEMPO, asi
# que parece colgarse en el 96% cuando lo que pasa es que empiezan los de integracion.
correr "backend: suite entera" "$ARBOL/backend" \
  "$PY" -m pytest tests/ --ignore=tests/content -q -p no:randomly --tb=short $CACHE_PYTEST
# Tests marcados `slow` (pytest.ini): O(corpus) por construccion, no un
# presupuesto de reloj fragil -- el de BM25 solo el solito tarda >5 min. La
# suite de arriba los deselecciona (`-m "not benchmark and not slow"` en
# addopts) para no arrastrar ese tiempo en cada corrida; van aqui, en su
# propio paso con veredicto propio, con mas margen que el limite general
# (decision del dueno 2026-09-30, >=45 min).
LIMITE_S_PREVIO="$LIMITE_S"
LIMITE_S=3600
correr "backend: suite lenta (slow)" "$ARBOL/backend" \
  "$PY" -m pytest tests/ -m slow -q -p no:randomly --tb=short $CACHE_PYTEST
LIMITE_S="$LIMITE_S_PREVIO"
correr "backend: contenido"    "$ARBOL/backend" \
  "$PY" -m pytest tests/content -q -p no:randomly --tb=short $CACHE_PYTEST
# `python -m mypy` y no `mypy`: el binario del PATH puede ser otro entorno sin
# las dependencias del proyecto (2026-09-24: un mypy de uv sin pydantic dio
# cientos de «Class cannot subclass BaseModel» falsos; con el intérprete del
# proyecto, 0 errores en 117 ficheros).
correr "backend: migración con datos" "$ARBOL/backend" \
  "$PY" ../scripts/test_migration_data.py
# Los stubs no están en requirements.txt: los instala `.github/workflows/ci.yml`
# aparte (desde PyJWT, ADR-69 #1, solo `types-passlib`). Sin él mypy puede dar
# `no-any-return` en app/core/security.py, que es del
# entorno y no del código (#89, 2026-10-03). Solo se avisa; el paso corre igual.
FALTAN_STUBS=$("$PY" -c 'import importlib.metadata as m
for p in ("types-passlib",):
    try: m.version(p)
    except m.PackageNotFoundError: print(p)' 2>/dev/null | tr '\n' ' ')
if [ -n "$FALTAN_STUBS" ]; then
  echo "[!!] faltan ${FALTAN_STUBS}en $PY: si mypy falla en app/core/security.py, es"
  echo "     el entorno (pip install ${FALTAN_STUBS% }), no el código"
fi
correr "backend: mypy --strict" "$ARBOL/backend" \
  "$PY" -m mypy app --strict --ignore-missing-imports

if command -v bandit >/dev/null 2>&1; then
  correr "backend: bandit (seguridad)" "$ARBOL/backend" \
    bandit -r app/ -c "$ARBOL/.bandit.yml" -ll -q
else
  titulo "backend: bandit"; echo "[--] bandit no instalado; me lo salto"
fi

if [ -d "$ARBOL/frontend/node_modules" ]; then
  correr "frontend: tipos"  "$ARBOL/frontend" npx tsc -b
  # oxlint se comprueba ANTES de usarlo. Si no arranca, el paso se salta con
  # [--] en vez de contar como rojo: un paso permanentemente rojo por una
  # herramienta rota localmente enseña a ignorar la puerta entera, que es peor
  # que no tenerla. Paso el 2026-09-20: oxlint@1.82 pide node
  # ^20.19.0 || >=22.12.0, la maquina tenia v20.18.0, npm se saltaba su
  # binario nativo opcional y `npx oxlint` moria al cargar el modulo. Se
  # arreglo subiendo node con nvm, NO reinstalando: probado que con node
  # 20.19 y el mismo lockfile arranca. En CI no ocurre: `node-version: "20"`
  # resuelve a la ultima 20.x.
  if ( cd "$ARBOL/frontend" && npx oxlint --version >/dev/null 2>&1 ); then
    correr "frontend: oxlint" "$ARBOL/frontend" npx oxlint --deny-warnings
  else
    titulo "frontend: oxlint"
    echo "[--] oxlint no arranca aqui (mira si node cumple el engine que pide)."
    echo "[--] No cuenta como rojo. En CI si corre."
  fi
  correr "frontend: vitest" "$ARBOL/frontend" npm run -s test
  # Red line 3 (fallbackLng: 'es' nunca se dispara). Existia el script (23.5) y
  # pasaba, pero no corria en ningun sitio automatico -- ni aqui, ni pre-push,
  # ni ci.yml -- hasta que la auditoria de 20.7 encontro el hueco.
  correr "frontend: i18n parity" "$ARBOL/frontend" npm run -s check:i18n
  # Red line: 30.4 midio "check-prerender PASS" pero el script solo corria en
  # ci.yml, que nunca se ejecuta por facturacion de GitHub -- igual que el
  # hueco de "i18n parity" arriba, encontrado por la auditoria de 20.7.
  # `npm run build` ya llama a scripts/prerender-landing.mjs vía el plugin de
  # Vite, pero ese script solo comprueba que `data-lcp="hero"` este presente,
  # no el idioma del texto: un build en Node 21+ puede colar el hero en
  # ingles (navigator.language del propio Node) sin que `vite build` se
  # entere. check-prerender.mjs es la unica guarda que lee la copia de verdad.
  correr "frontend: build (prerender incluido)" "$ARBOL/frontend" npm run -s build
  correr "frontend: check-prerender" "$ARBOL/frontend" node scripts/check-prerender.mjs
  correr "frontend: check-dev-only" "$ARBOL/frontend" node scripts/check-dev-only.mjs
  # 2026-10-02: 24 ejercicios Python pasaban en CPython (tests/content) y no
  # podian resolverse en el navegador: hilos, asyncio.run, sqlite3, tempfile.
  # Este los corre en el Pyodide del build, detras del sandbox del worker.
  correr "frontend: ejercicios resolubles en Pyodide" "$ARBOL/frontend" npm run -s check:exec-pyodide
  # 46.5: regresión visual (64 capturas, API simulada, sin backend). Solo aquí,
  # nunca en el hook: ~4 min. Las baselines van por plataforma (el antialiasing
  # del texto cambia entre sistemas); sin carpeta para esta, se avisa y se
  # salta en vez de dar rojo por «no hay baseline». Regenerar tras un cambio de
  # diseño a propósito: `npx playwright test -c playwright.visual.config.ts -u`.
  VIS_PLAT=linux
  case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) VIS_PLAT=win32 ;; Darwin) VIS_PLAT=darwin ;; esac
  if [ -d "$ARBOL/frontend/e2e/__screenshots__/$VIS_PLAT" ]; then
    correr "frontend: regresión visual" "$ARBOL/frontend" npx playwright test -c playwright.visual.config.ts
  else
    echo "[--] regresión visual: sin baselines de $VIS_PLAT en e2e/__screenshots__/; me la salto"
  fi
  # 42.2: la suite e2e (Playwright), lo mismo que el job `e2e` de ci.yml, que
  # desde el 2026-10-01 no recibe runner (H.13): hasta aquí no corría en ningún
  # sitio automático. Va la última: es la más lenta y la única que necesita BD.
  # Variables:
  #   WHETZY_E2E_DATABASE_URL  OBLIGATORIA. postgresql+asyncpg://usuario:clave@host:puerto/db
  #                            de un Postgres DEDICADO: se migra, se siembra y se
  #                            llena de usuarios de prueba. Nunca la de desarrollo
  #                            (:5433) ni la de producción. Sin ella, o si no
  #                            responde en 5 s, el paso se salta.
  #   PW_CHROMIUM_EXECUTABLE   opcional: un Chromium propio (playwright.config.ts).
  # Las demás las fija el paso como el job de ci.yml: ENVIRONMENT=test,
  # SECRET_KEY de prueba, GROQ_API_KEY vacía, y CI=1 (servidores siempre nuevos
  # contra esta BD, nunca uno que ya estuviera escuchando en :8000).
  # Saltarlo NO es un verde: queda apuntado en SALTADOS y el veredicto lo dice.
  E2E_BD="${WHETZY_E2E_DATABASE_URL:-}"
  if [ -z "$E2E_BD" ]; then
    echo "[--] frontend: e2e (Playwright): sin WHETZY_E2E_DATABASE_URL; me lo salto (no cuenta como verde)"
    SALTADOS+=("frontend: e2e (Playwright) — sin WHETZY_E2E_DATABASE_URL")
  elif ! DATABASE_URL="$E2E_BD" "$PY" -c '
import asyncio, os, asyncpg
async def tocar():
    c = await asyncio.wait_for(asyncpg.connect(os.environ["DATABASE_URL"].replace("+asyncpg", "", 1)), 5)
    await c.close()
asyncio.run(tocar())' >/dev/null 2>&1; then
    echo "[--] frontend: e2e (Playwright): el Postgres de WHETZY_E2E_DATABASE_URL no responde; me lo salto (no cuenta como verde)"
    SALTADOS+=("frontend: e2e (Playwright) — Postgres sin respuesta")
  else
    # El webServer arranca `python -m uvicorn` del PATH: que sea el intérprete de $PY.
    _py_dir="$(dirname "$(command -v "$PY")")"
    correr "frontend: e2e (Playwright)" "$ARBOL" \
      env PATH="$_py_dir:$PATH" DATABASE_URL="$E2E_BD" ENVIRONMENT=test \
        SECRET_KEY=e2e-test-secret-for-ci GROQ_API_KEY= CI=1 \
      bash -c 'cd backend && python -m alembic upgrade head \
        && python -m app.services.content_loader && python -m app.services.seed \
        && cd ../frontend && npm run -s test:e2e'
  fi
else
  titulo "frontend"; echo "[--] sin node_modules; me lo salto"
fi

# Lo anunciado que no dio veredicto cuenta como rojo, no como silencio.
for _anunciado in "${ANUNCIADOS[@]}"; do
  case "$_anunciado" in
    resumen|frontend|"frontend: oxlint") continue ;;
  esac
  _visto=0
  for _resuelto in ${RESUELTOS[@]+"${RESUELTOS[@]}"}; do
    if [ "$_resuelto" = "$_anunciado" ]; then _visto=1; break; fi
  done
  if [ "$_visto" = "0" ]; then
    echo "[SIN VEREDICTO] $_anunciado - se anuncio y no reporto nada"
    FALLOS+=("$_anunciado (sin veredicto)")
  fi
done

FIN="$(date '+%Y-%m-%d %H:%M')"
{
  if [ ${#FALLOS[@]} -eq 0 ]; then
    echo "VERDE"
    if [ ${#SALTADOS[@]} -eq 0 ]; then
      echo "$FIN · $SHA · todo en verde"
    else
      echo "$FIN · $SHA · en verde lo que corrió; SIN CORRER: ${#SALTADOS[@]}"
      for s in "${SALTADOS[@]}"; do echo "  - $s"; done
    fi
  else
    echo "ROJO"
    echo "$FIN · $SHA · en rojo: ${#FALLOS[@]}"
    for f in "${FALLOS[@]}"; do echo "  - $f"; done
  fi
} > "$BITACORA/estado"

cp "$BITACORA/ultima.log" "$BITACORA/$(date '+%Y%m%d-%H%M')-$SHA.log" 2>/dev/null || true
# Guarda solo las 10 ultimas, que si no esto crece sin fin.
ls -1t "$BITACORA"/*.log 2>/dev/null | tail -n +11 | xargs -r rm -f

titulo "resumen"
cat "$BITACORA/estado"
[ ${#FALLOS[@]} -eq 0 ]
}

main "$@"
