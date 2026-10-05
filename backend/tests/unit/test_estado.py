"""Tests para scripts/estado.py — el informe de estado que sustituye al «trae todo actualizado».

Sin red: se prueban las funciones que deciden qué es una alerta, y `main` con las
consultas sustituidas. El último test lee el ledger real: si `ledger.py stats` cambia
de formato, el informe dejaría de mostrar las cifras sin avisar.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "estado.py"

_spec = importlib.util.spec_from_file_location("estado", SCRIPT)
estado = importlib.util.module_from_spec(_spec)
sys.modules["estado"] = estado
_spec.loader.exec_module(estado)


def _run(nombre: str, conclusion: str | None, app: str = "cloudflare-workers-and-pages", status: str = "completed"):
    return {"name": nombre, "status": status, "conclusion": conclusion, "app": {"slug": app}}


# --- Cloudflare: el commit que sirve whetzy.com -------------------------------------------


def test_extrae_el_sha_del_meta_en_los_dos_ordenes_de_atributos():
    sha = "fac2e0cf4210c34d62f9b40fc3684e0d639aa5f8"
    assert estado.extraer_build_sha(f'<meta name="whetzy-build" content="{sha}">') == sha
    assert estado.extraer_build_sha(f"<meta content='{sha.upper()}' name='whetzy-build'>") == sha


def test_sin_meta_no_inventa_un_sha():
    assert estado.extraer_build_sha('<meta name="description" content="fac2e0cf4210">') is None


def test_mismo_commit_admite_sha_corto_y_rechaza_vacios():
    assert estado.mismo_commit("fac2e0c", "fac2e0cf4210c34d62f9b40fc3684e0d639aa5f8")
    assert not estado.mismo_commit("fac2e0c", "5d22bf7")
    assert not estado.mismo_commit(None, "fac2e0c")


# --- Checks de los PR: el rojo de Actions sin runner (H.13) no es del PR ------------------


def test_el_rojo_de_github_actions_no_cuenta_como_rojo_del_pr():
    nivel, texto = estado.resumir_checks_pr(
        [_run("Cloudflare Pages", "success"), _run("backend", "failure", app="github-actions")]
    )
    assert nivel == estado.OK
    assert "H.13" in texto


def test_un_check_propio_en_rojo_es_alerta():
    nivel, texto = estado.resumir_checks_pr([_run("Cloudflare Pages", "failure")])
    assert nivel == estado.ALERTA
    assert "Cloudflare Pages" in texto


def test_un_check_propio_sin_terminar_es_aviso():
    nivel, _ = estado.resumir_checks_pr([_run("Cloudflare Pages", None, status="in_progress")])
    assert nivel == estado.AVISO


def test_sin_checks_propios_no_se_da_por_verde():
    nivel, _ = estado.resumir_checks_pr([_run("backend", "failure", app="github-actions")])
    assert nivel == estado.SIN_LEER


# --- GitHub con respuestas fijas (sin red) ----------------------------------------------


class _GitHubFalso:
    def __init__(self, protegido: bool, conclusion_pr: str = "success"):
        self.respuestas = {
            "/commits/master": {
                "sha": "e" * 40,
                "commit": {"message": "Merge pull request #1\n\ncuerpo", "committer": {"date": "2026-10-05T00:00:00Z"}},
            },
            "/branches/master": {"protected": protegido},
            "/pulls?state=open&per_page=100": [
                {"number": 7, "title": "x", "draft": False, "head": {"sha": "1" * 40}, "updated_at": "2026-10-05T00:00:00Z"}
            ],
            f"/compare/master...{'1' * 40}": {"behind_by": 3},
            f"/commits/{'1' * 40}/check-runs?per_page=100": {"check_runs": [_run("Cloudflare Pages", conclusion_pr)]},
        }

    def get(self, ruta: str):
        return self.respuestas[ruta]


def _nivel(inf, nombre):
    return next(c.nivel for c in inf.checks if c.nombre == nombre)


def test_master_sin_proteger_es_alerta_y_protegido_es_ok():
    for protegido, esperado in ((False, estado.ALERTA), (True, estado.OK)):
        inf = estado.Informe(generado="hoy")
        estado.revisar_github(inf, _GitHubFalso(protegido))
        assert _nivel(inf, "master protegido") == esperado
        assert inf.master_sha == "e" * 40


def test_los_pr_traen_cuanto_van_detras_y_el_rojo_de_sus_checks():
    inf = estado.Informe(generado="hoy")
    estado.revisar_github(inf, _GitHubFalso(True, conclusion_pr="failure"))
    assert inf.prs[0]["detras"] == 3
    assert inf.prs[0]["checks_nivel"] == estado.ALERTA
    assert _nivel(inf, "PR abiertos") == estado.AVISO


# --- Cifras del repo ---------------------------------------------------------------------


def test_parsea_la_salida_de_ledger_stats():
    salida = (
        "Filas en el backlog ejecutable: 203\n\n"
        "  DONE                       79\n"
        "  HUMAN-BLOCKED (cola §3)    45\n"
        "  DOING                      1\n"
    )
    assert estado.parsear_ledger_stats(salida) == {"DONE": 79, "HUMAN-BLOCKED (cola §3)": 45, "DOING": 1}


def test_parsea_el_pendiente_del_catalogo_con_y_sin_separador_de_miles():
    assert estado.parsear_pendiente_catalogo("Total de preguntas pendientes: 4.118 ≈ 8 sesiones") == 4118
    assert estado.parsear_pendiente_catalogo("Total de preguntas pendientes: 512") == 512
    assert estado.parsear_pendiente_catalogo("sin la línea") is None


def test_ledger_stats_real_sigue_teniendo_el_formato_que_parsea_el_informe():
    salida = subprocess.run(
        [sys.executable, "scripts/ledger.py", "stats"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    cifras = estado.parsear_ledger_stats(salida)
    assert "DONE" in cifras and "TODO" in cifras, salida[:300]


# --- Cambios entre ejecuciones -----------------------------------------------------------


def _estado(sha="a" * 40, prs=(1,), nivel="ok", pendiente=100):
    return {
        "master_sha": sha,
        "prs": [{"numero": n} for n in prs],
        "checks": [{"area": "GitHub", "nombre": "master protegido", "nivel": nivel}],
        "cifras": {"pendiente": pendiente},
    }


def test_primera_ejecucion_lo_dice():
    assert "primera ejecución" in estado.comparar(None, _estado())[0]


def test_sin_cambios_lo_dice():
    assert estado.comparar(_estado(), _estado()) == ["sin cambios desde la última ejecución"]


def test_detecta_master_nuevo_pr_abierto_y_cerrado_nivel_y_cifra():
    cambios = estado.comparar(_estado(), _estado(sha="b" * 40, prs=(2,), nivel="alerta", pendiente=90))
    texto = "\n".join(cambios)
    assert "master: aaaaaaa → bbbbbbb" in texto
    assert "PR abiertos nuevos: #2" in texto
    assert "ya no están abiertos: #1" in texto
    assert "master protegido: ok → alerta" in texto
    assert "pendiente: 100 → 90" in texto


def test_un_check_que_desaparece_se_cuenta_solo_si_su_area_se_midio_otra_vez():
    previo = _estado()
    previo["checks"].append({"area": "Repo", "nombre": "sync.ps1", "nivel": "alerta"})
    con_repo = _estado()
    con_repo["checks"].append({"area": "Repo", "nombre": "ledger", "nivel": "ok"})
    assert "Repo · sync.ps1: ya no aparece (antes alerta)" in estado.comparar(previo, con_repo)
    assert estado.comparar(previo, _estado()) == ["sin cambios desde la última ejecución"]


# --- Informe y código de salida ----------------------------------------------------------


def test_el_markdown_escapa_las_barras_y_cuenta_las_alertas():
    inf = estado.Informe(generado="hoy", master_sha="f" * 40)
    inf.add("Repo", "x", estado.ALERTA, "a | b")
    md = estado.render_markdown(inf, ["sin cambios"])
    assert "alertas: **1**" in md
    assert "a \\| b" in md


def _sin_red(monkeypatch, con_alerta: bool):
    def github(inf, _gh):
        inf.master_sha = "c" * 40
        inf.add("GitHub", "master protegido", estado.ALERTA if con_alerta else estado.OK, "-")

    monkeypatch.setattr(estado, "revisar_github", github)
    monkeypatch.setattr(estado, "revisar_cloudflare", lambda inf: inf.add("Cloudflare", "whetzy.com", estado.OK, "-"))
    monkeypatch.setattr(estado, "revisar_railway", lambda inf, _t: None)
    monkeypatch.setattr(estado, "_token_github", lambda: None)


def test_main_sale_con_1_si_hay_alertas_y_escribe_los_ficheros(monkeypatch, tmp_path):
    _sin_red(monkeypatch, con_alerta=True)
    out, js = tmp_path / "i.md", tmp_path / "e.json"
    assert estado.main(["--sin-repo", "--out", str(out), "--json", str(js)]) == 1
    assert "master protegido" in out.read_text(encoding="utf-8")
    assert json.loads(js.read_text(encoding="utf-8"))["master_sha"] == "c" * 40


def test_main_sale_con_0_sin_alertas_y_compara_con_el_estado_previo(monkeypatch, tmp_path, capsys):
    _sin_red(monkeypatch, con_alerta=False)
    previo = tmp_path / "previo.json"
    previo.write_text(json.dumps(_estado(sha="d" * 40, prs=())), encoding="utf-8")
    assert estado.main(["--sin-repo", "--state", str(previo)]) == 0
    assert "master: ddddddd → ccccccc" in capsys.readouterr().out
