"""La prueba de nivel tiene que estimar el nivel que demuestran las respuestas.

Medido el 2026-10-16 sobre `master` e85900b: `update_ability` hacia
Newton-Raphson sin ninguna proteccion y divergia. Con 12 aciertos de 50 (un
24 %, el azar con cuatro opciones) daba theta = +4, el tope, y la pantalla
decia «Tu nivel estimado: Avanzado» junto a «aun no dominas ningun modulo».
Pasaba con las dificultades sembradas por nivel (easy 1350, medium 1500,
hard 1650, expert 1800; #187) y tambien con todas a 1500. Ademas el motor
elige la siguiente pregunta segun ese theta, asi que tras unos fallos servia
las mas dificiles.
"""

from __future__ import annotations

import math
import random

import pytest

from app.services.engine.placement import IRTItem, PlacementEngine, PlacementState

#: Mismo cambio de escala que `services/placement.py`.
ELO_A_LOGIT = 400.0 / math.log(10)
#: Prior editorial por nivel de `content_loader.ELO_TIER_PRIOR`.
ELOS_POR_NIVEL = (1350.0, 1500.0, 1650.0, 1800.0)


def _banco(mixto: bool, n: int = 200) -> list[IRTItem]:
    rng = random.Random(7)
    return [
        IRTItem(
            item_id=str(i),
            difficulty=((rng.choice(ELOS_POR_NIVEL) if mixto else 1500.0) - 1500.0) / ELO_A_LOGIT,
        )
        for i in range(n)
    ]


def _theta(aciertos: int, mixto: bool, total: int = 50, semilla: int = 1) -> PlacementState:
    motor = PlacementEngine(_banco(mixto))
    estado = PlacementState()
    orden = random.Random(semilla).sample(range(len(motor.item_list)), total)
    acertadas = set(orden[:aciertos])
    for k in orden:
        motor.update_ability(estado, motor.items[str(k)], k in acertadas)
    return estado


@pytest.mark.parametrize("mixto", [True, False])
def test_responder_al_azar_no_da_avanzado(mixto: bool) -> None:
    # 12/50 es lo que saca quien marca siempre la misma opcion. El umbral de
    # «Avanzado» en PlacementScreen.nivelDeTheta es 1,5; aqui ni siquiera
    # debe pasar de «Intermedio» (-0,5).
    assert _theta(12, mixto).ability_estimate < -0.5


@pytest.mark.parametrize("mixto", [True, False])
def test_los_extremos_quedan_en_su_lado(mixto: bool) -> None:
    assert _theta(0, mixto).ability_estimate < -1.5
    assert _theta(50, mixto).ability_estimate > 1.5


@pytest.mark.parametrize("mixto", [True, False])
def test_mas_aciertos_nunca_bajan_el_nivel(mixto: bool) -> None:
    thetas = [_theta(k, mixto).ability_estimate for k in range(0, 51, 5)]
    assert thetas == sorted(thetas), thetas


@pytest.mark.parametrize("semilla", range(5))
def test_el_estimador_es_finito_y_acotado(semilla: int) -> None:
    for aciertos in (0, 7, 25, 43, 50):
        estado = _theta(aciertos, mixto=True, semilla=semilla)
        assert math.isfinite(estado.ability_estimate)
        assert -4.0 <= estado.ability_estimate <= 4.0
        assert 0.0 < estado.ability_se <= 1.0


def test_el_error_baja_al_responder_mas() -> None:
    # Con mas respuestas se sabe mas: el error tipico tiene que bajar, que es
    # lo que usa `should_stop` para cortar la prueba (se_threshold=0,30).
    assert _theta(5, mixto=True, total=10).ability_se > _theta(25, mixto=True, total=50).ability_se
