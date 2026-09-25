"""La regla de salto que ve el alumno es la que aplica el motor (ledger 37.2).

`PlacementScreen.tsx` explica «se da por sabido con ≥ X % de ≥ N preguntas»
con números escritos en el cliente. Si alguien cambia el umbral en el motor y
no en la pantalla, la explicación miente; este test lo impide.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

from app.services.engine.placement import PlacementEngine

PANTALLA = Path(__file__).resolve().parents[2] / "frontend" / "src" / "pages" / "PlacementScreen.tsx"


def test_umbral_y_minimo_coinciden_con_el_motor() -> None:
    m = re.search(r"placement\.skipRule', \{ pct: (\d+), min: (\d+) \}", PANTALLA.read_text(encoding="utf-8"))
    assert m, "PlacementScreen.tsx ya no pasa pct/min a placement.skipRule"
    firma = inspect.signature(PlacementEngine.__init__).parameters
    assert int(m.group(1)) == round(firma["skip_threshold"].default * 100)
    assert int(m.group(2)) == firma["skip_min_questions"].default
