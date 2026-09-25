"""El frontend muestra el cupo del tutor y el precio de la certificación desde
`frontend/src/lib/plans.ts`; el backend los aplica desde `settings` (ADR-49).
Si uno cambia y el otro no, la pantalla promete algo que el servidor no hace.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.config import settings

PLANS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "plans.ts"


def _const(name: str) -> str:
    m = re.search(rf"export const {name} = ([0-9.]+);", PLANS.read_text(encoding="utf-8"))
    assert m, f"{name} no está en {PLANS}"
    return m.group(1)


def test_cupo_del_tutor_coincide() -> None:
    assert int(_const("TUTOR_DAILY_LIMIT_PRO")) == settings.TUTOR_DAILY_LIMIT_PLUS


def test_precio_de_la_certificacion_coincide() -> None:
    assert float(_const("CERTIFICATION_PRICE_USD")) == settings.CERTIFICATION_PRICE_USD


def test_precios_adr41_unica_fuente() -> None:
    """Every $X.XX in the frontend must match ADR-41 prices (38.1)."""
    from app.core.prices import CERT_EXAM_USD, CREATOR_MONTHLY_USD, PRO_MAX_MONTHLY_USD, PRO_MONTHLY_USD

    allowed = {str(p) for p in [PRO_MONTHLY_USD, PRO_MAX_MONTHLY_USD, CREATOR_MONTHLY_USD, CERT_EXAM_USD]}
    allowed |= {"0.00", "0.99"}  # edge values that are not plan prices

    src = Path(__file__).resolve().parents[2] / "frontend" / "src"
    price_re = re.compile(r"\$(\d+\.\d{2})")

    violations = []
    for f in src.rglob("*"):
        if f.suffix not in {".ts", ".tsx", ".json"} or ".test." in f.name or "node_modules" in str(f):
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("//") or line.lstrip().startswith("*"):
                continue
            for m in price_re.finditer(line):
                val = m.group(1)
                if val not in allowed:
                    violations.append(f"{f.relative_to(src)}:{n} → ${val}")
    assert violations == [], f"Prices not from ADR-41: {violations}"


FORBIDDEN = re.compile(r"certificaci[oó]n oficial|official certification", re.IGNORECASE)
ROOT = Path(__file__).resolve().parents[2]


def test_ningun_texto_llama_oficial_al_certificado_de_whetzy() -> None:
    """ADR-49: es un «Certificado Whetzy de preparación»; el oficial lo emite el proveedor."""
    places = [ROOT / "frontend" / "src" / "i18n", ROOT / "frontend" / "src" / "pages",
              ROOT / "frontend" / "src" / "components", ROOT / "backend" / "app"]
    hits = [
        f"{p.relative_to(ROOT)}:{n}"
        for base in places
        for p in base.rglob("*")
        if p.suffix in {".json", ".ts", ".tsx", ".py"} and ".test." not in p.name
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
        if FORBIDDEN.search(line)
    ]
    assert hits == []
