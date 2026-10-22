"""46.6 (ADR-68): el embudo de pago y la encuesta de la primera sesión.

Mismas reglas que los efectos (46.6a): el cliente manda en lote, el servidor
guarda **sin `user_id`** ni IP y con esquema cerrado. `GET /analytics/conversion`
pone en fila registro → primera respuesta → ver el pago → abrir Paddle →
suscripción, y reparte la encuesta con su `n`.
"""

from __future__ import annotations

from sqlalchemy import select

from app.models.analytics import AnalyticsEvent

URL = "/api/v1/analytics/client-events"
CONVERSION = "/api/v1/analytics/conversion"
ADMIN_KEY = "test-admin-key-conversion"


async def test_pasos_de_pago_y_encuesta_se_guardan_sin_usuario(client, db_session, auth_headers):
    body = {
        "events": [
            {"type": "checkout_viewed", "plan": "plus"},
            {"type": "checkout_opened", "plan": "pro"},
            {"type": "first_session_survey", "answer": "somewhat"},
        ]
    }
    r = await client.post(URL, json=body, headers=auth_headers)
    assert r.status_code == 202, r.text

    rows = list((await db_session.scalars(select(AnalyticsEvent))).all())
    assert sorted(e.event_type for e in rows) == ["checkout_opened", "checkout_viewed", "first_session_survey"]
    assert all(e.user_id is None for e in rows)
    survey = next(e for e in rows if e.event_type == "first_session_survey")
    assert survey.properties == {"answer": "somewhat"}


async def test_plan_o_respuesta_fuera_de_la_lista_422(client, auth_headers):
    bad = [
        {"type": "checkout_viewed", "plan": "enterprise"},
        {"type": "checkout_opened", "plan": "pro", "email": "a@b.c"},
        # Sin texto libre: la encuesta no puede traer nada que la política no cubra.
        {"type": "first_session_survey", "answer": "me encantó, soy Ana"},
        {"type": "first_session_survey", "answer": "a_lot", "comment": "x"},
    ]
    for event in bad:
        r = await client.post(URL, json={"events": [event]}, headers=auth_headers)
        assert r.status_code == 422, event


async def test_embudo_y_encuesta_con_su_n(client, auth_headers, monkeypatch):
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "CONTENT_ADMIN_KEY", ADMIN_KEY)
    events = (
        [{"type": "checkout_viewed", "plan": "plus"}] * 5
        + [{"type": "checkout_viewed", "plan": "pro"}] * 3
        + [{"type": "checkout_opened", "plan": "plus"}] * 2
        + [{"type": "first_session_survey", "answer": "a_lot"}] * 4
        + [{"type": "first_session_survey", "answer": "not_really"}]
    )
    r = await client.post(URL, json={"events": events}, headers=auth_headers)
    assert r.status_code == 202, r.text

    r = await client.get(CONVERSION, headers={"X-Admin-Key": ADMIN_KEY})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["checkout_viewed"] == {"total": 8, "by_plan": {"plus": 5, "pro": 3}}
    assert data["checkout_opened"] == {"total": 2, "by_plan": {"plus": 2}}
    # `auth_headers` crea un usuario: un registro en la ventana.
    assert data["registrations"] >= 1
    assert data["subscription_started"] == 0
    assert data["survey"] == {
        "n": 5,
        "answers": {"a_lot": 4, "somewhat": 0, "not_really": 1},
        "sample_too_small": True,
    }
    # Pasos de pago anónimos: son visitas, no personas, y el informe lo dice.
    assert data["checkout_unit"] == "visits"


async def test_conversion_exige_clave_de_admin(client, monkeypatch):
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "CONTENT_ADMIN_KEY", ADMIN_KEY)
    assert (await client.get(CONVERSION)).status_code in (401, 403)


async def test_dashboard_incluye_el_embudo_de_pago(client, monkeypatch):
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "CONTENT_ADMIN_KEY", ADMIN_KEY)
    r = await client.get("/api/v1/analytics/dashboard", headers={"X-Admin-Key": ADMIN_KEY})
    assert r.status_code == 200, r.text
    assert r.json()["conversion_steps"]["checkout_unit"] == "visits"
