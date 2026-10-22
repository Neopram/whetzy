"""Newsletter mensual (26.10): a quién se envía y a quién no.

Solo a suscriptores confirmados (doble opt-in) y sin baja, una vez por mes natural
y detrás de ``NEWSLETTER_MONTHLY_ENABLED`` (apagado por defecto)."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token
from app.models.newsletter import NewsletterSubscriber
from app.services import email as email_service
from app.services.periodic import run_periodic_jobs, send_monthly_newsletter

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def _sub(email: str, **kw: object) -> NewsletterSubscriber:
    fields: dict[str, object] = {
        "email": email, "language": "es", "confirmed": True,
        "confirmed_at": NOW - timedelta(days=40),
    }
    fields.update(kw)
    return NewsletterSubscriber(**fields)


@pytest.fixture
def outbox(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    sent: list[dict[str, object]] = []
    monkeypatch.setattr(email_service, "send_newsletter_monthly", lambda **kw: sent.append(kw))
    return sent


@pytest.fixture
def enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "NEWSLETTER_MONTHLY_ENABLED", True)
    monkeypatch.setattr(email_service, "is_configured", lambda: True)


@pytest.mark.asyncio
async def test_without_an_email_provider_the_month_is_not_spent(
    db_session: AsyncSession, outbox: list, enabled: None, monkeypatch: pytest.MonkeyPatch
):
    """Con el flag encendido pero sin proveedor (H.30), el correo no sale de la
    máquina: no se marca `last_sent_at`, o ese mes se perdería en silencio."""
    monkeypatch.setattr(email_service, "is_configured", lambda: False)
    sub = _sub("on@example.com")
    db_session.add(sub)
    await db_session.commit()

    assert await send_monthly_newsletter(db_session, NOW) == 0
    await db_session.refresh(sub)
    assert sub.last_sent_at is None
    assert outbox == []


@pytest.mark.asyncio
async def test_off_by_default_sends_nothing(db_session: AsyncSession, outbox: list):
    from app.core.config import settings

    assert settings.NEWSLETTER_MONTHLY_ENABLED is False
    db_session.add(_sub("on@example.com"))
    await db_session.commit()

    assert await send_monthly_newsletter(db_session, NOW) == 0
    assert (await run_periodic_jobs(db_session, NOW))["newsletter_monthly"] == 0
    assert outbox == []


@pytest.mark.asyncio
async def test_sends_to_confirmed_with_one_click_unsubscribe_in_their_language(
    db_session: AsyncSession, outbox: list, enabled: None
):
    es, en = _sub("es@example.com"), _sub("en@example.com", language="en")
    db_session.add_all([es, en])
    await db_session.commit()

    assert await send_monthly_newsletter(db_session, NOW) == 2
    by_to = {str(m["to"]): m for m in outbox}
    assert by_to["es@example.com"]["lang"] == "es" and by_to["en@example.com"]["lang"] == "en"
    url = str(by_to["es@example.com"]["unsubscribe_url"])
    assert "/api/v1/newsletter/unsubscribe?token=" in url
    token = url.split("token=")[1].split("&")[0]
    assert verify_token(token, expected_type="unsubscribe").sub == str(es.id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "override",
    [
        {"confirmed": False, "confirmed_at": None},  # nunca confirmó el doble opt-in
        {"unsubscribed_at": NOW - timedelta(days=2)},  # se dio de baja
        {"last_sent_at": NOW - timedelta(days=3)},  # ya salió uno este mes
    ],
)
async def test_skips_unconfirmed_unsubscribed_and_already_sent_this_month(
    db_session: AsyncSession, outbox: list, enabled: None, override: dict[str, object]
):
    db_session.add(_sub("x@example.com", **override))
    await db_session.commit()

    assert await send_monthly_newsletter(db_session, NOW) == 0
    assert outbox == []


@pytest.mark.asyncio
async def test_once_per_calendar_month(db_session: AsyncSession, outbox: list, enabled: None):
    s = _sub("m@example.com", last_sent_at=NOW - timedelta(days=25))  # septiembre
    db_session.add(s)
    await db_session.commit()

    assert await send_monthly_newsletter(db_session, NOW) == 1
    assert await send_monthly_newsletter(db_session, NOW + timedelta(hours=1)) == 0  # misma vuelta horaria
    assert await send_monthly_newsletter(db_session, datetime(2026, 11, 1, 0, 5, tzinfo=UTC)) == 1
    assert len(outbox) == 2


@pytest.mark.asyncio
async def test_only_the_unsubscribed_one_is_left_out(db_session: AsyncSession, outbox: list, enabled: None):
    db_session.add_all([
        _sub("ok@example.com"),
        _sub("baja@example.com", unsubscribed_at=NOW - timedelta(days=1)),
        _sub("pend@example.com", confirmed=False, confirmed_at=None),
    ])
    await db_session.commit()

    assert await send_monthly_newsletter(db_session, NOW) == 1
    assert [m["to"] for m in outbox] == ["ok@example.com"]


def test_template_is_neutral_bilingual_with_site_and_unsubscribe_links():
    for lang in ("es", "en"):
        subject, html = email_service._render(
            "newsletter_monthly", lang, base_url="https://whetzy.com", unsubscribe_url="https://api/u?token=t"
        )
        assert "Whetzy" in subject
        assert 'href="https://whetzy.com"' in html and 'href="https://api/u?token=t"' in html
        texto = re.sub(r"<[^>]+>", " ", html)  # sin etiquetas ni atributos
        assert not re.search(r"\d", texto), "sin cifras en el cuerpo: nada que haya que medir"
