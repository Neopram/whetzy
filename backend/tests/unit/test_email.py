"""Tests for the transactional email service.

These are the mails a user cannot work around: verify your address, reset your
password. If `_dispatch` swallowed a real failure silently, or a template
rendered a broken link, the user is locked out of their account with no signal
anywhere. So the tests pin the fallback behaviour and the link construction,
and check the templates themselves for ES/EN parity.
"""

from __future__ import annotations

import smtplib
from typing import Any, ClassVar, Self

import pytest

from app.services import email as email_service
from app.services.email import (
    _TEMPLATES,
    _dispatch,
    _render,
    send_email_verification,
    send_password_reset,
    send_welcome,
)

# Todas, no una lista a mano: con tres nombres fijos, las otras seis plantillas
# (soporte, reactivación, créditos, renovación, boletín) no tenían paridad ES/EN.
TEMPLATE_NAMES = tuple(_TEMPLATES)


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str, str]]:
    """Capture whatever reaches the log-only provider."""
    calls: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        email_service, "_send_log", lambda to, subject, html: calls.append((to, subject, html))
    )
    return calls


# ── templates ─────────────────────────────────────────────────────────────────


class TestTemplates:
    def test_every_template_has_both_languages(self) -> None:
        """Red line 3: no user-visible string ships in one language only."""
        for name in TEMPLATE_NAMES:
            assert set(_TEMPLATES[name]) >= {"es", "en"}, name

    @pytest.mark.parametrize("name", TEMPLATE_NAMES)
    @pytest.mark.parametrize("lang", ["es", "en"])
    def test_subject_and_body_are_non_empty(self, name: str, lang: str) -> None:
        tpl = _TEMPLATES[name][lang]
        assert tpl["subject"].strip()
        assert tpl["html"].strip()

    @pytest.mark.parametrize("name", TEMPLATE_NAMES)
    def test_both_languages_use_the_same_placeholders(self, name: str) -> None:
        """A placeholder present in one language and missing in the other means
        `.format()` raises (or drops a link) for exactly one locale."""
        import string

        def fields(tpl: dict[str, str]) -> set[str]:
            out: set[str] = set()
            for part in ("subject", "html"):
                out |= {
                    f for _, f, _, _ in string.Formatter().parse(tpl[part]) if f
                }
            return out

        assert fields(_TEMPLATES[name]["es"]) == fields(_TEMPLATES[name]["en"])

    @pytest.mark.parametrize("name", TEMPLATE_NAMES)
    def test_both_languages_point_to_the_same_whetzy_addresses(self, name: str) -> None:
        """Una dirección traducida («soporte@») es otro buzón: el alumno en ES
        escribía a uno que no sale en ningún otro sitio (support_resolved, 2026-10-21)."""
        import re

        def addresses(tpl: dict[str, str]) -> set[str]:
            return set(re.findall(r"[\w.+-]+@whetzy\.com", tpl["subject"] + tpl["html"]))

        assert addresses(_TEMPLATES[name]["es"]) == addresses(_TEMPLATES[name]["en"])


class TestRender:
    def test_renders_spanish(self) -> None:
        subject, html = _render("welcome", "es", name="Ana", base_url="https://whetzy.com")
        assert "Ana" in html
        assert subject

    def test_renders_english(self) -> None:
        subject, html = _render("welcome", "en", name="Ana", base_url="https://whetzy.com")
        assert "Ana" in html
        assert subject

    def test_es_and_en_differ(self) -> None:
        es = _render("password_reset", "es", name="A", reset_url="u")
        en = _render("password_reset", "en", name="A", reset_url="u")
        assert es[0] != en[0]

    def test_unknown_language_falls_back_to_spanish(self) -> None:
        fallback = _render("welcome", "fr", name="Ana", base_url="u")
        spanish = _render("welcome", "es", name="Ana", base_url="u")
        assert fallback == spanish

    def test_empty_language_falls_back_to_spanish(self) -> None:
        assert _render("welcome", "", name="A", base_url="u") == _render(
            "welcome", "es", name="A", base_url="u"
        )

    def test_a_malicious_display_name_is_escaped_in_the_body(self) -> None:
        """`display_name` no pasa por ningún filtro de HTML al registrarse
        (`schemas/user.py`, solo una lista de palabras bloqueadas) — un
        nombre con una etiqueta no debe llegar intacto al cuerpo HTML."""
        payload = "<img src=x onerror=alert(1)>"
        _subject, html = _render("welcome", "es", name=payload, base_url="https://whetzy.com")
        assert payload not in html
        assert "&lt;img src=x onerror=alert(1)&gt;" in html

    def test_a_malicious_display_name_is_not_escaped_in_the_subject(self) -> None:
        """El asunto es texto plano para la cabecera `Subject`, no HTML: un
        alumno llamado O'Brien no debe ver entidades en su bandeja."""
        subject, _html = _render("welcome", "es", name="O'Brien", base_url="https://whetzy.com")
        assert "O'Brien" in subject
        assert "&#x27;" not in subject


# ── dispatch ──────────────────────────────────────────────────────────────────


class TestDispatch:
    def test_falls_back_to_log_when_nothing_is_configured(
        self, sent: list[tuple[str, str, str]], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.core.config import settings

        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp", raising=False)
        monkeypatch.setattr(settings, "SMTP_USER", "", raising=False)
        monkeypatch.setattr(settings, "RESEND_API_KEY", "", raising=False)
        _dispatch("a@b.test", "Subject", "<p>hi</p>")
        assert len(sent) == 1

    def test_uses_smtp_when_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.core.config import settings

        calls: list[tuple[str, str, str]] = []
        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp", raising=False)
        monkeypatch.setattr(settings, "SMTP_USER", "user", raising=False)
        monkeypatch.setattr(settings, "SMTP_PASSWORD", "pass", raising=False)
        monkeypatch.setattr(
            email_service, "_send_smtp", lambda to, s, h, unsubscribe_url=None: calls.append((to, s, h))
        )
        _dispatch("a@b.test", "S", "<p>h</p>")
        assert calls == [("a@b.test", "S", "<p>h</p>")]

    def test_uses_resend_when_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.core.config import settings

        calls: list[tuple[str, str, str]] = []
        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend", raising=False)
        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_x", raising=False)
        monkeypatch.setattr(
            email_service, "_send_resend", lambda to, s, h, unsubscribe_url=None: calls.append((to, s, h))
        )
        _dispatch("a@b.test", "S", "<p>h</p>")
        assert calls == [("a@b.test", "S", "<p>h</p>")]

    def test_resend_without_key_falls_back_to_log(
        self, sent: list[tuple[str, str, str]], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.core.config import settings

        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend", raising=False)
        monkeypatch.setattr(settings, "RESEND_API_KEY", "", raising=False)
        _dispatch("a@b.test", "S", "<p>h</p>")
        assert len(sent) == 1

    def test_provider_failure_is_logged_and_falls_back(
        self, sent: list[tuple[str, str, str]], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A dead SMTP host must not 500 the caller — but the mail must still
        land in the log so the failure is recoverable, not invisible."""
        from app.core.config import settings

        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp", raising=False)
        monkeypatch.setattr(settings, "SMTP_USER", "user", raising=False)

        def boom(to: str, subject: str, html: str, unsubscribe_url: str | None = None) -> None:
            raise smtplib.SMTPException("host unreachable")

        monkeypatch.setattr(email_service, "_send_smtp", boom)
        _dispatch("a@b.test", "S", "<p>h</p>")  # must not raise
        assert len(sent) == 1

    def test_caller_never_sees_an_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.core.config import settings

        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp", raising=False)
        monkeypatch.setattr(settings, "SMTP_USER", "user", raising=False)

        def boom(*a: Any, **k: Any) -> None:
            raise RuntimeError("anything at all")

        monkeypatch.setattr(email_service, "_send_smtp", boom)
        monkeypatch.setattr(email_service, "_send_log", boom)
        with pytest.raises(RuntimeError):
            # If even the fallback raises it propagates — documents the limit
            # of the best-effort guarantee rather than pretending it's total.
            _dispatch("a@b.test", "S", "<p>h</p>")


# ── public senders ────────────────────────────────────────────────────────────


class TestPublicSenders:
    def test_welcome_includes_the_name(self, sent: list[tuple[str, str, str]]) -> None:
        send_welcome("a@b.test", "Ana", "es")
        assert sent and "Ana" in sent[0][2]

    def test_verification_link_carries_the_token(
        self, sent: list[tuple[str, str, str]]
    ) -> None:
        send_email_verification("a@b.test", "Ana", "tok123", "es")
        assert "verify-email?token=tok123" in sent[0][2]

    def test_reset_link_carries_the_token(self, sent: list[tuple[str, str, str]]) -> None:
        send_password_reset("a@b.test", "Ana", "tok456", "es")
        assert "reset-password?token=tok456" in sent[0][2]

    def test_reset_link_is_absolute(
        self, sent: list[tuple[str, str, str]], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A relative link in an email client goes nowhere."""
        from app.core.config import settings

        monkeypatch.setattr(settings, "FRONTEND_BASE_URL", "https://whetzy.com", raising=False)
        send_password_reset("a@b.test", "Ana", "t", "en")
        assert "https://whetzy.com/reset-password?token=t" in sent[0][2]

    @pytest.mark.parametrize("lang", ["es", "en"])
    def test_every_sender_works_in_both_languages(
        self, sent: list[tuple[str, str, str]], lang: str
    ) -> None:
        send_welcome("a@b.test", "Ana", lang)
        send_email_verification("a@b.test", "Ana", "t", lang)
        send_password_reset("a@b.test", "Ana", "t", lang)
        assert len(sent) == 3
        assert all(subject.strip() for _, subject, _ in sent)

    def test_recipient_is_preserved(self, sent: list[tuple[str, str, str]]) -> None:
        send_welcome("someone@example.test", "Ana", "es")
        assert sent[0][0] == "someone@example.test"


class TestSendLog:
    def test_log_provider_does_not_raise(self) -> None:
        email_service._send_log("a@b.test", "S", "<p>body</p>")


# ── the actual delivery paths ─────────────────────────────────────────────────


class _FakeSMTP:
    """Minimal stand-in for smtplib.SMTP used as a context manager."""

    instances: ClassVar[list[_FakeSMTP]] = []

    def __init__(self, host: str, port: int, timeout: int = 10) -> None:
        self.host, self.port, self.timeout = host, port, timeout
        self.started_tls = False
        self.login_args: tuple[str, str] | None = None
        self.sent: tuple[str, str, str] | None = None
        _FakeSMTP.instances.append(self)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def starttls(self, context: object = None) -> None:
        self.started_tls = True

    def login(self, user: str, password: str) -> None:
        self.login_args = (user, password)

    def sendmail(self, sender: str, to: str, body: str) -> None:
        self.sent = (sender, to, body)


@pytest.fixture
def fake_smtp(monkeypatch: pytest.MonkeyPatch) -> type[_FakeSMTP]:
    _FakeSMTP.instances = []
    monkeypatch.setattr(smtplib, "SMTP", _FakeSMTP)
    return _FakeSMTP


class TestSendSmtp:
    def test_message_headers_and_body(
        self, fake_smtp: type[_FakeSMTP], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.core.config import settings

        monkeypatch.setattr(settings, "SMTP_USE_TLS", True, raising=False)
        monkeypatch.setattr(settings, "SMTP_USER", "user", raising=False)
        monkeypatch.setattr(settings, "SMTP_PASSWORD", "pw", raising=False)

        email_service._send_smtp("dest@b.test", "Asunto", "<p>hola</p>")

        smtp = fake_smtp.instances[0]
        assert smtp.sent is not None
        sender, to, raw = smtp.sent
        assert to == "dest@b.test"
        assert sender == settings.EMAIL_FROM_ADDRESS
        assert "Subject: Asunto" in raw
        assert smtp.started_tls is True
        assert smtp.login_args == ("user", "pw")

    def test_tls_disabled_skips_starttls(
        self, fake_smtp: type[_FakeSMTP], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.core.config import settings

        monkeypatch.setattr(settings, "SMTP_USE_TLS", False, raising=False)
        monkeypatch.setattr(settings, "SMTP_USER", "", raising=False)
        email_service._send_smtp("dest@b.test", "S", "<p>h</p>")
        assert fake_smtp.instances[0].started_tls is False

    def test_no_user_skips_login(
        self, fake_smtp: type[_FakeSMTP], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.core.config import settings

        monkeypatch.setattr(settings, "SMTP_USER", "", raising=False)
        email_service._send_smtp("dest@b.test", "S", "<p>h</p>")
        assert fake_smtp.instances[0].login_args is None

    def test_non_ascii_subject_survives(
        self, fake_smtp: type[_FakeSMTP], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Spanish subjects carry accents; a broken encoding shows as mojibake
        in the user's inbox (red line 3 in the place it is most visible)."""
        from app.core.config import settings

        monkeypatch.setattr(settings, "SMTP_USER", "", raising=False)
        email_service._send_smtp("dest@b.test", "Restablece tu contraseña", "<p>¡hola!</p>")
        smtp = fake_smtp.instances[0]
        assert smtp.sent is not None
        raw = smtp.sent[2]
        # MIME-encoded, but decodable back to the original.
        from email import message_from_string
        from email.header import decode_header, make_header

        parsed = message_from_string(raw)
        assert str(make_header(decode_header(parsed["Subject"]))) == "Restablece tu contraseña"


class _FakeResponse:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


class TestSendResend:
    """El proveedor HTTP.

    Estos tests mockeaban `urllib.request.urlopen`. Al pasar el proveedor a
    `httpx` dejaron de interceptar nada y **empezaron a llamar a la API real de
    Resend** en cada ejecucion de la suite, fallando con un 401 autentico. Un
    test que sale a internet no prueba el codigo: prueba la conectividad.
    """

    @staticmethod
    def _captura(monkeypatch: pytest.MonkeyPatch, status: int = 200, body: str = "{}"):
        import httpx

        visto: dict[str, Any] = {}

        def fake_post(url: str, **kwargs: Any) -> httpx.Response:
            visto["url"] = url
            visto.update(kwargs)
            return httpx.Response(status_code=status, text=body)

        monkeypatch.setattr(httpx, "post", fake_post)
        return visto

    def test_posts_expected_payload(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.core.config import settings

        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_secret", raising=False)
        visto = self._captura(monkeypatch)

        email_service._send_resend("dest@b.test", "Asunto", "<p>hola</p>")

        assert visto["url"] == "https://api.resend.com/emails"
        assert visto["json"]["to"] == ["dest@b.test"]
        assert visto["json"]["subject"] == "Asunto"
        assert visto["json"]["html"] == "<p>hola</p>"
        assert visto["headers"]["Authorization"] == "Bearer re_secret"

    def test_error_status_raises_with_the_reason(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """El motivo tiene que llegar: 'error 500' a secas no sirve para nada.

        Los fallos reales de Resend son 'clave invalida' o 'remitente sin
        verificar', y los dos se arreglan en un minuto **si se leen**.
        """
        from app.core.config import settings

        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_x", raising=False)
        self._captura(
            monkeypatch,
            status=403,
            body='{"message":"The whetzy.com domain is not verified"}',
        )

        with pytest.raises(RuntimeError, match="domain is not verified"):
            email_service._send_resend("dest@b.test", "S", "<p>h</p>")

    def test_api_key_is_not_in_the_payload(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The key belongs in the header, never in the JSON body."""
        import json as _json

        from app.core.config import settings

        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_secret", raising=False)
        visto = self._captura(monkeypatch)

        email_service._send_resend("dest@b.test", "S", "<p>h</p>")
        assert "re_secret" not in _json.dumps(visto["json"])


