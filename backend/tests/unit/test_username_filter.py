"""Filtro de palabras para username/display_name (19.11, App Store 1.2)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate
from app.services.username_filter import contains_blocked_word


@pytest.mark.parametrize("text", ["puta", "PUTA", "p-u-t-a", "pu7a", "esto es una puta", "fuck_you"])
def test_detects_blocked_words_despite_obfuscation(text: str) -> None:
    assert contains_blocked_word(text)


@pytest.mark.parametrize("text", ["Ana", "python_dev_42", "Clasificación", "put", "fckoff"])
def test_clean_text_passes(text: str) -> None:
    assert not contains_blocked_word(text)


@pytest.mark.parametrize(
    "text",
    ["reputation", "Reputation", "reputación", "imputado", "imputada", "shitake",
     "disputa", "diputado", "computadora", "mi reputation es buena"],
)
def test_real_words_containing_a_blocked_substring_are_not_false_positives(text: str) -> None:
    """Hallado por el verificador adversario (protocolo §7, 2026-10-02): un
    substring ciego bloqueaba "reputation" porque contiene "puta"."""
    assert not contains_blocked_word(text)


def test_register_rejects_blocked_username() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            email="a@b.com", username="puto123", display_name="Ana",
            password="Passw0rd!", age_confirmed=True,
        )


def test_register_rejects_blocked_display_name() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            email="a@b.com", username="ana123", display_name="Soy una mierda",
            password="Passw0rd!", age_confirmed=True,
        )


def test_register_accepts_clean_names() -> None:
    user = UserCreate(
        email="a@b.com", username="ana123", display_name="Ana García",
        password="Passw0rd!", age_confirmed=True,
    )
    assert user.username == "ana123"
