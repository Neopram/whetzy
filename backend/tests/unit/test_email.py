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

TEMPLATE_NAMES = ("welcome", "email_verification", "password_reset")


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


# ── dispatch ──────────────────────────────────────────────────────────────────


class TestDispatch:
    def test_falls_back_to_log_when_nothing_is_configured(
        self, sent: list[tuple[str, str, str]], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.core.config import settings

        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp", raising=False)
        monkeypatch.setattr(settings, "SMTP_USER", "", raising=False)
        _dispatch("a@b.test", "Subject", "<p>hi</p>")
        assert len(sent) == 1

    def test_uses_smtp_when_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.core.config import settings

        calls: list[tuple[str, str, str]] = []
        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp", raising=False)
        monkeypatch.setattr(settings, "SMTP_USER", "user", raising=False)
        monkeypatch.setattr(
            email_service, "_send_smtp", lambda to, s, h: calls.append((to, s, h))
        )
        _dispatch("a@b.test", "S", "<p>h</p>")
        assert calls == [("a@b.test", "S", "<p>h</p>")]

    def test_uses_resend_when_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.core.config import settings

        calls: list[tuple[str, str, str]] = []
        monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend", raising=False)
        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_x", raising=False)
        monkeypatch.setattr(
            email_service, "_send_resend", lambda to, s, h: calls.append((to, s, h))
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

        def boom(to: str, subject: str, html: str) -> None:
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
    def test_posts_expected_payload(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import json as _json
        import urllib.request

        from app.core.config import settings

        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_secret", raising=False)
        captured: dict[str, object] = {}

        def fake_urlopen(req: object, timeout: int = 10) -> _FakeResponse:
            captured["url"] = req.full_url  # type: ignore[attr-defined]
            captured["method"] = req.method  # type: ignore[attr-defined]
            captured["headers"] = req.headers  # type: ignore[attr-defined]
            captured["body"] = _json.loads(req.data)  # type: ignore[attr-defined]
            return _FakeResponse(200)

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        email_service._send_resend("dest@b.test", "Asunto", "<p>hola</p>")

        assert captured["url"] == "https://api.resend.com/emails"
        assert captured["method"] == "POST"
        body = captured["body"]
        assert body["to"] == ["dest@b.test"]  # type: ignore[index]
        assert body["subject"] == "Asunto"  # type: ignore[index]
        assert body["html"] == "<p>hola</p>"  # type: ignore[index]
        headers = captured["headers"]
        assert headers["Authorization"] == "Bearer re_secret"  # type: ignore[index]

    def test_error_status_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import urllib.request

        from app.core.config import settings

        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_x", raising=False)
        monkeypatch.setattr(
            urllib.request, "urlopen", lambda req, timeout=10: _FakeResponse(500)
        )
        with pytest.raises(RuntimeError, match="Resend API error 500"):
            email_service._send_resend("dest@b.test", "S", "<p>h</p>")

    def test_api_key_is_not_in_the_payload(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The key belongs in the header, never in the JSON body."""
        import json as _json
        import urllib.request

        from app.core.config import settings

        monkeypatch.setattr(settings, "RESEND_API_KEY", "re_secret", raising=False)
        seen: dict[str, object] = {}

        def fake_urlopen(req: object, timeout: int = 10) -> _FakeResponse:
            seen["body"] = _json.loads(req.data)  # type: ignore[attr-defined]
            return _FakeResponse(200)

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        email_service._send_resend("dest@b.test", "S", "<p>h</p>")
        assert "re_secret" not in _json.dumps(seen["body"])
