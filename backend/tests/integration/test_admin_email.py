"""Los dos endpoints que responden «¿sale el correo?» (H.30).

Existen porque durante un dia entero nadie pudo contestar esa pregunta sin leer
el codigo: `POST /auth/forgot-password` devolvia 200 tanto si el correo salia
como si se escribia en un log y se perdia.
"""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.core.security import create_access_token

ADMIN = "/api/v1/admin"


def _h(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


class TestEmailStatus:
    async def test_dice_que_no_esta_configurado_cuando_no_lo_esta(
        self, client, owner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "auto")
        monkeypatch.setattr(settings, "RESEND_API_KEY", "")
        monkeypatch.setattr(settings, "SMTP_USER", "")
        monkeypatch.setattr(settings, "SMTP_PASSWORD", "")

        r = await client.get(f"{ADMIN}/email/status", headers=_h(owner))

        assert r.status_code == 200, r.text
        assert r.json()["configured"] is False
        assert r.json()["provider"] == "log"

    async def test_refleja_la_clave_sin_devolverla(
        self, client, owner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_no_debe_aparecer")

        r = await client.get(f"{ADMIN}/email/status", headers=_h(owner))

        cuerpo = r.text
        assert r.json()["configured"] is True
        assert r.json()["provider"] == "resend"
        assert "re_no_debe_aparecer" not in cuerpo

    async def test_solo_el_owner(self, client, auth_headers) -> None:
        r = await client.get(f"{ADMIN}/email/status", headers=auth_headers)
        assert r.status_code == 403

    async def test_sin_sesion_es_401(self, client) -> None:
        r = await client.get(f"{ADMIN}/email/status")
        assert r.status_code == 401


class TestEmailTest:
    async def test_sin_proveedor_devuelve_503_con_el_motivo(
        self, client, owner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Aqui el fallo si tiene que subir: es la comprobacion, no un envio real."""
        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "auto")
        monkeypatch.setattr(settings, "RESEND_API_KEY", "")
        monkeypatch.setattr(settings, "SMTP_USER", "")
        monkeypatch.setattr(settings, "SMTP_PASSWORD", "")

        r = await client.post(f"{ADMIN}/email/test", headers=_h(owner))

        assert r.status_code == 503
        assert "RESEND_API_KEY" in r.json()["detail"]

    async def test_envia_al_propio_owner_por_defecto(
        self, client, owner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.services import email as email_service

        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_key")
        enviados: list[tuple[str, str, str]] = []
        monkeypatch.setattr(
            email_service,
            "_send_resend",
            lambda to, s, h: enviados.append((to, s, h)),
        )

        r = await client.post(f"{ADMIN}/email/test", headers=_h(owner))

        assert r.status_code == 200, r.text
        assert r.json() == {"sent": True, "provider": "resend", "to": owner.email}
        assert enviados[0][0] == owner.email

    async def test_el_error_del_proveedor_llega_al_owner(
        self, client, owner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Un dominio sin verificar en Resend se arregla en un minuto si se lee."""
        from app.services import email as email_service

        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_key")

        def explota(to: str, subject: str, html: str) -> None:
            raise RuntimeError("Resend 403: The whetzy.com domain is not verified")

        monkeypatch.setattr(email_service, "_send_resend", explota)

        r = await client.post(f"{ADMIN}/email/test", headers=_h(owner))

        assert r.status_code == 503
        assert "domain is not verified" in r.json()["detail"]

    async def test_solo_el_owner(self, client, auth_headers) -> None:
        r = await client.post(f"{ADMIN}/email/test", headers=auth_headers)
        assert r.status_code == 403
