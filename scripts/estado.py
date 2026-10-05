"""Estado de Whetzy en un solo comando: GitHub, Railway, Cloudflare y el repo.

Sustituye el informe que hasta ahora pedía el dueño a una sesión («trae todo
actualizado»): unos 15 minutos y 3-4 $ de modelo cada vez, y con el riesgo de
confundir un valor por defecto del código con el estado de producción. Este
script solo LEE; no escribe en ningún servicio ni en el repo.

    python scripts/estado.py                      # informe en Markdown por stdout
    python scripts/estado.py --out informe.md --json estado.json --state previo.json

Credenciales, todas opcionales (sin ellas, esa parte sale como «sin leer»):
    GITHUB_TOKEN o GH_TOKEN   lectura del repo privado (si faltan, prueba `gh auth token`)
    RAILWAY_PROJECT_TOKEN     token de proyecto del entorno production (despliegues)

Salida: 0 sin alertas, 1 con alguna alerta. Documentación: docs/ESTADO_AUTOMATICO.md.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO = os.environ.get("WHETZY_REPO", "Neopram/whetzy")
API = os.environ.get("WHETZY_API", "https://api-production-9751.up.railway.app").rstrip("/")
WEB = os.environ.get("WHETZY_WEB", "https://whetzy.com").rstrip("/")
GITHUB_API = "https://api.github.com"
RAILWAY_GRAPHQL = "https://backboard.railway.com/graphql/v2"
# IDs del proyecto `whetzy` en Railway (no son secretos; leídos con el conector el 2026-10-05).
RAILWAY_PROJECT_ID = "45292163-570b-42c3-9579-fecf661d17df"
RAILWAY_ENVIRONMENT_ID = "b8bd601c-0252-420a-8818-7c75c20494bb"
RAILWAY_API_SERVICE_ID = "fb2dbcaa-1cc3-4e92-918d-25fcdb65e426"
TIMEOUT = 20

OK, AVISO, ALERTA, SIN_LEER = "ok", "aviso", "alerta", "sin leer"
_ORDEN = {ALERTA: 0, AVISO: 1, SIN_LEER: 2, OK: 3}


@dataclass
class Check:
    area: str
    nombre: str
    nivel: str
    detalle: str


@dataclass
class Informe:
    generado: str
    master_sha: str | None = None
    checks: list[Check] = field(default_factory=list)
    prs: list[dict] = field(default_factory=list)
    cifras: dict = field(default_factory=dict)

    def add(self, area: str, nombre: str, nivel: str, detalle: str) -> None:
        self.checks.append(Check(area, nombre, nivel, detalle))

    @property
    def alertas(self) -> list[Check]:
        return [c for c in self.checks if c.nivel == ALERTA]


# --------------------------------------------------------------------------- análisis puros


def extraer_build_sha(html: str) -> str | None:
    """SHA del build que sirve Cloudflare Pages (`<meta name="whetzy-build">`)."""
    m = re.search(r'<meta\s+name=["\']whetzy-build["\']\s+content=["\']([0-9a-fA-F]{7,40})["\']', html)
    if not m:
        m = re.search(r'<meta\s+content=["\']([0-9a-fA-F]{7,40})["\']\s+name=["\']whetzy-build["\']', html)
    return m.group(1).lower() if m else None


def mismo_commit(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    a, b = a.lower(), b.lower()
    return a.startswith(b) or b.startswith(a)


def parsear_ledger_stats(texto: str) -> dict[str, int]:
    """`python scripts/ledger.py stats` → {"DONE": 79, "TODO": 64, ...}."""
    cifras: dict[str, int] = {}
    for linea in texto.splitlines():
        m = re.match(r"\s{2,}(.+?)\s{2,}(\d+)\s*$", linea)
        if m:
            cifras[m.group(1).strip()] = int(m.group(2))
    return cifras


def parsear_pendiente_catalogo(texto: str) -> int | None:
    """`catalog_coverage.py` → total de preguntas pendientes (acepta «4.118» y «4118»)."""
    m = re.search(r"Total de preguntas pendientes:\s*([\d.,]+)", texto)
    return int(re.sub(r"[.,]", "", m.group(1))) if m else None


def resumir_checks_pr(check_runs: list[dict]) -> tuple[str, str]:
    """Estado de los checks de un PR. Los de GitHub Actions se separan: sin runner (H.13)
    fallan en segundos en todos los PR y su rojo no dice nada del PR."""
    propios, actions = [], []
    for c in check_runs:
        app = ((c.get("app") or {}).get("slug") or "").lower()
        (actions if app == "github-actions" else propios).append(c)

    def malo(c: dict) -> bool:
        return c.get("conclusion") in {"failure", "timed_out", "cancelled", "action_required"}

    pendientes = [c["name"] for c in propios if c.get("status") != "completed"]
    rojos = [c["name"] for c in propios if c.get("status") == "completed" and malo(c)]
    nota = f" (+{len(actions)} de Actions sin contar, H.13)" if actions else ""
    if rojos:
        return ALERTA, "rojo: " + ", ".join(sorted(rojos)) + nota
    if pendientes:
        return AVISO, "en curso: " + ", ".join(sorted(pendientes)) + nota
    if not propios:
        return SIN_LEER, "sin checks propios" + nota
    return OK, f"{len(propios)} en verde" + nota


def comparar(previo: dict | None, actual: dict) -> list[str]:
    """Cambios relevantes desde la última ejecución, en frases cortas."""
    if not previo:
        return ["primera ejecución: no hay estado anterior con el que comparar"]
    cambios: list[str] = []
    if previo.get("master_sha") != actual.get("master_sha"):
        cambios.append(f"master: {str(previo.get('master_sha'))[:7]} → {str(actual.get('master_sha'))[:7]}")
    antes = {p["numero"] for p in previo.get("prs", [])}
    ahora = {p["numero"] for p in actual.get("prs", [])}
    if ahora - antes:
        cambios.append("PR abiertos nuevos: " + ", ".join(f"#{n}" for n in sorted(ahora - antes)))
    if antes - ahora:
        cambios.append("PR que ya no están abiertos: " + ", ".join(f"#{n}" for n in sorted(antes - ahora)))
    niveles_antes = {(c["area"], c["nombre"]): c["nivel"] for c in previo.get("checks", [])}
    niveles_ahora = {(c["area"], c["nombre"]): c["nivel"] for c in actual.get("checks", [])}
    for clave, nivel in niveles_ahora.items():
        if clave in niveles_antes and niveles_antes[clave] != nivel:
            cambios.append(f"{clave[0]} · {clave[1]}: {niveles_antes[clave]} → {nivel}")
    # Un check que desaparece solo cuenta si su área se midió las dos veces (--sin-repo no mide «Repo»).
    areas_ahora = {area for area, _ in niveles_ahora}
    for clave, nivel in niveles_antes.items():
        if clave not in niveles_ahora and clave[0] in areas_ahora:
            cambios.append(f"{clave[0]} · {clave[1]}: ya no aparece (antes {nivel})")
    for k, v in actual.get("cifras", {}).items():
        if k in previo.get("cifras", {}) and previo["cifras"][k] != v:
            cambios.append(f"{k}: {previo['cifras'][k]} → {v}")
    return cambios or ["sin cambios desde la última ejecución"]


def render_markdown(inf: Informe, cambios: list[str]) -> str:
    icono = {OK: "✅", AVISO: "⚠️", ALERTA: "🛑", SIN_LEER: "·"}
    lineas = [
        f"# Estado de Whetzy — {inf.generado}",
        "",
        f"`master` = `{(inf.master_sha or '?')[:12]}` · alertas: **{len(inf.alertas)}**",
        "",
        "## Cambios desde la última ejecución",
        "",
        *[f"- {c}" for c in cambios],
        "",
        "## Comprobaciones",
        "",
        "| | Área | Qué | Detalle |",
        "|---|---|---|---|",
    ]
    for c in sorted(inf.checks, key=lambda c: (_ORDEN[c.nivel], c.area, c.nombre)):
        detalle = c.detalle.replace("|", "\\|").replace("\n", " ")
        lineas.append(f"| {icono[c.nivel]} | {c.area} | {c.nombre} | {detalle} |")
    if inf.prs:
        lineas += ["", "## PR abiertos", "", "| PR | Borrador | Detrás de master | Checks | Actualizado |", "|---|---|---|---|---|"]
        for p in inf.prs:
            titulo = p["titulo"][:70].replace("|", "\\|")
            lineas.append(
                f"| #{p['numero']} {titulo} | {'sí' if p['borrador'] else 'no'} | {p.get('detras', '?')} "
                f"| {icono[p['checks_nivel']]} {p['checks']} | {p['actualizado'][:16].replace('T', ' ')} |"
            )
    if inf.cifras:
        lineas += ["", "## Cifras", ""]
        lineas += [f"- **{k}:** {v}" for k, v in inf.cifras.items()]
    lineas += [
        "",
        "---",
        (
            "Solo lectura. No incluye el estado de las sesiones de Claude (no hay API que un script pueda leer); "
            "ver docs/ESTADO_AUTOMATICO.md."
        ),
    ]
    return "\n".join(lineas) + "\n"


# --------------------------------------------------------------------------- E/S


def _http(url: str, headers: dict | None = None, data: bytes | None = None) -> tuple[int, bytes, float]:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "whetzy-estado", **(headers or {})})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read(), time.monotonic() - t0
    except urllib.error.HTTPError as e:
        return e.code, e.read(), time.monotonic() - t0


def _token_github() -> str | None:
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    if shutil.which("gh"):
        r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=False)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    return None


class GitHub:
    def __init__(self, token: str | None):
        self.headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def get(self, ruta: str):
        status, body, _ = _http(f"{GITHUB_API}/repos/{REPO}{ruta}", self.headers)
        if status != 200:
            raise RuntimeError(f"GitHub {ruta}: HTTP {status}")
        return json.loads(body)


def revisar_github(inf: Informe, gh: GitHub) -> None:
    try:
        commit = gh.get("/commits/master")
    except RuntimeError as e:
        inf.add("GitHub", "acceso al repo", SIN_LEER, f"{e} (¿GITHUB_TOKEN?)")
        return
    inf.master_sha = commit["sha"]
    primera = commit["commit"]["message"].splitlines()[0]
    inf.add("GitHub", "master", OK, f"`{commit['sha'][:7]}` {commit['commit']['committer']['date']} — {primera[:80]}")
    rama = gh.get("/branches/master")
    inf.add(
        "GitHub", "master protegido",
        OK if rama.get("protected") else ALERTA,
        "sí" if rama.get("protected") else "no: se puede fusionar en rojo y cada fusión despliega (H.16)",
    )
    for p in gh.get("/pulls?state=open&per_page=100"):
        sha = p["head"]["sha"]
        try:
            detras = gh.get(f"/compare/master...{sha}")["behind_by"]
        except RuntimeError:
            detras = "?"
        nivel, texto = resumir_checks_pr(gh.get(f"/commits/{sha}/check-runs?per_page=100").get("check_runs", []))
        inf.prs.append({
            "numero": p["number"], "titulo": p["title"], "borrador": p["draft"], "detras": detras,
            "checks": texto, "checks_nivel": nivel, "actualizado": p["updated_at"],
        })
    inf.prs.sort(key=lambda p: p["numero"])
    rojos = [f"#{p['numero']}" for p in inf.prs if p["checks_nivel"] == ALERTA]
    inf.add("GitHub", "PR abiertos", AVISO if rojos else OK,
            f"{len(inf.prs)} abiertos" + (f"; checks en rojo: {', '.join(rojos)}" if rojos else ""))


def revisar_cloudflare(inf: Informe) -> None:
    status, body, dt = _http(f"{WEB}/")
    if status != 200:
        inf.add("Cloudflare", "whetzy.com", ALERTA, f"HTTP {status}")
        return
    inf.add("Cloudflare", "whetzy.com", OK, f"HTTP 200 en {dt:.2f} s")
    servido = extraer_build_sha(body.decode("utf-8", "replace"))
    if not servido:
        inf.add("Cloudflare", "build servido = master", AVISO, "sin <meta name=\"whetzy-build\"> en el HTML")
    elif not inf.master_sha:
        inf.add("Cloudflare", "build servido = master", SIN_LEER, f"sirve `{servido[:7]}`; master sin leer")
    else:
        igual = mismo_commit(servido, inf.master_sha)
        inf.add("Cloudflare", "build servido = master", OK if igual else AVISO,
                f"sirve `{servido[:7]}`" + ("" if igual else f", master es `{inf.master_sha[:7]}` (despliegue en curso o fallido)"))


def revisar_railway(inf: Informe, token: str | None) -> None:
    status, body, dt = _http(f"{API}/health")
    sano = status == 200 and b"healthy" in body
    inf.add("Railway", "API /health", OK if sano else ALERTA, f"HTTP {status} en {dt:.2f} s" + ("" if sano else f": {body[:120]!r}"))
    status, body, _ = _http(f"{API}/api/v1/billing/paddle/config")
    if status == 200:
        d = json.loads(body)
        precios = d.get("prices") or {}
        sin = [k for k, v in precios.items() if not v]
        inf.add("Railway", "Paddle", OK if d.get("enabled") else AVISO,
                f"enabled={d.get('enabled')}, entorno={d.get('environment')}" + (f"; sin precio: {', '.join(sin)}" if sin else ""))
    else:
        inf.add("Railway", "Paddle", AVISO, f"/billing/paddle/config HTTP {status}")
    if not token:
        inf.add("Railway", "último despliegue = master", SIN_LEER, "falta RAILWAY_PROJECT_TOKEN")
        return
    consulta = {
        "query": "query($input: DeploymentListInput!) { deployments(input: $input, first: 1) "
                 "{ edges { node { id status createdAt meta } } } }",
        "variables": {"input": {"projectId": RAILWAY_PROJECT_ID, "environmentId": RAILWAY_ENVIRONMENT_ID,
                                "serviceId": RAILWAY_API_SERVICE_ID}},
    }
    status, body, _ = _http(RAILWAY_GRAPHQL, {"Project-Access-Token": token, "Content-Type": "application/json"},
                            json.dumps(consulta).encode())
    try:
        nodo = json.loads(body)["data"]["deployments"]["edges"][0]["node"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        inf.add("Railway", "último despliegue = master", AVISO, f"respuesta inesperada (HTTP {status}): {body[:160]!r}")
        return
    commit = (nodo.get("meta") or {}).get("commitHash")
    estado = nodo.get("status")
    igual = mismo_commit(commit, inf.master_sha)
    nivel = ALERTA if estado in {"FAILED", "CRASHED"} else (OK if estado == "SUCCESS" and igual else AVISO)
    inf.add("Railway", "último despliegue = master", nivel,
            f"{estado} `{str(commit)[:7]}` {nodo.get('createdAt', '')[:16]}" + ("" if igual else f" (master `{str(inf.master_sha)[:7]}`)"))


def _extraer_master(repo_dir: Path, ref: str, destino: Path) -> bool:
    """`git archive <ref>` a un directorio fuera del proyecto (OneDrive bloquea escrituras dentro)."""
    r = subprocess.run(["git", "-C", str(repo_dir), "archive", "--format=tar", ref], capture_output=True, check=False)
    if r.returncode != 0:
        return False
    with tarfile.open(fileobj=io.BytesIO(r.stdout)) as tar:
        try:
            tar.extractall(destino, filter="data")
        except TypeError:  # Python sin el parámetro filter (anterior a 3.11.4 / 3.12)
            tar.extractall(destino)
    return True


def revisar_repo(inf: Informe, repo_dir: Path, ref: str) -> None:
    subprocess.run(["git", "-C", str(repo_dir), "fetch", "-q", "origin", "master"], capture_output=True, check=False)
    with tempfile.TemporaryDirectory(prefix="whetzy-estado-") as tmp:
        raiz = Path(tmp)
        if not _extraer_master(repo_dir, ref, raiz):
            inf.add("Repo", f"contenido de {ref}", SIN_LEER, f"git archive {ref} falló en {repo_dir}")
            return
        py = sys.executable
        stats = subprocess.run([py, "scripts/ledger.py", "stats"], cwd=raiz, capture_output=True, text=True, check=False)
        cifras = parsear_ledger_stats(stats.stdout)
        if cifras:
            inf.cifras["ledger"] = ", ".join(f"{k} {v}" for k, v in cifras.items())
        else:
            inf.add("Repo", "ledger", SIN_LEER, (stats.stderr or "sin salida")[:160])
        cob = subprocess.run([py, "scripts/catalog_coverage.py"], cwd=raiz, capture_output=True, text=True, check=False)
        pendiente = parsear_pendiente_catalogo(cob.stdout)
        if pendiente is not None:
            inf.cifras["preguntas pendientes (catalog_coverage)"] = pendiente
        env_prod = (raiz / "frontend" / ".env.production").read_text(encoding="utf-8", errors="replace")
        correo = re.search(r"^VITE_FEEDBACK_EMAIL=\S+", env_prod, re.MULTILINE)
        inf.add("Repo", "botón «Enviar comentario» (piloto)", OK if correo else AVISO,
                "VITE_FEEDBACK_EMAIL definido" if correo else "VITE_FEEDBACK_EMAIL vacío: el botón no aparece (LANZAMIENTO_PILOTO §0.2)")
        inf.add("Repo", "carpeta iOS", OK if (raiz / "frontend" / "ios").exists() else AVISO,
                "existe" if (raiz / "frontend" / "ios").exists() else "no existe frontend/ios (H.14)")
        sync = raiz / "sync.ps1"
        if sync.exists() and "pg_restore --clean" in sync.read_text(encoding="latin-1"):
            inf.add("Repo", "sync.ps1", ALERTA,
                    "restaura la base local sobre la DATABASE_URL de Railway con pg_restore --clean: no ejecutar")
        else:
            inf.add("Repo", "sync.ps1", OK, "no hay script que restaure sobre Railway")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, help="escribe el Markdown aquí (además de stdout)")
    ap.add_argument("--json", type=Path, help="escribe el estado en JSON aquí")
    ap.add_argument("--state", type=Path, help="JSON de la ejecución anterior, para el apartado de cambios")
    ap.add_argument("--repo-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--ref", default="origin/master", help="commit cuyo contenido se lee (por defecto origin/master)")
    ap.add_argument("--sin-repo", action="store_true", help="no lee el ledger ni el catálogo (p. ej. en Railway)")
    args = ap.parse_args(argv)

    inf = Informe(generado=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"))
    revisar_github(inf, GitHub(_token_github()))
    revisar_cloudflare(inf)
    revisar_railway(inf, os.environ.get("RAILWAY_PROJECT_TOKEN"))
    if not args.sin_repo:
        revisar_repo(inf, args.repo_dir, args.ref)

    actual = asdict(inf)
    previo = None
    if args.state and args.state.exists():
        try:
            previo = json.loads(args.state.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previo = None
    md = render_markdown(inf, comparar(previo, actual))
    sys.stdout.write(md)
    if args.out:
        args.out.write_text(md, encoding="utf-8")
    if args.json:
        args.json.write_text(json.dumps(actual, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if inf.alertas else 0


if __name__ == "__main__":
    sys.exit(main())
