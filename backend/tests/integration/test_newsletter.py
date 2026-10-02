"""Newsletter: alta pública con doble opt-in (ledger 26.10, H.30).

`POST /subscribe` nunca confirma por sí solo: solo `GET /confirm` con el token
del correo lo hace. El cuerpo de la respuesta no cambia según exista o no el
email, para no filtrar qué direcciones están suscritas.

Todos los tests sustituyen `email_service.send_newsletter_confirmation` por un
registrador síncrono: la función real despacha el envío a un hilo aparte
(`_dispatch`, ver `services/email.py`) y esperar a ese hilo sin ayuda sería un
test intermitente — justo lo que no puede ser una puerta.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.newsletter import NewsletterSubscriber

NEWS = "/api/v1/newsletter"


async def _subscriber(db_session: AsyncSession, email: str) -> NewsletterSubscriber:
    row = (
        await db_session.execute(
            select(NewsletterSubscriber).where(NewsletterSubscriber.email == email)
        )
    ).scalar_one()
    await db_session.refresh(row)
    return row


@pytest.fixture
def correos_mandados(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str, str]]:
    """Sustituye el envío real; cada llamada queda como (to, token, lang)."""
    enviados: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        "app.api.v1.endpoints.newsletter.email_service.send_newsletter_confirmation",
        lambda to, token, lang="es": enviados.append((to, token, lang)),
    )
    return enviados


class TestSubscribe:
    async def test_crea_sin_confirmar_y_manda_correo(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        r = await client.post(
            f"{NEWS}/subscribe", json={"email": "Lector@example.com", "language": "es"}
        )

        assert r.status_code == 202, r.text
        assert r.json() == {"status": "pending_confirmation"}

        row = await _subscriber(db_session, "lector@example.com")
        assert row.confirmed is False
        assert row.language == "es"
        assert correos_mandados == [("lector@example.com", correos_mandados[0][1], "es")]
        assert len(correos_mandados[0][1]) > 10

    async def test_email_invalido_es_422(self, client) -> None:
        r = await client.post(f"{NEWS}/subscribe", json={"email": "no-es-un-email"})
        assert r.status_code == 422

    async def test_idioma_desconocido_cae_a_es(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        r = await client.post(
            f"{NEWS}/subscribe", json={"email": "otro@example.com", "language": "fr"}
        )

        assert r.status_code == 202
        row = await _subscriber(db_session, "otro@example.com")
        assert row.language == "es"
        assert correos_mandados[0][2] == "es"

    async def test_repetir_un_email_ya_confirmado_no_reenvia_ni_cambia_nada(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        await client.post(f"{NEWS}/subscribe", json={"email": "repetido@example.com"})
        row = await _subscriber(db_session, "repetido@example.com")
        row.confirmed = True
        await db_session.commit()
        token_hash_antes = row.token_hash

        r = await client.post(f"{NEWS}/subscribe", json={"email": "repetido@example.com"})

        assert r.status_code == 202
        assert r.json() == {"status": "pending_confirmation"}
        assert len(correos_mandados) == 1, "no debe mandar un segundo correo a uno ya confirmado"
        row_despues = await _subscriber(db_session, "repetido@example.com")
        assert row_despues.token_hash == token_hash_antes

    async def test_dar_de_baja_y_volver_a_suscribirse_manda_correo_nuevo(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        await client.post(f"{NEWS}/subscribe", json={"email": "baja@example.com"})
        row = await _subscriber(db_session, "baja@example.com")
        row.confirmed = True
        row.unsubscribed_at = row.created_at
        await db_session.commit()

        r = await client.post(f"{NEWS}/subscribe", json={"email": "baja@example.com"})

        assert r.status_code == 202
        assert len(correos_mandados) == 2
        row_despues = await _subscriber(db_session, "baja@example.com")
        assert row_despues.confirmed is False
        assert row_despues.unsubscribed_at is None


class TestConfirm:
    async def test_confirma_con_el_token_del_correo(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        await client.post(f"{NEWS}/subscribe", json={"email": "confirma@example.com"})
        token = correos_mandados[0][1]

        r = await client.get(f"{NEWS}/confirm", params={"token": token})

        assert r.status_code == 200
        assert "confirmada" in r.text.lower() or "confirmed" in r.text.lower()
        row = await _subscriber(db_session, "confirma@example.com")
        assert row.confirmed is True
        assert row.confirmed_at is not None

    async def test_token_invalido_no_revienta(self, client) -> None:
        r = await client.get(f"{NEWS}/confirm", params={"token": "no-existe-este-token"})
        assert r.status_code == 200
        assert "no v" in r.text.lower() or "invalid" in r.text.lower()

    async def test_token_corto_es_422(self, client) -> None:
        r = await client.get(f"{NEWS}/confirm", params={"token": "corto"})
        assert r.status_code == 422


class TestUnsubscribe:
    async def test_un_clic_da_de_baja_y_confirm_deja_de_servir(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        await client.post(f"{NEWS}/subscribe", json={"email": "unclick@example.com"})
        token = correos_mandados[0][1]
        await client.get(f"{NEWS}/confirm", params={"token": token})

        r = await client.post(f"{NEWS}/unsubscribe", params={"token": token})

        assert r.status_code == 200
        assert r.json() == {"unsubscribed": True}
        row = await _subscriber(db_session, "unclick@example.com")
        assert row.unsubscribed_at is not None

        r2 = await client.get(f"{NEWS}/confirm", params={"token": token})
        assert "no v" in r2.text.lower() or "invalid" in r2.text.lower()

    async def test_baja_con_token_desconocido_no_revienta(self, client) -> None:
        r = await client.post(f"{NEWS}/unsubscribe", params={"token": "no-existe-este-token"})
        assert r.status_code == 200
        assert r.json() == {"unsubscribed": False}
