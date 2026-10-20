"""46.6a (ADR-68, docs/PLAN_UI_AVANZADA.md §7.2): analítica de efectos.

El cliente manda en lote `fx_emitted`, `fx_skipped`, `sound_toggled` y
`haptic_toggled`; se guardan en `analytics_events` **sin `user_id`** (ADR-68
punto 3) y `GET /analytics/fx` da la tasa de salto por nivel, con la bandera
de §6.0 punto 5 (> 60 % con n ≥ 30 → rebajar el nivel).
"""

from __future__ import annotations

from sqlalchemy import select

from app.models.analytics import AnalyticsEvent

URL = "/api/v1/analytics/client-events"
FX = "/api/v1/analytics/fx"
ADMIN_KEY = "test-admin-key-fx"


def _emitted(tier: int, type_: str, sounded: bool = True, vibrated: bool = False) -> dict:
    return {"type": "fx_emitted", "tier": tier, "fx": type_, "sounded": sounded, "vibrated": vibrated}


async def _rows(db_session) -> list[AnalyticsEvent]:
    return list((await db_session.scalars(select(AnalyticsEvent))).all())


async def test_lote_mixto_se_guarda_sin_usuario(client, db_session, auth_headers):
    body = {
        "events": [
            _emitted(1, "correct"),
            {"type": "fx_skipped", "tier": 4, "fx": "level_up"},
            {"type": "sound_toggled", "enabled": False},
            {"type": "haptic_toggled", "enabled": True},
        ]
    }
    r = await client.post(URL, json=body, headers=auth_headers)
    assert r.status_code == 202, r.text
    assert r.json() == {"accepted": 4}

    rows = await _rows(db_session)
    assert sorted(e.event_type for e in rows) == ["fx_emitted", "fx_skipped", "haptic_toggled", "sound_toggled"]
    # ADR-68 punto 3: ni quién ni desde dónde.
    assert all(e.user_id is None for e in rows)
    emitted = next(e for e in rows if e.event_type == "fx_emitted")
    assert emitted.properties == {"tier": 1, "fx": "correct", "sounded": True, "vibrated": False}


async def test_sin_sesion_401(client):
    r = await client.post(URL, json={"events": [_emitted(1, "correct")]})
    assert r.status_code == 401


async def test_campo_de_mas_o_tipo_desconocido_422(client, auth_headers):
    extra = {**_emitted(1, "correct"), "user_agent": "x"}
    assert (await client.post(URL, json={"events": [extra]}, headers=auth_headers)).status_code == 422
    unknown = {"type": "page_view", "path": "/home"}
    assert (await client.post(URL, json={"events": [unknown]}, headers=auth_headers)).status_code == 422
    # Un nivel fuera de 0–4, o un efecto que no existe.
    assert (await client.post(URL, json={"events": [_emitted(7, "correct")]}, headers=auth_headers)).status_code == 422
    assert (await client.post(URL, json={"events": [_emitted(1, "explosion")]}, headers=auth_headers)).status_code == 422
    # El nivel es el del efecto: un acierto no se cuenta como ceremonia.
    assert (await client.post(URL, json={"events": [_emitted(2, "correct")]}, headers=auth_headers)).status_code == 422
    # Solo se salta lo que bloquea (niveles 3 y 4).
    skip1 = {"type": "fx_skipped", "tier": 1, "fx": "correct"}
    assert (await client.post(URL, json={"events": [skip1]}, headers=auth_headers)).status_code == 422


async def test_lote_vacio_o_de_mas_de_50_422(client, auth_headers):
    assert (await client.post(URL, json={"events": []}, headers=auth_headers)).status_code == 422
    big = {"events": [_emitted(0, "tap", sounded=False)] * 51}
    assert (await client.post(URL, json=big, headers=auth_headers)).status_code == 422


async def test_tasa_de_salto_por_nivel_y_bandera(client, db_session, auth_headers, monkeypatch):
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "CONTENT_ADMIN_KEY", ADMIN_KEY)
    # Nivel 4: 40 ceremonias, 30 saltadas → 75 % con n = 40 → rebajar.
    # Nivel 3: 10 resúmenes, 9 saltados → 90 % pero n < 30 → aún no.
    # Nivel 1: 20 aciertos, nada que saltar.
    batches = (
        [_emitted(4, "level_up")] * 40
        + [{"type": "fx_skipped", "tier": 4, "fx": "level_up"}] * 30
        + [_emitted(3, "session_end")] * 10
        + [{"type": "fx_skipped", "tier": 3, "fx": "session_end"}] * 9
        + [_emitted(1, "correct")] * 20
    )
    for i in range(0, len(batches), 50):
        r = await client.post(URL, json={"events": batches[i : i + 50]}, headers=auth_headers)
        assert r.status_code == 202, r.text

    r = await client.get(FX, headers={"X-Admin-Key": ADMIN_KEY})
    assert r.status_code == 200, r.text
    tiers = {t["tier"]: t for t in r.json()["tiers"]}
    assert tiers[4] == {"tier": 4, "emitted": 40, "skipped": 30, "skip_rate": 0.75, "downgrade": True}
    assert tiers[3] == {"tier": 3, "emitted": 10, "skipped": 9, "skip_rate": 0.9, "downgrade": False}
    assert tiers[1] == {"tier": 1, "emitted": 20, "skipped": 0, "skip_rate": 0.0, "downgrade": False}
    assert r.json()["rule"] == {"max_skip_rate": 0.6, "min_emitted": 30}


async def test_fx_exige_clave_de_admin(client, monkeypatch):
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "CONTENT_ADMIN_KEY", ADMIN_KEY)
    assert (await client.get(FX)).status_code in (401, 403)


async def test_ritmo_limitado_429(client, auth_headers):
    one = {"events": [_emitted(0, "tap", sounded=False)]}
    codes = [(await client.post(URL, json=one, headers=auth_headers)).status_code for _ in range(31)]
    assert codes[:30] == [202] * 30
    assert codes[30] == 429


def test_niveles_iguales_que_el_cliente():
    """El cliente (`TIER` de feedbackFx.ts) lee el mismo fichero en su test."""
    import json
    from pathlib import Path

    from app.schemas.client_events import FX_TIER

    shared = json.loads((Path(__file__).parents[1] / "fixtures" / "fx_tiers.json").read_text())
    assert FX_TIER == shared
