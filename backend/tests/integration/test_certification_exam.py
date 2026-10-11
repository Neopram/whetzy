"""Examen certificador de pago único (38.7, ADR-49).

Rutas:
  GET  /api/v1/exams/certification/{track_id}/access
  POST /api/v1/exams/certification/{track_id}/start
  POST /api/v1/exams/mock/{attempt_id}/submit
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.content import Question
from app.models.exam import CertificationPurchase, MockExamAttempt
from app.models.user import User
from app.services import certification
from tests.integration import test_mock_exam, test_track_exam

BASE = "/api/v1/exams"

# Mismos sembrados que las suites del simulacro y del final de track.
cert_seed = test_mock_exam.cert_seed
track_seed = test_track_exam.track_seed


@pytest.fixture(autouse=True)
def _banco_reservado_listo(monkeypatch):
    """Estos tests miden el pago y el certificado; la disponibilidad tiene los suyos."""
    monkeypatch.setattr(certification, "_certification_available", lambda: True)


@pytest.fixture
def paywall(monkeypatch):
    monkeypatch.setattr(settings, "CERTIFICATION_PAYWALL", True)


async def _user(db: AsyncSession, **kw: object) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"c-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"c{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Cert",
        language="es",
        **kw,
    )
    db.add(u)
    await db.commit()
    return u


def _h(u: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(u.id)}"}


async def _start(client: AsyncClient, headers: dict, track_id: str):
    return await client.post(f"{BASE}/certification/{track_id}/start", headers=headers)


async def _all_correct(db: AsyncSession, question_ids: list[str]) -> list[dict]:
    rows = (
        await db.scalars(select(Question).where(Question.id.in_(question_ids)))
    ).all()
    return [{"question_id": q.id, "selected_index": q.correct_index} for q in rows]


async def _sit(client, db, headers, track_id, *, correct: bool) -> dict:
    res = await _start(client, headers, track_id)
    assert res.status_code == 201, res.text
    body = res.json()
    ids = [q["id"] for q in body["questions"]]
    answers = await _all_correct(db, ids) if correct else []
    sub = await client.post(
        f"{BASE}/mock/{body['attempt_id']}/submit",
        json={"answers": answers},
        headers=headers,
    )
    assert sub.status_code == 200, sub.text
    return sub.json()


# ── Paywall apagado: abierto a todos (hasta H.19) ────────────────────────────


async def test_con_el_flag_apagado_cualquiera_se_presenta(
    client, db_session, cert_seed
) -> None:
    free = await _user(db_session)
    access = (
        await client.get(
            f"{BASE}/certification/{cert_seed['track_id']}/access", headers=_h(free)
        )
    ).json()
    assert access == {
        "track_id": cert_seed["track_id"],
        "price_usd": 39.99,
        "paywall_enabled": False,
        "purchased": False,
        "available": True,
        "can_start": True,
    }
    assert (await _start(client, _h(free), cert_seed["track_id"])).status_code == 201


@pytest.mark.asyncio
async def test_sin_banco_reservado_no_se_presenta_ni_se_vende(
    client, db_session, cert_seed, monkeypatch
) -> None:
    """Sin banco reservado el examen saldría de las preguntas ya practicadas:
    ni se presenta ni se ofrece comprarlo. El staff sí, para probarlo."""
    monkeypatch.setattr(certification, "_certification_available", lambda: False)
    free = await _user(db_session)
    access = (
        await client.get(
            f"{BASE}/certification/{cert_seed['track_id']}/access", headers=_h(free)
        )
    ).json()
    assert (access["available"], access["can_start"]) == (False, False)
    res = await _start(client, _h(free), cert_seed["track_id"])
    assert res.status_code == 409
    assert res.json()["detail"] == certification.NOT_AVAILABLE
    db_session.add(CertificationPurchase(
        id=uuid.uuid4(), user_id=free.id, track_id=cert_seed["track_id"], price_usd=39.99, source="test",
    ))
    await db_session.commit()
    assert (await _start(client, _h(free), cert_seed["track_id"])).status_code == 409
    owner = await _user(db_session, role="owner")
    assert (await _start(client, _h(owner), cert_seed["track_id"])).status_code == 201


# ── Paywall encendido ────────────────────────────────────────────────────────


async def test_sin_compra_402(client, db_session, cert_seed, paywall) -> None:
    free = await _user(db_session)
    res = await _start(client, _h(free), cert_seed["track_id"])
    assert res.status_code == 402
    assert res.json()["detail"] == certification.PURCHASE_REQUIRED
    access = (
        await client.get(
            f"{BASE}/certification/{cert_seed['track_id']}/access", headers=_h(free)
        )
    ).json()
    assert access["can_start"] is False and access["paywall_enabled"] is True


async def test_ninguna_suscripcion_incluye_la_certificacion(
    client, db_session, cert_seed, paywall
) -> None:
    pro_max = await _user(
        db_session,
        is_premium=True,
        subscription_status="active",
        subscription_tier="pro",
    )
    assert (await _start(client, _h(pro_max), cert_seed["track_id"])).status_code == 402


async def test_con_compra_examen_y_certificado_verificable(
    client, db_session, cert_seed, paywall
) -> None:
    buyer = await _user(db_session)
    await certification.grant(
        db_session, buyer.id, cert_seed["track_id"], source="grant"
    )
    await db_session.commit()

    body = await _sit(
        client, db_session, _h(buyer), cert_seed["track_id"], correct=True
    )
    report = body["report"]
    assert report["passed"] is True and report["pass_pct"] == 70.0
    assert "no sustituye al examen oficial del proveedor" in report["pass_note_es"]
    cert = body["certificate"]
    assert cert is not None and cert["track_id"] == cert_seed["track_id"]
    assert cert["is_certification"] is True

    public = await client.get(f"{BASE}/certificates/{cert['code']}")
    assert public.status_code == 200 and public.json()["score_pct"] == 100.0

    attempt = await db_session.get(MockExamAttempt, uuid.UUID(body["attempt_id"]))
    assert attempt is not None and attempt.kind == certification.KIND_CERTIFYING


async def test_suspender_y_reintentar_no_pide_otro_pago(
    client, db_session, cert_seed, paywall
) -> None:
    buyer = await _user(db_session)
    await certification.grant(
        db_session, buyer.id, cert_seed["track_id"], source="grant"
    )
    await db_session.commit()

    failed = await _sit(
        client, db_session, _h(buyer), cert_seed["track_id"], correct=False
    )
    assert failed["report"]["passed"] is False and failed["certificate"] is None

    passed = await _sit(
        client, db_session, _h(buyer), cert_seed["track_id"], correct=True
    )
    assert passed["certificate"] is not None
    count = await db_session.scalar(
        select(func.count(CertificationPurchase.id)).where(
            CertificationPurchase.user_id == buyer.id
        )
    )
    assert count == 1


async def test_comprar_dos_veces_no_crea_dos_derechos(db_session, cert_seed) -> None:
    buyer = await _user(db_session)
    first = await certification.grant(
        db_session, buyer.id, cert_seed["track_id"], source="grant"
    )
    again = await certification.grant(
        db_session, buyer.id, cert_seed["track_id"], source="grant", price_usd=1.0
    )
    assert first.id == again.id and again.price_usd == 39.99


async def test_dueno_y_admin_no_pagan(client, db_session, cert_seed, paywall) -> None:
    for kw in ({"role": "owner"}, {"is_admin": True}):
        staff = await _user(db_session, **kw)
        assert (
            await _start(client, _h(staff), cert_seed["track_id"])
        ).status_code == 201


# ── Lo que no cambia ─────────────────────────────────────────────────────────


async def test_el_simulacro_sigue_sin_aprobado_ni_certificado(
    client, db_session, cert_seed, paywall
) -> None:
    free = await _user(db_session)
    res = await client.post(
        f"{BASE}/mock/start", json={"track_id": cert_seed["track_id"]}, headers=_h(free)
    )
    assert res.status_code == 201
    body = res.json()
    answers = await _all_correct(db_session, [q["id"] for q in body["questions"]])
    sub = (
        await client.post(
            f"{BASE}/mock/{body['attempt_id']}/submit",
            json={"answers": answers},
            headers=_h(free),
        )
    ).json()
    assert sub["report"]["passed"] is None and sub["certificate"] is None


async def test_los_finales_de_track_siguen_gratis(
    client, db_session, track_seed, paywall
) -> None:
    free = await _user(db_session)
    res = await client.post(
        f"{BASE}/track/{track_seed['track_id']}/start", headers=_h(free)
    )
    assert res.status_code == 201, res.text


async def test_un_track_que_no_es_de_certificacion(
    client, db_session, track_seed
) -> None:
    free = await _user(db_session)
    tid = track_seed["track_id"]
    assert (
        await client.get(f"{BASE}/certification/{tid}/access", headers=_h(free))
    ).status_code == 404
    assert (await _start(client, _h(free), tid)).status_code == 400


async def test_el_certificador_no_se_entrega_por_la_ruta_de_track(
    client, db_session, cert_seed
) -> None:
    free = await _user(db_session)
    body = (await _start(client, _h(free), cert_seed["track_id"])).json()
    res = await client.post(
        f"{BASE}/track/{body['attempt_id']}/submit",
        json={"answers": []},
        headers=_h(free),
    )
    assert res.status_code == 400


async def test_fuera_de_tiempo_no_emite_certificado(
    client, db_session, cert_seed
) -> None:
    free = await _user(db_session)
    body = (await _start(client, _h(free), cert_seed["track_id"])).json()
    attempt = await db_session.get(MockExamAttempt, uuid.UUID(body["attempt_id"]))
    attempt.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await db_session.commit()
    answers = await _all_correct(db_session, [q["id"] for q in body["questions"]])
    sub = (
        await client.post(
            f"{BASE}/mock/{body['attempt_id']}/submit",
            json={"answers": answers},
            headers=_h(free),
        )
    ).json()
    assert (
        sub["expired"] is True
        and sub["report"]["passed"] is True
        and sub["certificate"] is None
    )


async def test_requiere_sesion(client, cert_seed) -> None:
    assert (
        await client.get(f"{BASE}/certification/{cert_seed['track_id']}/access")
    ).status_code == 401
    assert (
        await client.post(f"{BASE}/certification/{cert_seed['track_id']}/start")
    ).status_code == 401
