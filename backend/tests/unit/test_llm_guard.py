"""39.11 / 39.12: the tutor degrades instead of failing, and has a spend ceiling.

Before this, a Groq timeout or 5xx propagated to `POST /tutor/explain` as a
500, and nothing capped the number of LLM calls per day (Pro Max is unlimited
per user by design, ADR-49, so the only ceiling is a global one).
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from app.services.ai.provider import GuardedProvider, NullProvider


class _Fake:
    def __init__(self, name: str, *, fail: Exception | None = None) -> None:
        self.name = name
        self.fail = fail
        self.calls = 0

    async def complete(self, system: str, user: str, **_: Any) -> str:
        self.calls += 1
        if self.fail:
            raise self.fail
        return f"{self.name}-answer"


def _status(code: int) -> httpx.HTTPStatusError:
    req = httpx.Request("POST", "https://llm.test/chat/completions")
    return httpx.HTTPStatusError("boom", request=req, response=httpx.Response(code, request=req))


def _run(p: GuardedProvider) -> tuple[str, str, int]:
    return asyncio.run(p.complete_named("sys", "Pregunta\n\nCONTEXTO: la explicación"))


def test_primary_answers_when_healthy() -> None:
    # 41.17: _Fake solo implementa complete() (sin complete_with_tokens),
    # así que GuardedProvider no tiene de dónde sacar un recuento real -- 0.
    assert _run(GuardedProvider(_Fake("groq"), None, 10)) == ("groq-answer", "groq", 0)


@pytest.mark.parametrize("err", [httpx.ConnectTimeout("t"), _status(503), _status(429)])
def test_fallback_llm_takes_over_on_outage(err: Exception) -> None:
    fb = _Fake("fallback-llm")
    assert _run(GuardedProvider(_Fake("groq", fail=err), fb, 10)) == (
        "fallback-llm-answer",
        "fallback-llm",
        0,
    )
    assert fb.calls == 1


def test_without_fallback_the_grounded_context_is_returned() -> None:
    text, name, tokens = _run(GuardedProvider(_Fake("groq", fail=_status(500)), None, 10))
    assert name == NullProvider.name
    assert "la explicación" in text
    assert tokens == 0


def test_client_errors_are_not_hidden() -> None:
    with pytest.raises(httpx.HTTPStatusError):
        _run(GuardedProvider(_Fake("groq", fail=_status(401)), _Fake("fallback-llm"), 10))


def test_daily_budget_stops_calling_the_llm() -> None:
    primary = _Fake("groq")
    p = GuardedProvider(primary, None, 2)
    assert _run(p)[1] == "groq"
    assert _run(p)[1] == "groq"
    assert _run(p)[1] == NullProvider.name
    assert primary.calls == 2


def test_zero_means_no_ceiling() -> None:
    primary = _Fake("groq")
    p = GuardedProvider(primary, None, 0)
    for _ in range(5):
        _run(p)
    assert primary.calls == 5


class _FakeWithTokens(_Fake):
    """41.17: un proveedor que sí reporta `usage.total_tokens`, como Groq."""

    def __init__(self, name: str, tokens: int, **kw: Any) -> None:
        super().__init__(name, **kw)
        self.tokens = tokens

    async def complete_with_tokens(self, system: str, user: str, **_: Any) -> tuple[str, int]:
        text = await self.complete(system, user)
        return text, self.tokens


def test_real_token_usage_is_reported_when_the_provider_has_it() -> None:
    text, name, tokens = _run(GuardedProvider(_FakeWithTokens("groq", 345), None, 10))
    assert (text, name, tokens) == ("groq-answer", "groq", 345)
