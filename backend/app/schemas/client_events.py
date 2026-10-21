"""46.6a y 46.6 (ADR-68, docs/PLAN_UI_AVANZADA.md §7.2): eventos del cliente.

Esquema cerrado: cualquier campo o tipo fuera de aquí es un 422, para que el
navegador no pueda colar en `analytics_events` nada que la política de
privacidad no cubra. El nivel de cada efecto es el de `TIER` en
`frontend/src/lib/feedbackFx.ts`; los dos lados leen
`tests/fixtures/fx_tiers.json` en sus tests para no separarse.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

FX_TIER: dict[str, int] = {
    "tap": 0,
    "correct": 1,
    "wrong": 1,
    "idk": 1,
    "combo": 2,
    "mission": 2,
    "session_end": 3,
    "level_up": 4,
    "badge": 4,
    "streak": 4,
}

FxName = Literal["tap", "correct", "wrong", "idk", "combo", "mission", "session_end", "level_up", "badge", "streak"]


class _Closed(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _check_tier[M: FxEmitted | FxSkipped](event: M) -> M:
    """El nivel tiene que ser el del efecto: `correct` siempre es 1."""
    if FX_TIER[event.fx] != event.tier:
        raise ValueError(f"{event.fx} is tier {FX_TIER[event.fx]}, not {event.tier}")
    return event


class FxEmitted(_Closed):
    type: Literal["fx_emitted"]
    tier: int = Field(ge=0, le=4)
    fx: FxName
    sounded: bool
    vibrated: bool

    _tier_matches = model_validator(mode="after")(_check_tier)


class FxSkipped(_Closed):
    """Solo se salta lo que bloquea: el resumen (3) y las ceremonias (4)."""

    type: Literal["fx_skipped"]
    tier: int = Field(ge=3, le=4)
    fx: FxName

    _tier_matches = model_validator(mode="after")(_check_tier)


class Toggled(_Closed):
    type: Literal["sound_toggled", "haptic_toggled"]
    enabled: bool


# 46.6: los planes son los de `PaddlePlan` (`frontend/src/lib/paddle.ts`).
CheckoutPlan = Literal["plus", "pro", "plus_annual", "pro_annual", "certification"]
SurveyAnswer = Literal["a_lot", "somewhat", "not_really"]


class CheckoutStep(_Closed):
    """46.6: ver el pago (precio y consentimiento a la vista) y abrir Paddle."""

    type: Literal["checkout_viewed", "checkout_opened"]
    plan: CheckoutPlan


class FirstSessionSurvey(_Closed):
    """46.6: «¿te ha servido?» tras la primera sesión. Sin texto libre."""

    type: Literal["first_session_survey"]
    answer: SurveyAnswer


ClientEvent = Annotated[
    FxEmitted | FxSkipped | Toggled | CheckoutStep | FirstSessionSurvey, Field(discriminator="type")
]


class ClientEventBatch(_Closed):
    events: list[ClientEvent] = Field(min_length=1, max_length=50)
