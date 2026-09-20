"""El correo sale de la maquina, o se nota que no.

La version anterior de `email.py` exigia dos variables correctas a la vez
(`EMAIL_PROVIDER=resend` **y** `RESEND_API_KEY`) y, si fallaba una, escribia el
mensaje en un log y devolvia exito. En produccion eso significo que
`POST /auth/forgot-password` respondia 200 sin enviar nada y quien olvidaba su
contrasena perdia la cuenta sin enterarse (ledger H.30).

Estos tests fijan las dos propiedades que impiden que vuelva a pasar: **basta una
credencial** para que el proveedor se active, y **cuando no hay ninguna, queda un
error localizable** en vez de silencio.
"""

from __future__ import annotations

import logging

import pytest

from app.core.config import settings
from app.services import email as email_service


@pytest.fixture
def sin_credenciales(monkeypatch: pytest.MonkeyPatch) -> None:
    """El estado en el que arranco produccion: ninguna credencial."""
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "auto")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")


class TestResolucionDeProveedor:
    def test_una_sola_variable_basta_para_activar_resend(
        self, sin_credenciales: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """La regresion que importa: poner solo la clave tiene que funcionar.

        Antes hacia falta cambiar ademas `EMAIL_PROVIDER`, que sigue valiendo
        "smtp" aqui a proposito.
        """
        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp")  # el default de antes
        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_key")

        assert email_service.resolve_provider() == "resend"
        assert email_service.is_configured() is True

    def test_smtp_necesita_usuario_y_contrasena(
        self, sin_credenciales: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "SMTP_USER", "alguien@whetzy.com")
        assert email_service.resolve_provider() == "log"

        monkeypatch.setattr(settings, "SMTP_PASSWORD", "secreto")
        assert email_service.resolve_provider() == "smtp"

    def test_resend_gana_a_smtp_cuando_estan_los_dos(
        self, sin_credenciales: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_key")
        monkeypatch.setattr(settings, "SMTP_USER", "alguien@whetzy.com")
        monkeypatch.setattr(settings, "SMTP_PASSWORD", "secreto")
        assert email_service.resolve_provider() == "resend"

    def test_env_puede_forzar_log_en_desarrollo(
        self, sin_credenciales: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_key")
        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "log")
        assert email_service.resolve_provider() == "log"

    def test_un_proveedor_forzado_sin_credenciales_no_calla(
        self, sin_credenciales: None, monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Pedir 'smtp' sin credenciales y tener una clave de Resend: se usa Resend y se avisa."""
        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp")
        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_key")

        with caplog.at_level(logging.WARNING, logger="whetzy.email"):
            assert email_service.resolve_provider() == "resend"
        assert "le faltan credenciales" in caplog.text

    def test_describe_config_no_filtra_la_clave(
        self, sin_credenciales: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_secreto_que_no_debe_salir")

        datos = email_service.describe_config()

        assert datos["configured"] is True
        assert datos["has_resend_key"] is True
        assert "re_secreto_que_no_debe_salir" not in repr(datos)


class TestFalloVisible:
    def test_sin_proveedor_queda_un_error_localizable(
        self, sin_credenciales: None, caplog: pytest.LogCaptureFixture
    ) -> None:
        """El fallo original: un envio perdido no dejaba ni un rastro buscable."""
        with caplog.at_level(logging.ERROR, logger="whetzy.email"):
            email_service._entregar("quien@sea.com", "Restablece tu contrasena", "<p>x</p>")

        assert "email_not_configured" in caplog.text
        assert "RESEND_API_KEY" in caplog.text
        assert "H.30" in caplog.text

    def test_sin_proveedor_send_now_lanza(self, sin_credenciales: None) -> None:
        """La ruta de diagnostico si tiene que fallar: es para lo que existe."""
        with pytest.raises(RuntimeError, match="RESEND_API_KEY"):
            email_service._send_now("quien@sea.com", "prueba", "<p>x</p>")

    def test_un_proveedor_que_falla_no_rompe_a_quien_llama(
        self, sin_credenciales: None, monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Un reset no puede devolver 500: delataria que el correo existe."""
        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_key")

        def explota(to: str, subject: str, html: str) -> None:
            raise RuntimeError("Resend 401: API key is invalid")

        monkeypatch.setattr(email_service, "_send_resend", explota)

        with caplog.at_level(logging.ERROR, logger="whetzy.email"):
            email_service._entregar("quien@sea.com", "asunto", "<p>x</p>")

        assert "email_failed" in caplog.text
        assert "API key is invalid" in caplog.text


class TestDespachoNoBloqueante:
    async def test_el_envio_no_corre_en_el_bucle_de_eventos(
        self, sin_credenciales: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """smtplib bloquea; en el hilo del bucle congelaba el servidor entero."""
        import asyncio
        import threading

        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_key")
        hilos: list[int] = []

        def anota(to: str, subject: str, html: str) -> None:
            hilos.append(threading.get_ident())

        monkeypatch.setattr(email_service, "_send_resend", anota)

        email_service._dispatch("quien@sea.com", "asunto", "<p>x</p>")
        # El despacho vuelve enseguida; el envio ocurre despues, fuera de este hilo.
        assert hilos == []

        for _ in range(50):
            await asyncio.sleep(0.01)
            if hilos:
                break

        assert hilos, "el envio nunca llego a ejecutarse"
        assert hilos[0] != threading.get_ident()
