"""Newsletter: alta pública con doble opt-in (ledger 26.10, H.30).

`POST /subscribe` nunca confirma por sí solo. El token del enlace es un JWT
firmado (`create_unsubscribe_token`), así que los tests lo extraen capturando
la llamada a `send_newsletter_confirmation` en vez de leerlo de la base de
datos — ahí no hay ninguna columna de token que leer.

`GET /confirm` y `GET /unsubscribe` no mutan nada (revisión de [S5], PR #94:
un escáner de enlaces de correo corporativo sigue cualquier GET apenas llega
el correo, antes de que la persona lo abra). Solo el `POST` que dispara el
botón de esa página muta.
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
        assert row.last_sent_at is not None
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

        r = await client.post(f"{NEWS}/subscribe", json={"email": "repetido@example.com"})

        assert r.status_code == 202
        assert r.json() == {"status": "pending_confirmation"}
        assert len(correos_mandados) == 1, "no debe mandar un segundo correo a uno ya confirmado"

    async def test_repetir_dentro_del_enfriamiento_no_reenvia(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        """Sin esta ventana, repetir la petición manda un correo por llamada a
        cualquier dirección — el hallazgo bloqueante de [S5] en el PR #94."""
        await client.post(f"{NEWS}/subscribe", json={"email": "victima@example.com"})
        assert len(correos_mandados) == 1

        for _ in range(5):
            r = await client.post(f"{NEWS}/subscribe", json={"email": "victima@example.com"})
            assert r.status_code == 202

        assert len(correos_mandados) == 1, "la ventana de enfriamiento debe bloquear el reenvío"

    async def test_dar_de_baja_y_volver_a_suscribirse_manda_correo_nuevo(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        await client.post(f"{NEWS}/subscribe", json={"email": "baja@example.com"})
        row = await _subscriber(db_session, "baja@example.com")
        row.confirmed = True
        row.unsubscribed_at = row.created_at
        row.last_sent_at = None  # fuera de la ventana de enfriamiento para este test
        await db_session.commit()

        r = await client.post(f"{NEWS}/subscribe", json={"email": "baja@example.com"})

        assert r.status_code == 202
        assert len(correos_mandados) == 2
        row_despues = await _subscriber(db_session, "baja@example.com")
        assert row_despues.confirmed is False
        assert row_despues.unsubscribed_at is None

    async def test_alta_concurrente_de_la_misma_direccion_no_revienta(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        """Dos `POST /subscribe` a la vez para el mismo email no deben dar 500
        por `IntegrityError` (hallazgo de [S5], PR #94) — se inserta la fila
        directamente para simular que ganó la otra petición."""
        db_session.add(NewsletterSubscriber(email="carrera@example.com", language="es"))
        await db_session.commit()

        r = await client.post(f"{NEWS}/subscribe", json={"email": "carrera@example.com"})

        assert r.status_code == 202, r.text


class TestSubscribeSinCorreoConfigurado:
    """26.10: sin proveedor de correo el alta se acepta y queda registrada, pero no
    sale nada de la máquina (solo el marcador `email_not_configured` en el log)."""

    async def test_alta_aceptada_y_registrada_sin_enviar_nada(
        self, client, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        import asyncio

        from app.core.config import settings
        from app.services import email as email_service

        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "auto")
        monkeypatch.setattr(settings, "RESEND_API_KEY", "")
        monkeypatch.setattr(settings, "SMTP_USER", "")
        monkeypatch.setattr(settings, "SMTP_PASSWORD", "")
        assert email_service.resolve_provider() == "log"
        salidas: list[str] = []
        for nombre in ("_send_now", "_send_resend", "_send_smtp"):
            monkeypatch.setattr(email_service, nombre, lambda *a, _n=nombre, **k: salidas.append(_n))

        with caplog.at_level("ERROR"):
            r = await client.post(f"{NEWS}/subscribe", json={"email": "Sin@example.com", "language": "en"})
            if email_service._en_vuelo:
                await asyncio.gather(*email_service._en_vuelo)

        assert r.status_code == 202, r.text
        assert r.json() == {"status": "pending_confirmation"}
        row = await _subscriber(db_session, "sin@example.com")
        assert (row.confirmed, row.language) == (False, "en")
        assert salidas == []
        assert "email_not_configured" in caplog.text


class TestConfirm:
    async def test_get_no_muta_nada(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        await client.post(f"{NEWS}/subscribe", json={"email": "confirma@example.com"})
        token = correos_mandados[0][1]

        r = await client.get(f"{NEWS}/confirm", params={"token": token})

        assert r.status_code == 200
        assert "confirmar" in r.text.lower() or "confirm" in r.text.lower()
        row = await _subscriber(db_session, "confirma@example.com")
        assert row.confirmed is False, "GET no debe confirmar — lo dispara el botón, no el enlace"

    async def test_post_confirma_con_el_token_del_correo(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        await client.post(f"{NEWS}/subscribe", json={"email": "confirma2@example.com"})
        token = correos_mandados[0][1]

        r = await client.post(f"{NEWS}/confirm", params={"token": token})

        assert r.status_code == 200
        assert "confirmada" in r.text.lower() or "confirmed" in r.text.lower()
        row = await _subscriber(db_session, "confirma2@example.com")
        assert row.confirmed is True
        assert row.confirmed_at is not None

    async def test_token_invalido_no_revienta(self, client) -> None:
        r = await client.get(f"{NEWS}/confirm", params={"token": "no-es-un-jwt-valido"})
        assert r.status_code == 200
        assert "no v" in r.text.lower() or "invalid" in r.text.lower()

    async def test_token_corto_es_422(self, client) -> None:
        r = await client.get(f"{NEWS}/confirm", params={"token": "corto"})
        assert r.status_code == 422

    async def test_ya_confirmado_lo_dice_sin_mutar_de_nuevo(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        await client.post(f"{NEWS}/subscribe", json={"email": "doble@example.com"})
        token = correos_mandados[0][1]
        await client.post(f"{NEWS}/confirm", params={"token": token})

        r = await client.get(f"{NEWS}/confirm", params={"token": token})

        assert r.status_code == 200
        assert "confirmada" in r.text.lower() or "confirmed" in r.text.lower()


class TestUnsubscribe:
    async def test_get_no_muta_nada(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        await client.post(f"{NEWS}/subscribe", json={"email": "unclick@example.com"})
        token = correos_mandados[0][1]
        await client.post(f"{NEWS}/confirm", params={"token": token})

        r = await client.get(f"{NEWS}/unsubscribe", params={"token": token})

        assert r.status_code == 200
        row = await _subscriber(db_session, "unclick@example.com")
        assert row.unsubscribed_at is None, "GET no debe dar de baja — lo dispara el botón"

    async def test_post_da_de_baja_y_confirm_deja_de_servir(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        await client.post(f"{NEWS}/subscribe", json={"email": "unclick2@example.com"})
        token = correos_mandados[0][1]
        await client.post(f"{NEWS}/confirm", params={"token": token})

        r = await client.post(f"{NEWS}/unsubscribe", params={"token": token})

        assert r.status_code == 200
        row = await _subscriber(db_session, "unclick2@example.com")
        assert row.unsubscribed_at is not None

        r2 = await client.get(f"{NEWS}/confirm", params={"token": token})
        assert "no v" in r2.text.lower() or "invalid" in r2.text.lower()

    async def test_one_click_post_funciona_sin_haber_visto_la_pagina(
        self, client, db_session: AsyncSession, correos_mandados: list[tuple[str, str, str]]
    ) -> None:
        """RFC 8058: el cliente de correo manda este POST directo, sin GET previo."""
        await client.post(f"{NEWS}/subscribe", json={"email": "oneclick@example.com"})
        token = correos_mandados[0][1]

        r = await client.post(f"{NEWS}/unsubscribe", params={"token": token})

        assert r.status_code == 200
        row = await _subscriber(db_session, "oneclick@example.com")
        assert row.unsubscribed_at is not None

    async def test_baja_con_token_desconocido_no_revienta(self, client) -> None:
        r = await client.post(f"{NEWS}/unsubscribe", params={"token": "no-es-un-jwt-valido"})
        assert r.status_code == 200
        assert "no v" in r.text.lower() or "invalid" in r.text.lower()
