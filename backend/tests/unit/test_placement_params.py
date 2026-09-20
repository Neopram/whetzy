"""Los parametros del motor de nivelacion tienen que ser compatibles entre si.

`can_skip_module` exige `skip_min_questions` preguntas **de un mismo modulo**,
y la prueba entera gasta como mucho `max_questions` repartidas entre todos los
modulos del track. Si el primero no cabe en el segundo, «saltate lo que ya
dominas» —la razon de que exista la prueba— no se dispara jamas y nadie se
entera, porque la prueba funciona y simplemente no recomienda nada.

Estaba asi: 30 por modulo con un tope de 50 y 12 modulos. Medido en produccion
el 2026-09-20 (maximo real: 7) y simulado con el banco real en cinco niveles de
habilidad (media 7,6-9,4; pico 11).
"""

from __future__ import annotations

import pytest

from app.services.engine.placement import IRTItem, PlacementEngine, PlacementState

#: Modulos por track en el catalogo real. track01 tiene 12; ninguno pasa de ~20.
MODULOS_TIPICOS = 12


def test_el_minimo_por_modulo_cabe_en_la_prueba() -> None:
    """La invariante que faltaba: el umbral tiene que ser alcanzable."""
    motor = PlacementEngine(items=[])

    # Reparto uniforme: el caso peor para un solo modulo. El motor concentra
    # mas que esto, pero si ni con el doble del reparto uniforme se llega, el
    # umbral es inalcanzable por construccion.
    techo_razonable = 2 * motor.max_questions / MODULOS_TIPICOS

    assert motor.skip_min_questions <= techo_razonable, (
        f"skip_min_questions={motor.skip_min_questions} no se alcanza con "
        f"max_questions={motor.max_questions} repartidas entre {MODULOS_TIPICOS} "
        f"modulos: ningun modulo llegaria, y la prueba nunca recomendaria saltar nada"
    )


def test_el_minimo_por_modulo_sigue_exigiendo_evidencia() -> None:
    """Bajarlo no puede convertirlo en «acierta dos y saltate el modulo»."""
    motor = PlacementEngine(items=[])
    assert motor.skip_min_questions >= 5
    # Con el umbral de acierto, cuantos hay que acertar de verdad.
    aciertos = motor.skip_min_questions * motor.skip_threshold
    assert aciertos >= 4, f"solo {aciertos:.1f} aciertos para saltar un modulo"


def test_la_prueba_no_puede_terminar_antes_del_minimo() -> None:
    motor = PlacementEngine(items=[])
    assert motor.min_questions <= motor.max_questions


@pytest.mark.parametrize("respondidas", [0, 5, 7])
def test_por_debajo_del_minimo_no_se_recomienda_saltar(respondidas: int) -> None:
    motor = PlacementEngine(items=[])
    estado = PlacementState()
    estado.skill_estimates = {"sk1": {"correct": respondidas, "total": respondidas}}

    # Aunque haya acertado TODAS, sin evidencia suficiente no se salta.
    assert motor.can_skip_module(estado, ["sk1"]) is False


def test_con_evidencia_suficiente_y_buen_acierto_si_se_recomienda() -> None:
    """El caso que antes era imposible de alcanzar."""
    motor = PlacementEngine(items=[])
    estado = PlacementState()
    n = motor.skip_min_questions
    estado.skill_estimates = {"sk1": {"correct": n, "total": n}}

    assert motor.can_skip_module(estado, ["sk1"]) is True


def test_acertar_justo_por_debajo_del_umbral_no_basta() -> None:
    motor = PlacementEngine(items=[])
    estado = PlacementState()
    n = motor.skip_min_questions
    # Un acierto menos del que pide `skip_threshold`.
    aciertos = int(n * motor.skip_threshold) - 1
    estado.skill_estimates = {"sk1": {"correct": aciertos, "total": n}}

    assert motor.can_skip_module(estado, ["sk1"]) is False


def test_un_modulo_alcanza_el_umbral_en_una_prueba_completa() -> None:
    """Simulacion con el motor real: el umbral se alcanza de verdad.

    No mide contenido —el pool es sintetico— sino el reparto que hace el
    selector: si concentra lo bastante como para que un modulo junte
    `skip_min_questions`.
    """
    import collections
    import random

    random.seed(7)
    # 12 modulos x 40 items, dificultades repartidas como en un track real.
    items, modulo_de = [], {}
    for m in range(MODULOS_TIPICOS):
        for i in range(40):
            sid = f"sk{m:02d}{i:02d}"
            modulo_de[sid] = f"m{m:02d}"
            items.append(
                IRTItem(
                    item_id=f"q{m:02d}{i:02d}",
                    difficulty=-2.5 + (m * 0.4) + (i % 5) * 0.1,
                    skill_ids=[sid],
                )
            )

    motor = PlacementEngine(items=items)
    estado = PlacementState()
    por_modulo: collections.Counter[str] = collections.Counter()
    while not motor.should_stop(estado):
        item = motor.select_next_item(estado)
        if item is None:
            break
        acierto = random.random() < motor.probability_correct(0.5, item)
        motor.update_ability(estado, item, acierto)
        por_modulo[modulo_de[item.skill_ids[0]]] += 1

    assert por_modulo, "la simulacion no llego a servir ningun item"
    assert max(por_modulo.values()) >= motor.skip_min_questions, (
        f"el modulo mas visto junto {max(por_modulo.values())} preguntas y el "
        f"umbral es {motor.skip_min_questions}: sigue sin poder dispararse"
    )
