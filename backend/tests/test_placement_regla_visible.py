"""La regla de salto que ve el alumno es la que aplica el servidor (ledger 35.2, 43.3).

`PlacementScreen.tsx` explica «se da por sabido con ≥ X % de ≥ N preguntas»
con números escritos en el cliente. Si alguien cambia el umbral en el motor y
no en la pantalla, la explicación miente; este test lo impide.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.services import placement

PANTALLA = Path(__file__).resolve().parents[2] / "frontend" / "src" / "pages" / "PlacementScreen.tsx"


def test_umbral_y_minimo_coinciden_con_el_motor() -> None:
    m = re.search(r"placement\.skipRule', \{ pct: (\d+), min: (\d+) \}", PANTALLA.read_text(encoding="utf-8"))
    assert m, "PlacementScreen.tsx ya no pasa pct/min a placement.skipRule"
    # 43.3 (D4): la regla es la de la siembra por módulo, no la del motor CAT.
    assert int(m.group(1)) == round(placement.MODULE_STRONG_ACCURACY * 100)
    assert int(m.group(2)) == placement.MODULE_STRONG_MIN


def test_el_total_de_la_pantalla_es_el_del_servidor() -> None:
    m = re.search(r"export const PLACEMENT_LENGTH = (\d+);", PANTALLA.read_text(encoding="utf-8"))
    assert m, "PlacementScreen.tsx ya no exporta PLACEMENT_LENGTH"
    assert int(m.group(1)) == placement.PLACEMENT_LENGTH
