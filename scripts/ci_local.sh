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
# Uso: bash scripts/ci_local.sh            (corre todo)
#      bash scripts/ci_local.sh --estado   (que paso la ultima vez)
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ" || exit 1
BITACORA="$RAIZ/.ci-local"
mkdir -p "$BITACORA"

if [ "${1:-}" = "--estado" ]; then
  [ -f "$BITACORA/estado" ] && cat "$BITACORA/estado" || echo "todavia no ha corrido nunca"
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

SHA="$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
INICIO="$(date '+%Y-%m-%d %H:%M')"
printf 'CORRIENDO desde %s (%s)\n' "$INICIO" "$SHA" > "$BITACORA/estado"

FALLOS=()
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
  if ( cd "$dir" && timeout --kill-after=60 "$LIMITE_S" "$@" ); then
    echo "[ok] $nombre"
    RESUELTOS+=("$nombre")
  else
    local rc=$?
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
correr "backend: suite entera" "$RAIZ/backend" \
  python -m pytest tests/ --ignore=tests/content -q -p no:randomly --tb=short $CACHE_PYTEST
correr "backend: contenido"    "$RAIZ/backend" \
  python -m pytest tests/content -q -p no:randomly --tb=short $CACHE_PYTEST
correr "backend: mypy --strict" "$RAIZ/backend" \
  mypy app --strict --ignore-missing-imports

if [ -d "$RAIZ/frontend/node_modules" ]; then
  correr "frontend: tipos"  "$RAIZ/frontend" npx tsc -b
  # oxlint se comprueba ANTES de usarlo. Si no arranca, el paso se salta con
  # [--] en vez de contar como rojo: un paso permanentemente rojo por una
  # herramienta rota localmente enseña a ignorar la puerta entera, que es peor
  # que no tenerla. El 2026-09-20 pasaba esto: oxlint@1.82 pide node
  # ^20.19.0 || >=22.12.0 y la maquina tiene v20.18.0, asi que npm se salta su
  # binario nativo opcional y `npx oxlint` muere al cargar el modulo. En CI no
  # ocurre: `node-version: "20"` resuelve a la ultima 20.x.
  if ( cd "$RAIZ/frontend" && npx oxlint --version >/dev/null 2>&1 ); then
    correr "frontend: oxlint" "$RAIZ/frontend" npx oxlint src --deny-warnings
  else
    titulo "frontend: oxlint"
    echo "[--] oxlint no arranca aqui (mira si node cumple el engine que pide)."
    echo "[--] No cuenta como rojo. En CI si corre."
  fi
  correr "frontend: vitest" "$RAIZ/frontend" npm run -s test
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
    echo "$FIN · $SHA · todo en verde"
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
