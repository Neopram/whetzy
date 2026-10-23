#!/usr/bin/env bash
# H.50: descarga del corpus para una sesión de autoría en la nube (ADR-46, PLAN_CONTENIDO §3).
#
# El contenedor de la nube es efímero y `corpus/` está en .gitignore: sin este paso,
# una sesión de autoría no encuentra las fuentes. Pegar una vez en Setup script del entorno:
#     bash scripts/corpus/sesion_nube.sh
#
# Cubre solo las fuentes que son un repo de GitHub (el pipeline sabe clonar git).
# Las demás (sitios web de documentación) no tienen cobertura en este script: el
# pipeline `fetch --kind http` baja un único fichero, no un sitio. Se listan al final.
#
# Idempotente: una fuente ya clonada se salta. Sale con 1 en el primer fallo.
# SESION_NUBE_DRY=1 imprime el plan sin tocar la red (lo usa tests/unit/test_corpus_nube.py).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"

mapfile -t FUENTES < <("$PY" - <<'PYEOF'
import json
for s in json.load(open("content/sources/index.json", encoding="utf-8")):
    print(f"{s['name']}\t{s['url']}")
PYEOF
)

git_n=0 ; web_n=0 ; saltadas=0
for linea in "${FUENTES[@]}"; do
  name="${linea%%$'\t'*}"
  url="${linea#*$'\t'}"
  if [[ "$url" != https://github.com/* ]]; then
    web_n=$((web_n + 1))
    echo "[omitida-web] $name ($url)"
    continue
  fi
  git_n=$((git_n + 1))
  if [ -d "corpus/$name/raw/.git" ]; then
    saltadas=$((saltadas + 1))
    echo "[ya] $name"
    continue
  fi
  if [ "${SESION_NUBE_DRY:-0}" = "1" ]; then
    echo "[plan] $name <- $url"
    continue
  fi
  echo "[fetch] $name"
  "$PY" -m scripts.corpus.fetch --name "$name" --kind git --url "$url"
  "$PY" -m scripts.corpus.verify_license --name "$name"
done

echo "corpus: $git_n repos git (${saltadas} ya presentes), $web_n sitios web sin cobertura aquí"
